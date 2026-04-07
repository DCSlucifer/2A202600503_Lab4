from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from tools import calculate_budget, search_flights, search_hotels

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
SYSTEM_PROMPT_PATH = BASE_DIR / "system_prompt.txt"

BASE_SYSTEM_PROMPT = (
    SYSTEM_PROMPT_PATH.read_text(encoding="utf-8") if SYSTEM_PROMPT_PATH.exists() else ""
)

RUNTIME_AGENT_RULES = """
<runtime_rules>
- Luôn trả lời bằng tiếng Việt.
- Chỉ hỗ trợ các yêu cầu liên quan đến du lịch, chuyến bay, khách sạn, lịch trình, ngân sách chuyến đi.
- Nếu user hỏi ngoài domain du lịch (ví dụ code, linked list, bài tập lập trình), từ chối lịch sự và không gọi tool.
- Nếu user mới chào hỏi hoặc nói muốn đi du lịch nhưng chưa rõ điểm đến/sở thích/ngân sách/thời gian, hãy trả lời trực tiếp để hỏi thêm. Không gọi tool.
- Nếu user muốn đặt khách sạn nhưng thiếu thành phố, số đêm/ngày lưu trú, hoặc ngân sách, hãy hỏi đúng 3 ý đó. Không gọi tool.
- Khi user đã có yêu cầu lập kế hoạch chuyến đi đủ rõ, hãy chủ động gọi tool theo nhiều bước nếu cần.
- Với bài toán trọn gói: ưu tiên tìm chuyến bay trước, sau đó tìm khách sạn, rồi tính budget.
- Nếu cần nhiều tool, hãy tiếp tục gọi tool cho đến khi có đủ dữ liệu để trả lời hoàn chỉnh.
- Khi đã có kết quả, tổng hợp ngắn gọn, rõ ràng, có bảng chi phí nếu đã dùng calculate_budget.
</runtime_rules>
""".strip()

SYSTEM_PROMPT = f"{BASE_SYSTEM_PROMPT}\n\n{RUNTIME_AGENT_RULES}".strip()


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


tools_list = [search_flights, search_hotels, calculate_budget]
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm_with_tools = llm.bind_tools(tools_list)


# =========================================================
# Text helpers
# =========================================================

def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _looks_like_budget(text: str) -> bool:
    patterns = [
        r"\bbudget\b",
        r"ngân\s*sách",
        r"\d+\s*triệu",
        r"\d+[\.,]?\d*\s*(k|ngàn|nghìn)",
        r"\d+[\.,]?\d*\s*(vnd|đ\b|dong)",
    ]
    return any(re.search(p, text) for p in patterns)


def _looks_like_nights(text: str) -> bool:
    patterns = [
        r"\d+\s*đêm",
        r"\d+\s*ngày",
        r"check[- ]?in",
        r"check[- ]?out",
        r"nhận\s*phòng",
        r"trả\s*phòng",
    ]
    return any(re.search(p, text) for p in patterns)


_SUPPORTED_CITIES = [
    "hà nội", "đà nẵng", "phú quốc",
    "hồ chí minh", "sài gòn", "hcm",
    "tp hcm", "tphcm", "thành phố hồ chí minh",
]


def _contains_supported_city(text: str) -> bool:
    return any(city in text for city in _SUPPORTED_CITIES)


_PROGRAMMING_KEYWORDS = [
    "python", "linked list", r"\bcode\b", "lập trình",
    "thuật toán", "bài tập", r"\bjava\b", r"c\+\+",
    "javascript", r"\bsql\b", "debug", "compiler",
    "hàm số", "vòng lặp", "array", "database schema",
]

_TRAVEL_KEYWORDS = [
    "du lịch", "khách sạn", "chuyến bay", "vé máy bay",
    "đặt phòng", "đi đâu", "nghỉ dưỡng", "đi phú quốc",
    "đi đà nẵng", "resort", "tour", "lịch trình",
]


def _is_out_of_domain(text: str) -> bool:
    has_prog = any(re.search(kw, text) for kw in _PROGRAMMING_KEYWORDS)
    has_travel = any(kw in text for kw in _TRAVEL_KEYWORDS)
    return has_prog and not has_travel


# =========================================================
# Guardrail — chỉ chạy khi KHÔNG mid-chain
# =========================================================

def _is_mid_chain(messages: list) -> bool:
    """Trả về True nếu conversation đã có ToolMessage → đang trong tool-chain.
    Khi mid-chain, bỏ qua guardrail để tránh short-circuit sai."""
    return any(isinstance(m, ToolMessage) for m in messages)


def _guardrail_or_clarify(user_text: str) -> str | None:
    """
    Trả về chuỗi phản hồi trực tiếp nếu cần từ chối / hỏi lại.
    Trả về None nếu nên để LLM xử lý (kể cả gọi tool).
    """
    text = _normalize_text(user_text)

    # 1. Out-of-domain refusal
    if _is_out_of_domain(text):
        return (
            "Xin lỗi, mình chỉ hỗ trợ các yêu cầu liên quan đến du lịch như chuyến bay, "
            "khách sạn, lịch trình và ngân sách chuyến đi. "
            "Nếu bạn cần tư vấn du lịch, mình sẵn sàng hỗ trợ ngay!"
        )

    # 2. Hotel intent nhưng thiếu thông tin
    hotel_intent = any(
        kw in text for kw in ["khách sạn", "đặt khách sạn", "đặt phòng", "hotel", "tìm phòng"]
    )
    if hotel_intent:
        has_city = _contains_supported_city(text)
        has_nights = _looks_like_nights(text)
        has_budget = _looks_like_budget(text)
        if not (has_city and has_nights and has_budget):
            return (
                "Bạn muốn đặt khách sạn ở thành phố nào, bao nhiêu đêm, "
                "và ngân sách khoảng bao nhiêu để mình lọc lựa chọn phù hợp cho bạn?"
            )

    # 3. Vague travel intent (không có thành phố cụ thể)
    vague_travel = (
        any(kw in text for kw in ["du lịch", "đi chơi", "nghỉ dưỡng", "đi đâu", "muốn đi"])
        and not _contains_supported_city(text)
        and not any(kw in text for kw in ["chuyến bay", "vé máy bay"])
    )

    # 4. Greeting only (không kèm intent cụ thể)
    greeting_only = (
        any(kw in text for kw in ["xin chào", "chào", "hello", "hi", "hey"])
        and not any(kw in text for kw in ["khách sạn", "chuyến bay", "vé máy bay", "lịch trình"])
    )

    if vague_travel or greeting_only:
        return (
            "Chào bạn! Mình là TravelBuddy — trợ lý du lịch thông minh. "
            "Bạn đang dự định đi đâu, trong bao nhiêu ngày và ngân sách khoảng bao nhiêu? "
            "Cho mình biết để tư vấn chuyến đi phù hợp nhất nhé!"
        )

    return None


# =========================================================
# Agent node
# =========================================================

def agent_node(state: AgentState):
    messages = state["messages"]

    # Chèn SystemMessage một lần ở đầu chuỗi
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    # Bỏ qua guardrail nếu đang mid-chain (đã có ToolMessage)
    # → tránh short-circuit sai khi LLM đang orchestrate nhiều tool
    if not _is_mid_chain(messages):
        latest_user_text: str | None = None
        for msg in reversed(messages):
            if getattr(msg, "type", None) == "human":
                latest_user_text = (
                    msg.content if isinstance(msg.content, str) else str(msg.content)
                )
                break

        if latest_user_text:
            shortcut = _guardrail_or_clarify(latest_user_text)
            if shortcut:
                print("[agent] Trả lời trực tiếp (guardrail/clarify)")
                return {"messages": [AIMessage(content=shortcut)]}

    response = llm_with_tools.invoke(messages)

    if getattr(response, "tool_calls", None):
        for tc in response.tool_calls:
            print(f"[agent] Gọi tool: {tc['name']}({tc['args']})")
    else:
        print("[agent] Trả lời trực tiếp (LLM synthesis)")

    return {"messages": [response]}


# =========================================================
# Graph
# =========================================================

builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)

tool_node = ToolNode(tools_list)
builder.add_node("tools", tool_node)

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

graph = builder.compile()


# =========================================================
# CLI entrypoint
# =========================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TravelBuddy — Trợ lý Du lịch Thông minh")
    print("  Gõ 'quit' để thoát")
    print("=" * 60)

    while True:
        user_input = input("\nBạn: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            break

        print("\nTravelBuddy đang suy nghĩ...")
        result = graph.invoke({"messages": [("human", user_input)]})
        final = result["messages"][-1]
        print(f"\nTravelBuddy: {final.content}")