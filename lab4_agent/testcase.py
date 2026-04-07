from __future__ import annotations

import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

# agent.py phải nằm cùng thư mục với file này
from agent import graph


BASE_DIR = Path(__file__).resolve().parent
RESULT_PATH = BASE_DIR / "test_results.md"


@dataclass
class TestResult:
    name: str
    user_input: str
    expected: str
    passed: bool
    reasons: list[str]
    final_answer: str
    tool_calls: list[dict[str, Any]]
    tool_outputs: list[dict[str, Any]]
    raw_trace: str
    error: str | None = None


@dataclass
class TestCase:
    name: str
    user_input: str
    expected: str
    checker: Callable[[str, list[dict[str, Any]], list[dict[str, Any]], list[Any]], tuple[bool, list[str]]]


def safe_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def normalize_text(text: str) -> str:
    return " ".join(safe_str(text).strip().lower().split())


def contains_any(text: str, keywords: list[str]) -> bool:
    text_norm = normalize_text(text)
    return any(keyword.lower() in text_norm for keyword in keywords)


def extract_run(messages: list[Any]) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]], str]:
    tool_calls: list[dict[str, Any]] = []
    tool_outputs: list[dict[str, Any]] = []
    trace_lines: list[str] = []

    last_ai_content = ""

    for msg in messages:
        if isinstance(msg, HumanMessage):
            trace_lines.append(f"[HUMAN]\n{safe_str(msg.content)}")
            continue

        if isinstance(msg, AIMessage):
            content = safe_str(msg.content)
            calls = getattr(msg, "tool_calls", None) or []
            if calls:
                trace_lines.append(f"[AI - tool request]\n{content or '(empty content)'}")
                for call in calls:
                    tool_calls.append(
                        {
                            "name": call.get("name"),
                            "args": call.get("args", {}),
                            "id": call.get("id"),
                        }
                    )
                    trace_lines.append(f"  -> {call.get('name')}({call.get('args', {})})")
            else:
                last_ai_content = content
                trace_lines.append(f"[AI]\n{content}")
            continue

        if isinstance(msg, ToolMessage):
            tool_outputs.append(
                {
                    "name": getattr(msg, "name", None),
                    "content": safe_str(msg.content),
                    "tool_call_id": getattr(msg, "tool_call_id", None),
                }
            )
            trace_lines.append(
                f"[TOOL {getattr(msg, 'name', 'unknown')}]\n{safe_str(msg.content)}"
            )
            continue

        trace_lines.append(f"[OTHER {type(msg).__name__}]\n{safe_str(getattr(msg, 'content', msg))}")

    if not last_ai_content:
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and not (getattr(msg, "tool_calls", None) or []):
                last_ai_content = safe_str(msg.content)
                break

    return last_ai_content, tool_calls, tool_outputs, "\n\n".join(trace_lines)


def count_numbered_items(text: str) -> int:
    lines = [line.strip() for line in safe_str(text).splitlines()]
    return sum(1 for line in lines if line[:2].replace('.', '').isdigit() or line[:3].replace('.', '').isdigit())


# =========================
# Checker functions
# =========================

def check_test_1(final_answer: str, tool_calls: list[dict[str, Any]], tool_outputs: list[dict[str, Any]], _: list[Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    if tool_calls:
        reasons.append(f"Fail: không được gọi tool, nhưng thực tế gọi {len(tool_calls)} tool.")
    else:
        reasons.append("OK: không gọi tool.")

    if contains_any(final_answer, ["xin chào", "chào bạn", "hello", "hi"]):
        reasons.append("OK: có chào hỏi.")
    else:
        reasons.append("Fail: chưa thấy phần chào hỏi rõ ràng.")

    asks_more = all(
        contains_any(final_answer, group)
        for group in [
            ["đi đâu", "địa điểm", "điểm đến"],
            ["ngân sách", "budget"],
            ["bao nhiêu ngày", "thời gian", "trong bao nhiêu ngày"],
        ]
    )
    if asks_more:
        reasons.append("OK: có hỏi thêm thông tin cần thiết.")
    else:
        reasons.append("Fail: chưa hỏi đủ nhóm thông tin như điểm đến/ngân sách/thời gian.")

    passed = all(reason.startswith("OK") for reason in reasons)
    return passed, reasons



def check_test_2(final_answer: str, tool_calls: list[dict[str, Any]], tool_outputs: list[dict[str, Any]], _: list[Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    if len(tool_calls) == 1 and tool_calls[0]["name"] == "search_flights":
        reasons.append("OK: chỉ gọi đúng 1 tool search_flights.")
    else:
        reasons.append(f"Fail: kỳ vọng 1 tool search_flights, thực tế: {[c['name'] for c in tool_calls]}.")

    if tool_calls:
        args = tool_calls[0].get("args", {})
        if args.get("origin") == "Hà Nội" and args.get("destination") == "Đà Nẵng":
            reasons.append("OK: tham số tool đúng (Hà Nội -> Đà Nẵng).")
        else:
            reasons.append(f"Fail: tham số tool chưa đúng. Nhận được: {args}")

    if tool_outputs:
        output = tool_outputs[0]["content"]
        if count_numbered_items(output) >= 4:
            reasons.append("OK: tool trả về ít nhất 4 chuyến bay.")
        else:
            reasons.append("Fail: tool output chưa liệt kê đủ 4 chuyến bay.")
    else:
        reasons.append("Fail: không có output từ tool.")

    if contains_any(final_answer, ["chuyến bay", "vé", "đà nẵng"]):
        reasons.append("OK: có tổng hợp kết quả cho user.")
    else:
        reasons.append("Fail: câu trả lời cuối chưa tổng hợp đúng ngữ cảnh chuyến bay.")

    passed = all(reason.startswith("OK") for reason in reasons)
    return passed, reasons



def check_test_3(final_answer: str, tool_calls: list[dict[str, Any]], tool_outputs: list[dict[str, Any]], _: list[Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    names = [call["name"] for call in tool_calls]

    expected_prefix = ["search_flights", "search_hotels", "calculate_budget"]
    if len(names) >= 3 and names[:3] == expected_prefix:
        reasons.append("OK: tool chain đúng thứ tự search_flights -> search_hotels -> calculate_budget.")
    else:
        reasons.append(f"Fail: thứ tự tool chưa đúng. Nhận được: {names}")

    if len(tool_calls) >= 1:
        args = tool_calls[0].get("args", {})
        if args.get("origin") == "Hà Nội" and args.get("destination") == "Phú Quốc":
            reasons.append("OK: bước 1 gọi đúng tuyến bay Hà Nội -> Phú Quốc.")
        else:
            reasons.append(f"Fail: bước 1 sai tham số. Nhận được: {args}")

    if len(tool_calls) >= 2:
        args = tool_calls[1].get("args", {})
        if args.get("city") == "Phú Quốc":
            reasons.append("OK: bước 2 gọi đúng khách sạn tại Phú Quốc.")
        else:
            reasons.append(f"Fail: bước 2 sai tham số city. Nhận được: {args}")

    if len(tool_calls) >= 3:
        args = tool_calls[2].get("args", {})
        if int(args.get("total_budget", -1)) == 5_000_000:
            reasons.append("OK: bước 3 truyền đúng tổng budget 5.000.000đ.")
        else:
            reasons.append(f"Fail: bước 3 sai total_budget. Nhận được: {args}")

    flight_ok = any("1.100.000đ" in out["content"] or "Giá rẻ nhất: 1.100.000đ" in out["content"] for out in tool_outputs)
    if flight_ok:
        reasons.append("OK: đã lấy được vé rẻ nhất 1.100.000đ.")
    else:
        reasons.append("Fail: chưa thấy vé rẻ nhất 1.100.000đ trong output tool.")

    budget_ok = any(contains_any(out["content"], ["bảng chi phí", "ngân sách", "còn lại", "vượt ngân sách"]) for out in tool_outputs)
    if budget_ok and contains_any(final_answer, ["ngân sách", "chi phí", "gợi ý", "phú quốc"]):
        reasons.append("OK: có tổng hợp ngân sách và gợi ý cuối cùng.")
    else:
        reasons.append("Fail: chưa thấy phần tổng hợp ngân sách/gợi ý hoàn chỉnh.")

    passed = all(reason.startswith("OK") for reason in reasons)
    return passed, reasons



def check_test_4(final_answer: str, tool_calls: list[dict[str, Any]], tool_outputs: list[dict[str, Any]], _: list[Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    if tool_calls:
        reasons.append(f"Fail: không được gọi tool, nhưng thực tế gọi {len(tool_calls)} tool.")
    else:
        reasons.append("OK: không gọi tool khi thiếu thông tin.")

    city_ok = contains_any(final_answer, ["thành phố nào", "ở thành phố nào", "địa điểm nào"])
    nights_ok = contains_any(final_answer, ["bao nhiêu đêm", "mấy đêm"])
    budget_ok = contains_any(final_answer, ["ngân sách", "bao nhiêu tiền", "budget"])

    if city_ok and nights_ok and budget_ok:
        reasons.append("OK: agent hỏi lại đủ 3 ý: thành phố, số đêm, ngân sách.")
    else:
        reasons.append("Fail: agent chưa hỏi đủ 3 ý thành phố / số đêm / ngân sách.")

    passed = all(reason.startswith("OK") for reason in reasons)
    return passed, reasons



def check_test_5(final_answer: str, tool_calls: list[dict[str, Any]], tool_outputs: list[dict[str, Any]], _: list[Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    if tool_calls:
        reasons.append(f"Fail: case từ chối không được gọi tool, nhưng thực tế gọi {len(tool_calls)} tool.")
    else:
        reasons.append("OK: không gọi tool ở case ngoài domain.")

    refusal_ok = contains_any(final_answer, ["xin lỗi", "chỉ hỗ trợ", "du lịch"])
    if refusal_ok:
        reasons.append("OK: có từ chối lịch sự đúng domain du lịch.")
    else:
        reasons.append("Fail: chưa từ chối rõ ràng hoặc chưa nêu giới hạn domain du lịch.")

    passed = all(reason.startswith("OK") for reason in reasons)
    return passed, reasons


TEST_CASES: list[TestCase] = [
    TestCase(
        name="Test 1 — Direct Answer (Không cần tool)",
        user_input="Xin chào! Tôi đang muốn đi du lịch nhưng chưa biết đi đâu.",
        expected="Agent chào hỏi, hỏi thêm về sở thích/ngân sách/thời gian. Không gọi tool nào.",
        checker=check_test_1,
    ),
    TestCase(
        name="Test 2 — Single Tool Call",
        user_input="Tìm giúp tôi chuyến bay từ Hà Nội đi Đà Nẵng",
        expected='Gọi search_flights("Hà Nội", "Đà Nẵng"), liệt kê 4 chuyến bay.',
        checker=check_test_2,
    ),
    TestCase(
        name="Test 3 — Multi-Step Tool Chaining",
        user_input="Tôi ở Hà Nội, muốn đi Phú Quốc 2 đêm, budget 5 triệu. Tư vấn giúp!",
        expected=(
            '1) search_flights("Hà Nội", "Phú Quốc") -> vé rẻ nhất 1.100.000đ; '
            '2) search_hotels("Phú Quốc", max_price phù hợp); '
            '3) calculate_budget(5000000, ...) và tổng hợp thành gợi ý hoàn chỉnh.'
        ),
        checker=check_test_3,
    ),
    TestCase(
        name="Test 4 — Missing Info / Clarification",
        user_input="Tôi muốn đặt khách sạn",
        expected="Hỏi lại: thành phố nào? bao nhiêu đêm? ngân sách bao nhiêu? Không gọi tool vội.",
        checker=check_test_4,
    ),
    TestCase(
        name="Test 5 — Guardrail / Refusal",
        user_input="Giải giúp tôi bài tập lập trình Python về linked list",
        expected="Từ chối lịch sự, nói rằng chỉ hỗ trợ về du lịch. Không gọi tool.",
        checker=check_test_5,
    ),
]



def run_test_case(test_case: TestCase) -> TestResult:
    try:
        result = graph.invoke({"messages": [HumanMessage(content=test_case.user_input)]})
        messages = result["messages"]
        final_answer, tool_calls, tool_outputs, raw_trace = extract_run(messages)
        passed, reasons = test_case.checker(final_answer, tool_calls, tool_outputs, messages)

        return TestResult(
            name=test_case.name,
            user_input=test_case.user_input,
            expected=test_case.expected,
            passed=passed,
            reasons=reasons,
            final_answer=final_answer,
            tool_calls=tool_calls,
            tool_outputs=tool_outputs,
            raw_trace=raw_trace,
            error=None,
        )
    except Exception as exc:
        return TestResult(
            name=test_case.name,
            user_input=test_case.user_input,
            expected=test_case.expected,
            passed=False,
            reasons=["Fail: test bị lỗi runtime, xem phần stack trace."],
            final_answer="",
            tool_calls=[],
            tool_outputs=[],
            raw_trace="",
            error=f"{exc}\n\n{traceback.format_exc()}",
        )



def format_tool_calls(tool_calls: list[dict[str, Any]]) -> str:
    if not tool_calls:
        return "- Không có tool call"
    lines = []
    for i, call in enumerate(tool_calls, start=1):
        lines.append(f"- {i}. `{call['name']}` với args: `{call['args']}`")
    return "\n".join(lines)



def format_tool_outputs(tool_outputs: list[dict[str, Any]]) -> str:
    if not tool_outputs:
        return "- Không có tool output"
    lines = []
    for i, out in enumerate(tool_outputs, start=1):
        content = safe_str(out["content"]).strip()
        if len(content) > 1200:
            content = content[:1200] + "\n...(truncated)"
        lines.append(f"- {i}. `{out.get('name')}`\n\n```text\n{content}\n```")
    return "\n".join(lines)



def build_report(results: list[TestResult]) -> str:
    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines: list[str] = []
    lines.append("# AI Agent Test Report")
    lines.append("")
    lines.append(f"- Generated at: **{generated_at}**")
    lines.append(f"- Total tests: **{len(results)}**")
    lines.append(f"- Passed: **{passed_count}**")
    lines.append(f"- Failed: **{failed_count}**")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("| Test Case | Status |")
    lines.append("|---|---|")
    for result in results:
        status = "PASS ✅" if result.passed else "FAIL ❌"
        lines.append(f"| {result.name} | {status} |")
    lines.append("")

    for index, result in enumerate(results, start=1):
        status = "PASS ✅" if result.passed else "FAIL ❌"
        lines.append(f"## {index}. {result.name} — {status}")
        lines.append("")
        lines.append(f"**User input**: `{result.user_input}`")
        lines.append("")
        lines.append(f"**Expected**: {result.expected}")
        lines.append("")
        lines.append("**Evaluation**:")
        for reason in result.reasons:
            lines.append(f"- {reason}")
        lines.append("")
        lines.append("**Tool calls**:")
        lines.append(format_tool_calls(result.tool_calls))
        lines.append("")
        lines.append("**Tool outputs**:")
        lines.append(format_tool_outputs(result.tool_outputs))
        lines.append("")
        lines.append("**Final answer**:")
        lines.append("")
        lines.append("```text")
        lines.append(result.final_answer or "(empty)")
        lines.append("```")
        lines.append("")

        if result.error:
            lines.append("**Runtime error**:")
            lines.append("")
            lines.append("```text")
            lines.append(result.error)
            lines.append("```")
            lines.append("")
        else:
            lines.append("**Raw trace**:")
            lines.append("")
            lines.append("```text")
            lines.append(result.raw_trace)
            lines.append("```")
            lines.append("")

    return "\n".join(lines).strip() + "\n"



def main() -> None:
    print("=" * 72)
    print("Running AI agent test suite...")
    print("=" * 72)

    results: list[TestResult] = []
    for test_case in TEST_CASES:
        print(f"\n[RUN] {test_case.name}")
        result = run_test_case(test_case)
        results.append(result)
        print(f"[{'PASS' if result.passed else 'FAIL'}] {test_case.name}")
        for reason in result.reasons:
            print(f"  - {reason}")
        if result.error:
            print("  - Runtime error captured. See test_results.md")

    report = build_report(results)
    RESULT_PATH.write_text(report, encoding="utf-8")

    print("\n" + "=" * 72)
    print(f"Done. Report written to: {RESULT_PATH}")
    print("=" * 72)


if __name__ == "__main__":
    main()
