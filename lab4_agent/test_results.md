# AI Agent Test Report

- Generated at: **2026-04-07 15:12:14**
- Total tests: **5**
- Passed: **5**
- Failed: **0**

## Summary

| Test Case | Status |
|---|---|
| Test 1 — Direct Answer (Không cần tool) | PASS ✅ |
| Test 2 — Single Tool Call | PASS ✅ |
| Test 3 — Multi-Step Tool Chaining | PASS ✅ |
| Test 4 — Missing Info / Clarification | PASS ✅ |
| Test 5 — Guardrail / Refusal | PASS ✅ |

## 1. Test 1 — Direct Answer (Không cần tool) — PASS ✅

**User input**: `Xin chào! Tôi đang muốn đi du lịch nhưng chưa biết đi đâu.`

**Expected**: Agent chào hỏi, hỏi thêm về sở thích/ngân sách/thời gian. Không gọi tool nào.

**Evaluation**:
- OK: không gọi tool.
- OK: có chào hỏi.
- OK: có hỏi thêm thông tin cần thiết.

**Tool calls**:
- Không có tool call

**Tool outputs**:
- Không có tool output

**Final answer**:

```text
Chào bạn! Mình là TravelBuddy — trợ lý du lịch thông minh. Bạn đang dự định đi đâu, trong bao nhiêu ngày và ngân sách khoảng bao nhiêu? Cho mình biết để tư vấn chuyến đi phù hợp nhất nhé!
```

**Raw trace**:

```text
[HUMAN]
Xin chào! Tôi đang muốn đi du lịch nhưng chưa biết đi đâu.

[AI]
Chào bạn! Mình là TravelBuddy — trợ lý du lịch thông minh. Bạn đang dự định đi đâu, trong bao nhiêu ngày và ngân sách khoảng bao nhiêu? Cho mình biết để tư vấn chuyến đi phù hợp nhất nhé!
```

## 2. Test 2 — Single Tool Call — PASS ✅

**User input**: `Tìm giúp tôi chuyến bay từ Hà Nội đi Đà Nẵng`

**Expected**: Gọi search_flights("Hà Nội", "Đà Nẵng"), liệt kê 4 chuyến bay.

**Evaluation**:
- OK: chỉ gọi đúng 1 tool search_flights.
- OK: tham số tool đúng (Hà Nội -> Đà Nẵng).
- OK: tool trả về ít nhất 4 chuyến bay.
- OK: có tổng hợp kết quả cho user.

**Tool calls**:
- 1. `search_flights` với args: `{'origin': 'Hà Nội', 'destination': 'Đà Nẵng'}`

**Tool outputs**:
- 1. `search_flights`

```text
✈️ Các chuyến bay từ Hà Nội đến Đà Nẵng:
  1. VietJet Air | 08:30 → 09:50 | Economy | 890.000đ
  2. Bamboo Airways | 11:00 → 12:20 | Economy | 1.200.000đ
  3. Vietnam Airlines | 06:00 → 07:20 | Economy | 1.450.000đ
  4. Vietnam Airlines | 14:00 → 15:20 | Business | 2.800.000đ

💡 Giá rẻ nhất: 890.000đ
```

**Final answer**:

```text
Dưới đây là các chuyến bay từ Hà Nội đi Đà Nẵng:

✈️ Chuyến bay:
1. **VietJet Air** | 08:30 → 09:50 | Hạng: Economy | Giá: 890.000đ
2. **Bamboo Airways** | 11:00 → 12:20 | Hạng: Economy | Giá: 1.200.000đ
3. **Vietnam Airlines** | 06:00 → 07:20 | Hạng: Economy | Giá: 1.450.000đ
4. **Vietnam Airlines** | 14:00 → 15:20 | Hạng: Business | Giá: 2.800.000đ

💡 Giá rẻ nhất: **890.000đ** (VietJet Air)

Nếu bạn cần thêm thông tin hoặc muốn đặt vé, hãy cho mình biết nhé!
```

**Raw trace**:

```text
[HUMAN]
Tìm giúp tôi chuyến bay từ Hà Nội đi Đà Nẵng

[AI - tool request]
(empty content)

  -> search_flights({'origin': 'Hà Nội', 'destination': 'Đà Nẵng'})

[TOOL search_flights]
✈️ Các chuyến bay từ Hà Nội đến Đà Nẵng:
  1. VietJet Air | 08:30 → 09:50 | Economy | 890.000đ
  2. Bamboo Airways | 11:00 → 12:20 | Economy | 1.200.000đ
  3. Vietnam Airlines | 06:00 → 07:20 | Economy | 1.450.000đ
  4. Vietnam Airlines | 14:00 → 15:20 | Business | 2.800.000đ

💡 Giá rẻ nhất: 890.000đ

[AI]
Dưới đây là các chuyến bay từ Hà Nội đi Đà Nẵng:

✈️ Chuyến bay:
1. **VietJet Air** | 08:30 → 09:50 | Hạng: Economy | Giá: 890.000đ
2. **Bamboo Airways** | 11:00 → 12:20 | Hạng: Economy | Giá: 1.200.000đ
3. **Vietnam Airlines** | 06:00 → 07:20 | Hạng: Economy | Giá: 1.450.000đ
4. **Vietnam Airlines** | 14:00 → 15:20 | Hạng: Business | Giá: 2.800.000đ

💡 Giá rẻ nhất: **890.000đ** (VietJet Air)

Nếu bạn cần thêm thông tin hoặc muốn đặt vé, hãy cho mình biết nhé!
```

## 3. Test 3 — Multi-Step Tool Chaining — PASS ✅

**User input**: `Tôi ở Hà Nội, muốn đi Phú Quốc 2 đêm, budget 5 triệu. Tư vấn giúp!`

**Expected**: 1) search_flights("Hà Nội", "Phú Quốc") -> vé rẻ nhất 1.100.000đ; 2) search_hotels("Phú Quốc", max_price phù hợp); 3) calculate_budget(5000000, ...) và tổng hợp thành gợi ý hoàn chỉnh.

**Evaluation**:
- OK: tool chain đúng thứ tự search_flights -> search_hotels -> calculate_budget.
- OK: bước 1 gọi đúng tuyến bay Hà Nội -> Phú Quốc.
- OK: bước 2 gọi đúng khách sạn tại Phú Quốc.
- OK: bước 3 truyền đúng tổng budget 5.000.000đ.
- OK: đã lấy được vé rẻ nhất 1.100.000đ.
- OK: có tổng hợp ngân sách và gợi ý cuối cùng.

**Tool calls**:
- 1. `search_flights` với args: `{'origin': 'Hà Nội', 'destination': 'Phú Quốc'}`
- 2. `search_hotels` với args: `{'city': 'Phú Quốc', 'max_price_per_night': 2500000}`
- 3. `calculate_budget` với args: `{'total_budget': 5000000, 'expenses': 'vé_máy_bay:1100000,khách_sạn:1600000'}`

**Tool outputs**:
- 1. `search_flights`

```text
✈️ Các chuyến bay từ Hà Nội đến Phú Quốc:
  1. VietJet Air | 16:00 → 18:15 | Economy | 1.100.000đ
  2. VietJet Air | 10:00 → 12:15 | Economy | 1.350.000đ
  3. Vietnam Airlines | 07:00 → 09:15 | Economy | 2.100.000đ

💡 Giá rẻ nhất: 1.100.000đ
```
- 2. `search_hotels`

```text
🏨 Khách sạn tại Phú Quốc (ngân sách tối đa 2.500.000đ/đêm):
  1. 9Station Hostel | 2★ | Dương Đông | Rating 4.5/5 | 200.000đ/đêm
  2. Sol by Meliá | 4★ | Bãi Trường | Rating 4.2/5 | 1.500.000đ/đêm
  3. Lahana Resort | 3★ | Dương Đông | Rating 4.0/5 | 800.000đ/đêm
```
- 3. `calculate_budget`

```text
📊 Bảng chi phí chuyến đi:
  • Vé máy bay: 1.100.000đ
  • Khách sạn: 1.600.000đ
  ────────────────────────────────────
  Tổng chi tiêu : 2.700.000đ
  Ngân sách ban đầu: 5.000.000đ
  ✅ Còn lại       : 2.300.000đ
```

**Final answer**:

```text
Dưới đây là kế hoạch cho chuyến đi của bạn từ Hà Nội đến Phú Quốc trong 2 đêm với ngân sách 5 triệu:

✈️ **Chuyến bay:**
- **VietJet Air** | 16:00 → 18:15 | Economy | **1.100.000đ**
- **VietJet Air** | 10:00 → 12:15 | Economy | 1.350.000đ
- **Vietnam Airlines** | 07:00 → 09:15 | Economy | 2.100.000đ

💡 **Giá rẻ nhất:** 1.100.000đ

🏨 **Khách sạn gợi ý:**
- **9Station Hostel** | 2★ | Dương Đông | Rating 4.5/5 | **200.000đ/đêm**
- **Sol by Meliá** | 4★ | Bãi Trường | Rating 4.2/5 | **1.500.000đ/đêm**
- **Lahana Resort** | 3★ | Dương Đông | Rating 4.0/5 | **800.000đ/đêm**

📊 **Tổng chi phí ước tính:**
- **Vé máy bay:** 1.100.000đ
- **Khách sạn (2 đêm tại 9Station Hostel):** 400.000đ
────────────────────────────────────
**Tổng chi tiêu:** 1.500.000đ  
**Ngân sách ban đầu:** 5.000.000đ  
✅ **Còn lại:** 3.500.000đ

💡 **Gợi ý thêm:**
Bạn còn dư ngân sách để chi cho ăn uống và các hoạt động vui chơi tại Phú Quốc. Nếu cần thêm thông tin hoặc hỗ trợ gì khác, hãy cho mình biết nhé!
```

**Raw trace**:

```text
[HUMAN]
Tôi ở Hà Nội, muốn đi Phú Quốc 2 đêm, budget 5 triệu. Tư vấn giúp!

[AI - tool request]
(empty content)

  -> search_flights({'origin': 'Hà Nội', 'destination': 'Phú Quốc'})

  -> search_hotels({'city': 'Phú Quốc', 'max_price_per_night': 2500000})

[TOOL search_flights]
✈️ Các chuyến bay từ Hà Nội đến Phú Quốc:
  1. VietJet Air | 16:00 → 18:15 | Economy | 1.100.000đ
  2. VietJet Air | 10:00 → 12:15 | Economy | 1.350.000đ
  3. Vietnam Airlines | 07:00 → 09:15 | Economy | 2.100.000đ

💡 Giá rẻ nhất: 1.100.000đ

[TOOL search_hotels]
🏨 Khách sạn tại Phú Quốc (ngân sách tối đa 2.500.000đ/đêm):
  1. 9Station Hostel | 2★ | Dương Đông | Rating 4.5/5 | 200.000đ/đêm
  2. Sol by Meliá | 4★ | Bãi Trường | Rating 4.2/5 | 1.500.000đ/đêm
  3. Lahana Resort | 3★ | Dương Đông | Rating 4.0/5 | 800.000đ/đêm

[AI - tool request]
(empty content)

  -> calculate_budget({'total_budget': 5000000, 'expenses': 'vé_máy_bay:1100000,khách_sạn:1600000'})

[TOOL calculate_budget]
📊 Bảng chi phí chuyến đi:
  • Vé máy bay: 1.100.000đ
  • Khách sạn: 1.600.000đ
  ────────────────────────────────────
  Tổng chi tiêu : 2.700.000đ
  Ngân sách ban đầu: 5.000.000đ
  ✅ Còn lại       : 2.300.000đ

[AI]
Dưới đây là kế hoạch cho chuyến đi của bạn từ Hà Nội đến Phú Quốc trong 2 đêm với ngân sách 5 triệu:

✈️ **Chuyến bay:**
- **VietJet Air** | 16:00 → 18:15 | Economy | **1.100.000đ**
- **VietJet Air** | 10:00 → 12:15 | Economy | 1.350.000đ
- **Vietnam Airlines** | 07:00 → 09:15 | Economy | 2.100.000đ

💡 **Giá rẻ nhất:** 1.100.000đ

🏨 **Khách sạn gợi ý:**
- **9Station Hostel** | 2★ | Dương Đông | Rating 4.5/5 | **200.000đ/đêm**
- **Sol by Meliá** | 4★ | Bãi Trường | Rating 4.2/5 | **1.500.000đ/đêm**
- **Lahana Resort** | 3★ | Dương Đông | Rating 4.0/5 | **800.000đ/đêm**

📊 **Tổng chi phí ước tính:**
- **Vé máy bay:** 1.100.000đ
- **Khách sạn (2 đêm tại 9Station Hostel):** 400.000đ
────────────────────────────────────
**Tổng chi tiêu:** 1.500.000đ  
**Ngân sách ban đầu:** 5.000.000đ  
✅ **Còn lại:** 3.500.000đ

💡 **Gợi ý thêm:**
Bạn còn dư ngân sách để chi cho ăn uống và các hoạt động vui chơi tại Phú Quốc. Nếu cần thêm thông tin hoặc hỗ trợ gì khác, hãy cho mình biết nhé!
```

## 4. Test 4 — Missing Info / Clarification — PASS ✅

**User input**: `Tôi muốn đặt khách sạn`

**Expected**: Hỏi lại: thành phố nào? bao nhiêu đêm? ngân sách bao nhiêu? Không gọi tool vội.

**Evaluation**:
- OK: không gọi tool khi thiếu thông tin.
- OK: agent hỏi lại đủ 3 ý: thành phố, số đêm, ngân sách.

**Tool calls**:
- Không có tool call

**Tool outputs**:
- Không có tool output

**Final answer**:

```text
Bạn muốn đặt khách sạn ở thành phố nào, bao nhiêu đêm, và ngân sách khoảng bao nhiêu để mình lọc lựa chọn phù hợp cho bạn?
```

**Raw trace**:

```text
[HUMAN]
Tôi muốn đặt khách sạn

[AI]
Bạn muốn đặt khách sạn ở thành phố nào, bao nhiêu đêm, và ngân sách khoảng bao nhiêu để mình lọc lựa chọn phù hợp cho bạn?
```

## 5. Test 5 — Guardrail / Refusal — PASS ✅

**User input**: `Giải giúp tôi bài tập lập trình Python về linked list`

**Expected**: Từ chối lịch sự, nói rằng chỉ hỗ trợ về du lịch. Không gọi tool.

**Evaluation**:
- OK: không gọi tool ở case ngoài domain.
- OK: có từ chối lịch sự đúng domain du lịch.

**Tool calls**:
- Không có tool call

**Tool outputs**:
- Không có tool output

**Final answer**:

```text
Xin lỗi, mình chỉ hỗ trợ các yêu cầu liên quan đến du lịch như chuyến bay, khách sạn, lịch trình và ngân sách chuyến đi. Nếu bạn cần tư vấn du lịch, mình sẵn sàng hỗ trợ ngay!
```

**Raw trace**:

```text
[HUMAN]
Giải giúp tôi bài tập lập trình Python về linked list

[AI]
Xin lỗi, mình chỉ hỗ trợ các yêu cầu liên quan đến du lịch như chuyến bay, khách sạn, lịch trình và ngân sách chuyến đi. Nếu bạn cần tư vấn du lịch, mình sẵn sàng hỗ trợ ngay!
```
