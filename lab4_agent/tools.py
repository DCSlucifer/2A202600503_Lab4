from langchain_core.tools import tool

# =========================================================
# MOCK DATA — Dữ liệu giả lập hệ thống du lịch
# =========================================================

FLIGHTS_DB = {
    ("Hà Nội", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "07:20", "price": 1_450_000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "14:00", "arrival": "15:20", "price": 2_800_000, "class": "business"},
        {"airline": "VietJet Air", "departure": "08:30", "arrival": "09:50", "price": 890_000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "11:00", "arrival": "12:20", "price": 1_200_000, "class": "economy"},
    ],
    ("Hà Nội", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "07:00", "arrival": "09:15", "price": 2_100_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "10:00", "arrival": "12:15", "price": 1_350_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "16:00", "arrival": "18:15", "price": 1_100_000, "class": "economy"},
    ],
    ("Hà Nội", "Hồ Chí Minh"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "08:10", "price": 1_600_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "07:30", "arrival": "09:40", "price": 950_000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "12:00", "arrival": "14:10", "price": 1_300_000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "18:00", "arrival": "20:10", "price": 3_200_000, "class": "business"},
    ],
    ("Hồ Chí Minh", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "09:00", "arrival": "10:20", "price": 1_300_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "13:00", "arrival": "14:20", "price": 780_000, "class": "economy"},
    ],
    ("Hồ Chí Minh", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "08:00", "arrival": "09:00", "price": 1_100_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "15:00", "arrival": "16:00", "price": 650_000, "class": "economy"},
    ],
}

HOTELS_DB = {
    "Đà Nẵng": [
        {"name": "Mường Thanh Luxury", "stars": 5, "price_per_night": 1_800_000, "area": "Mỹ Khê", "rating": 4.5},
        {"name": "Sala Danang Beach", "stars": 4, "price_per_night": 1_200_000, "area": "Mỹ Khê", "rating": 4.3},
        {"name": "Fivitel Danang", "stars": 3, "price_per_night": 650_000, "area": "Sơn Trà", "rating": 4.1},
        {"name": "Memory Hostel", "stars": 2, "price_per_night": 250_000, "area": "Hải Châu", "rating": 4.6},
        {"name": "Christina's Homestay", "stars": 2, "price_per_night": 350_000, "area": "An Thượng", "rating": 4.7},
    ],
    "Phú Quốc": [
        {"name": "Vinpearl Resort", "stars": 5, "price_per_night": 3_500_000, "area": "Bãi Dài", "rating": 4.4},
        {"name": "Sol by Meliá", "stars": 4, "price_per_night": 1_500_000, "area": "Bãi Trường", "rating": 4.2},
        {"name": "Lahana Resort", "stars": 3, "price_per_night": 800_000, "area": "Dương Đông", "rating": 4.0},
        {"name": "9Station Hostel", "stars": 2, "price_per_night": 200_000, "area": "Dương Đông", "rating": 4.5},
    ],
    "Hồ Chí Minh": [
        {"name": "Rex Hotel", "stars": 5, "price_per_night": 2_800_000, "area": "Quận 1", "rating": 4.3},
        {"name": "Liberty Central", "stars": 4, "price_per_night": 1_400_000, "area": "Quận 1", "rating": 4.1},
        {"name": "Cochin Zen Hotel", "stars": 3, "price_per_night": 550_000, "area": "Quận 3", "rating": 4.4},
        {"name": "The Common Room", "stars": 2, "price_per_night": 180_000, "area": "Quận 1", "rating": 4.6},
    ],
}

# =========================================================
# City alias normalization
# Giúp tool nhận diện các cách gọi thành phố phổ biến
# =========================================================
_CITY_ALIASES: dict[str, str] = {
    # Hồ Chí Minh variants
    "sài gòn": "Hồ Chí Minh",
    "saigon": "Hồ Chí Minh",
    "hcm": "Hồ Chí Minh",
    "tp hcm": "Hồ Chí Minh",
    "tphcm": "Hồ Chí Minh",
    "tp.hcm": "Hồ Chí Minh",
    "thành phố hồ chí minh": "Hồ Chí Minh",
    "ho chi minh": "Hồ Chí Minh",
    "hồ chí minh": "Hồ Chí Minh",
    # Hà Nội variants
    "hanoi": "Hà Nội",
    "ha noi": "Hà Nội",
    "hà nội": "Hà Nội",
    # Đà Nẵng variants
    "da nang": "Đà Nẵng",
    "danang": "Đà Nẵng",
    "đà nẵng": "Đà Nẵng",
    # Phú Quốc variants
    "phu quoc": "Phú Quốc",
    "phú quốc": "Phú Quốc",
}


def _normalize_city(city: str) -> str:
    """Chuẩn hoá tên thành phố về dạng chuẩn trong DB."""
    key = city.strip().lower()
    return _CITY_ALIASES.get(key, city.strip())


def _format_currency(amount: int) -> str:
    return f"{amount:,}".replace(",", ".") + "đ"


def _prettify_expense_name(name: str) -> str:
    cleaned = name.strip().replace("_", " ")
    return cleaned[:1].upper() + cleaned[1:] if cleaned else cleaned


@tool
def search_flights(origin: str, destination: str) -> str:
    """
    Tìm kiếm các chuyến bay giữa hai thành phố.

    Tham số:
    - origin: thành phố khởi hành (VD: 'Hà Nội', 'Hồ Chí Minh', 'Sài Gòn')
    - destination: thành phố đến (VD: 'Đà Nẵng', 'Phú Quốc')

    Trả về danh sách chuyến bay sắp xếp theo giá tăng dần với hãng, giờ bay, giá vé, hạng ghế.
    Nếu không tìm thấy tuyến bay, thử tra chiều ngược lại và thông báo rõ ràng.
    """
    try:
        origin = _normalize_city(origin)
        destination = _normalize_city(destination)

        if not origin or not destination:
            return "Lỗi: origin và destination không được để trống."

        if origin == destination:
            return "Lỗi: điểm đi và điểm đến không được trùng nhau."

        flights = FLIGHTS_DB.get((origin, destination))

        if flights:
            flights_sorted = sorted(flights, key=lambda item: item["price"])
            lines = [f"✈️ Các chuyến bay từ {origin} đến {destination}:"]
            for idx, flight in enumerate(flights_sorted, start=1):
                seat_class = flight.get("class", "economy").capitalize()
                lines.append(
                    f"  {idx}. {flight['airline']} | {flight['departure']} → {flight['arrival']} | "
                    f"{seat_class} | {_format_currency(flight['price'])}"
                )
            cheapest = flights_sorted[0]["price"]
            lines.append(f"\n💡 Giá rẻ nhất: {_format_currency(cheapest)}")
            return "\n".join(lines)

        # Thử tra chiều ngược lại
        reverse_flights = FLIGHTS_DB.get((destination, origin))
        if reverse_flights:
            return (
                f"Không tìm thấy chuyến bay từ {origin} đến {destination}. "
                f"Hệ thống có dữ liệu chiều ngược lại từ {destination} đến {origin}. "
                f"Bạn có muốn xem không?"
            )

        return (
            f"Không tìm thấy chuyến bay từ {origin} đến {destination}. "
            f"Hệ thống hiện hỗ trợ các tuyến: Hà Nội ↔ Đà Nẵng, Hà Nội ↔ Phú Quốc, "
            f"Hà Nội ↔ Hồ Chí Minh, Hồ Chí Minh ↔ Đà Nẵng, Hồ Chí Minh ↔ Phú Quốc."
        )

    except Exception as e:
        return f"Lỗi khi tìm chuyến bay: {str(e)}"


@tool
def search_hotels(city: str, max_price_per_night: int = 99_999_999) -> str:
    """
    Tìm kiếm khách sạn tại một thành phố, lọc theo giá tối đa mỗi đêm.

    Tham số:
    - city: tên thành phố (VD: 'Đà Nẵng', 'Phú Quốc', 'Hồ Chí Minh')
    - max_price_per_night: giá tối đa mỗi đêm (VND), mặc định không giới hạn

    Trả về danh sách khách sạn phù hợp, sắp xếp theo rating giảm dần,
    với tên, số sao, khu vực, rating và giá mỗi đêm.
    """
    try:
        city = _normalize_city(city)

        if not city:
            return "Lỗi: city không được để trống."

        if max_price_per_night < 0:
            return "Lỗi: max_price_per_night phải >= 0."

        hotels = HOTELS_DB.get(city)
        if not hotels:
            supported = ", ".join(HOTELS_DB.keys())
            return (
                f"Không tìm thấy dữ liệu khách sạn cho thành phố '{city}'. "
                f"Hệ thống hiện hỗ trợ: {supported}."
            )

        # Lọc theo ngân sách
        filtered = [h for h in hotels if h["price_per_night"] <= max_price_per_night]

        # Sắp xếp theo rating giảm dần
        filtered.sort(key=lambda h: h["rating"], reverse=True)

        if not filtered:
            cheapest_available = min(hotels, key=lambda h: h["price_per_night"])
            return (
                f"Không tìm thấy khách sạn tại {city} với giá dưới "
                f"{_format_currency(max_price_per_night)}/đêm.\n"
                f"💡 Khách sạn rẻ nhất hiện có: {cheapest_available['name']} "
                f"— {_format_currency(cheapest_available['price_per_night'])}/đêm. "
                f"Bạn có muốn điều chỉnh ngân sách không?"
            )

        limit_str = (
            f"{_format_currency(max_price_per_night)}/đêm"
            if max_price_per_night < 99_999_999
            else "không giới hạn"
        )
        lines = [f"🏨 Khách sạn tại {city} (ngân sách tối đa {limit_str}):"]
        for idx, h in enumerate(filtered, start=1):
            lines.append(
                f"  {idx}. {h['name']} | {h['stars']}★ | {h['area']} | "
                f"Rating {h['rating']}/5 | {_format_currency(h['price_per_night'])}/đêm"
            )
        return "\n".join(lines)

    except Exception as e:
        return f"Lỗi khi tìm khách sạn: {str(e)}"


@tool
def calculate_budget(total_budget: int, expenses: str) -> str:
    """
    Tính toán ngân sách còn lại sau khi trừ các khoản chi phí chuyến đi.

    Tham số:
    - total_budget: tổng ngân sách ban đầu (VND, số nguyên dương)
    - expenses: chuỗi các khoản chi, phân tách bằng dấu phẩy,
                định dạng 'tên_khoản:số_tiền'
                VD: 'vé_máy_bay:1100000,khách_sạn:1600000,ăn_uống:500000'

    Trả về bảng chi tiết từng khoản, tổng chi, ngân sách còn lại.
    Nếu vượt ngân sách, cảnh báo rõ số tiền thiếu và gợi ý điều chỉnh.
    """
    try:
        if total_budget < 0:
            return "Lỗi: total_budget phải là số nguyên không âm."

        if not expenses or not expenses.strip():
            return (
                "Lỗi định dạng expenses: vui lòng nhập theo dạng "
                "'vé_bay:1100000,khách_sạn:1600000'."
            )

        parsed_expenses: list[tuple[str, int]] = []

        for raw_item in expenses.split(","):
            item = raw_item.strip()
            if not item:
                continue

            if ":" not in item:
                return (
                    f"Lỗi định dạng: khoản '{item}' không đúng dạng 'tên_khoản:số_tiền'. "
                    f"Ví dụ: 'vé_bay:1100000,khách_sạn:1600000'."
                )

            name, amount_str = item.split(":", 1)
            name = name.strip()
            amount_str = amount_str.strip()

            if not name:
                return "Lỗi định dạng: tên khoản chi không được để trống."
            if not amount_str:
                return f"Lỗi định dạng: khoản '{name}' chưa có số tiền."

            # Cho phép dấu chấm phân tách hàng nghìn (VD: 1.100.000)
            amount_str = amount_str.replace(".", "").replace(",", "")

            try:
                amount = int(amount_str)
            except ValueError:
                return (
                    f"Lỗi định dạng: số tiền '{amount_str}' của khoản '{name}' không hợp lệ. "
                    f"Vui lòng nhập số nguyên (VD: 1100000)."
                )

            if amount < 0:
                return f"Lỗi: khoản chi '{name}' không được là số âm."

            parsed_expenses.append((name, amount))

        if not parsed_expenses:
            return "Lỗi: không có khoản chi hợp lệ nào trong expenses."

        total_expense = sum(amt for _, amt in parsed_expenses)
        remaining = total_budget - total_expense

        lines = ["📊 Bảng chi phí chuyến đi:"]
        for name, amt in parsed_expenses:
            lines.append(f"  • {_prettify_expense_name(name)}: {_format_currency(amt)}")

        lines += [
            "  " + "─" * 36,
            f"  Tổng chi tiêu : {_format_currency(total_expense)}",
            f"  Ngân sách ban đầu: {_format_currency(total_budget)}",
        ]

        if remaining >= 0:
            lines.append(f"  ✅ Còn lại       : {_format_currency(remaining)}")
            if remaining < total_budget * 0.1:
                lines.append("  ⚠️  Ngân sách còn rất ít — nên dự phòng thêm chi phí phát sinh.")
        else:
            lines.append(f"  ❌ Vượt ngân sách: {_format_currency(abs(remaining))}")
            lines.append(
                "  💡 Gợi ý: cân nhắc chọn khách sạn rẻ hơn, giảm số đêm, "
                "hoặc tìm vé máy bay giờ khác để tiết kiệm."
            )

        return "\n".join(lines)

    except Exception as e:
        return f"Lỗi khi tính ngân sách: {str(e)}"