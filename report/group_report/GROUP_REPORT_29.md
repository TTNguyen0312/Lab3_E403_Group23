# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: [29]
- **Team Members**: [Nguyễn Thị Ngọc, Nguyễn Trọng Tiến, Vũ Đức Minh, Nguyễn Việt Quang]
- **Deployment Date**: [2026-04-06]

---

## 1. Executive Summary

Trọng tâm của đội là xây dựng một **Travel Planner Agent** có khả năng tự động lên lịch trình du lịch dựa trên ngân sách (Ví dụ: *"Plan a 2-day trip to Da Nang under $200"*). Agent sử dụng công cụ tìm kiếm để tra cứu địa điểm/giá cả và máy tính để cộng dồn chi phí.

- **Success Rate**: Đạt 80% (16/20 test cases thành công) trên bộ dữ liệu kiểm thử.
- **Key Outcome**: Agent khắc phục được bài toán lớn nhất của Chatbot thuần là tình trạng "ảo giác dữ liệu". Nhờ có vòng lặp ReAct kết hợp tool `search` và `calculator`, hệ thống đưa ra lịch trình có chi phí sát thực tế và luôn tuân thủ nghiêm ngặt ngân sách cho phép. Phiên bản v2 của agent cũng khắc phục được sự ảo giác dữ liệu của phiên bản đầu tiên và gọi đúng vào luồng các tools.

### 1.1 Chatbot baseline

Baseline là lời gọi LLM một-shot qua `run_chatbot` (cùng provider/model có thể cấu hình với Agent), không tách bước Thought–Action–Observation và không gọi tool. Baseline dùng để so sánh công bằng với Agent trên cùng bộ prompt du lịch/ngân sách: Chatbot trả lời nhanh và mượt trên câu hỏi đơn, nhưng dễ tự suy diễn giá hoặc cộng sai khi bài toán đa bước — đó là lý do nhóm chuyển sang ReAct có `search` + `calculator`.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

*Lưu đồ đính kèm cùng thư mục báo cáo: `report/group_report/extra/flowchart.jpg`.*

![Agent flowchart](extra/flowchart.jpg)


**Mô tả chu trình hoạt động của hệ thống:**
1. **Start / Nhận yêu cầu:** Hệ thống tiếp nhận yêu cầu từ người dùng (bao gồm địa điểm, ngày đi, và ngân sách - budget).
2. **LLM Node (Phân tích yêu cầu):** Agent suy nghĩ (Thought) để bóc tách các thông tin cốt lõi từ prompt của người dùng.
3. **Search Tool:** Gọi công cụ tìm kiếm dữ liệu thực tế (khách sạn, ăn uống, điểm tham quan) kèm chi phí ước tính.
4. **Calculator Tool:** Trích xuất giá cả và gọi lệnh tính toán cộng dồn tất cả các khoản chi phí.
5. **Decision Node (Đánh giá ngân sách):** LLM đối chiếu tổng tiền với budget ban đầu.
   - **Nhánh Yes (Vượt budget):** Hệ thống chuyển sang bước **"Tối ưu lại chi phí (optimize)"** và tự động quay vòng (loop) ngược lại `LLM Node` để thay đổi địa điểm rẻ hơn.
   - **Nhánh No (Không vượt budget):** Hệ thống chốt chi phí và đi tiếp vào bước **"Tạo lịch trình chi tiết (itinerary)"**.
6. **Xuất kết quả (End):** Trả về lịch trình hoàn thiện (plan) kèm bảng báo cáo tổng chi phí cho người dùng cuối.

### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `search` | `string` (query) | Tra cứu địa điểm (places) và chi phí ước tính (costs). Ví dụ: "Cheap hotels in Da Nang". |
| `calculator` | `string` (math expression) | Tính toán cộng gộp hoặc trừ các khoản chi phí nhằm kiểm soát ngân sách. Ví dụ: "200 - 50 - 30". |

### 2.3 Tiến hóa mô tả tool (Agent v1 → v2)

| Khía cạnh | Agent v1 | Agent v2 (cải tiến) |
| :--- | :--- | :--- |
| **`search`** | Mô tả ngắn, không nhấn “chỉ dùng kết quả trả về từ tool”; dễ bịa thêm khi DB/mock trống. | Bổ sung quy tắc: nếu không có khớp địa điểm thì báo rõ và không tự tạo chi tiết; chuẩn hóa query (địa danh + loại chi phí). |
| **`calculator`** | Thiếu ví dụ JSON/tham số bắt buộc; LLM đôi khi gọi với tham số rỗng → lỗi parse. | Few-shot trong system prompt: luôn truyền biểu thức dạng chuỗi; cấm để trống `expression`. |
| **System prompt** | Tập trung mô tả nhiệm vụ chung. | Thêm thứ tự bắt buộc: search → tổng hợp giá → calculator → đối chiếu budget → Final Answer. |

### 2.4 LLM Providers & so sánh nhanh

- **Primary**: OpenAI GPT-4o — ưu tiên khi cần reasoning đa bước ổn định.
- **Alternate**: Google Gemini 1.5 Pro — dùng cùng interface `LLMProvider` để đổi provider chỉ bằng cấu hình.
- **Fallback (local)**: Llama / Phi qua `llama-cpp-python` khi cần giảm chi phí hoặc offline.

| Metric (ước lượng trên cùng 20 test, cùng prompt) | GPT-4o | Gemini 1.5 Pro |
| :--- | :--- | :--- |
| TTFT trung bình | ~380ms | ~420ms |
| Latency tổng (P50) một task Agent | ~4.4s | ~4.7s |
| Ghi chú | Hơi ổn định hơn với format JSON Action | Đôi khi thêm văn giải thích trước JSON (cần parser chắc) |

*(Số liệu lấy từ log telemetry `LOG_EVENT: LLM_METRIC` trong `logs/`; có thể lệch theo region/API.)*

---

## 3. Telemetry & Performance Dashboard

Số liệu dưới đây tổng hợp từ các file log (JSON) trong `logs/`, đối chiếu với các metric trong `EVALUATION.md` (token, latency, vòng lặp, lỗi).

### 3.1 Latency & token

- **TTFT trung bình (ước lượng)**: ~400ms (phụ thuộc provider; đo từ lần gọi LLM đầu tiên trong bước).
- **Average Latency (P50) — tổng thời gian task**: 4500ms (cao hơn Chatbot vì 4–5 bước ReAct + gọi search).
- **Max Latency (P99)**: 8200ms.
- **Average Tokens per Task**: 1250 tokens/query (Observation từ search còn dài).
- **Total Cost of Test Suite (ước lượng)**: ~$0.08 cho 20 test (cost mock/token trong `src/telemetry/metrics.py`).

### 3.2 Vòng lặp ReAct (loop / steps)

| Metric | Giá trị (trung bình trên các run thành công) |
| :--- | :--- |
| Số bước `Thought → Action → Observation` trước Final Answer | 3.8 (thường 3–5) |
| `max_steps` (cấu hình) | Đủ để kết thúc; một số case cận biên dừng do giới hạn bước thay vì lỗi logic |

### 3.3 Phân loại lỗi (từ trace / log)

| Loại | Mô tả ngắn | Tần suất tương đối (20 test) |
| :--- | :--- | :--- |
| JSON / parse | LLM trả Action không parse được hoặc tham số rỗng | Thấp sau khi có try/except + prompt v2 |
| Hallucination tool / sai tool | Gọi tool không tồn tại hoặc bỏ qua dữ liệu search | Trung bình ở v1; giảm mạnh ở v2 |
| Timeout `max_steps` | Lặp không thoát Final Answer | Hiếm |

### 3.4 Độ tin cậy tổng hợp: Agent v1 vs v2

| Phiên bản | Case pass / 20 | Ghi chú |
| :--- | :--- | :--- |
| Agent v1 | 14/20 (70%) | Nhiều lỗi hallucination khi DB không có địa điểm; parse tham số calculator không ổn định. |
| Agent v2 | 16/20 (80%) | Khắc phục nhờ prompt + mô tả tool; xử lý lỗi parse an toàn hơn. |

---

## 4. Trace chất lượng (thành công & thất bại)

*Phần này đáp ứng yêu cầu “cả trace thành công và thất bại” trong rubric; log thực tế nằm trong `logs/`.*

### 4.1 Trace thành công (rút gọn)

- **Input**: *"Plan a 2-day trip to Da Nang under $200"*
- **Luồng**: `Thought` (bóc budget + địa điểm) → `Action: search("...")` → `Observation` (giá ước tính từ mock/API) → `Action: calculator("150 + 30 + ...")` → `Observation` (tổng) → so khớp budget → `Final Answer` (itinerary + bảng chi phí).
- **Log**: Các bước tương ứng có `LOG_EVENT: LLM_METRIC` (latency, token) sau mỗi lần gọi LLM; không có `JSONDecodeError` trong chuỗi bước này.

### 4.2 RCA — Failure trace (hallucination)

*Phân tích điểm yếu (Weakness) mang tính đặc thù của team: "Less strict correctness" (Không cần đúng tuyệt đối 100%).*

### Case Study: Lỗi ảo giác dữ liệu (hallucination)
- **Input**: *"Lên kế hoạch du lịch Sydney"*
- **Observation**: Agent gọi `search` tìm thông tin các địa điểm, nhưng dù Sydney không có trong mock database, agent vẫn tự tạo thông tin. 
- **Root Cause**: Ở Agent v1, do prompt trước đó chưa có constraint và hướng dẫn đầy đủ về việc parse các tiêu chí tìm kiếm và thiếu description của tool, dẫn đến việc gọi sai tool, ảo tool, dẫn đến hallucination.
- **Fix (Hướng khắc phục)**: Nhóm đã cập nhật System Prompt để parse các filter param chính xác hơn, cập nhật description để agent không gọi tool sai luồng.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Có dùng Calculator vs Không dùng Calculator
- **Diff**: Ban đầu nhóm thả cho LLM tự nhẩm tính tổng chi phí (Không dùng tool `calculator`).
- **Result**: Tỉ lệ cộng sai tiền (hallucination trong toán học) lên tới 40% trên các Trip lớn trên 3 ngày. Sau khi bắt buộc sử dụng Tool `calculator`, độ chính xác tổng ngân sách đạt 100%.

### Experiment 2: Chatbot vs Agent
| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Simple Q ("What to eat in DN?") | Tốt, văn phong hay | Tốt | Draw |
| Multi-step ("Trip under $200") | Tự bịa ra giá, cộng sai ngân sách | Tìm giá thực, cộng đúng tiền nhờ Calculator | **Agent** |

---

## 6. Production Readiness Review

- **Data Parsing**: Data Parsing / Chuẩn hóa dữ liệu đầu vào: Kết quả trả về từ search (Search Engine API) hiện còn khá lộn xộn, thường chứa HTML thừa, ký tự nhiễu, đoạn text lặp, tiêu đề không cần thiết, hoặc nội dung không trực tiếp phục vụ cho bước lập kế hoạch. Nếu đưa lên môi trường Production, hệ thống nên có một lớp tiền xử lý riêng để làm sạch và chuẩn hóa dữ liệu trước khi đưa vào Observation. Lớp này có thể gồm các bước như loại bỏ HTML tags, cắt bỏ boilerplate text, chuẩn hóa encoding, rút gọn đoạn văn, và chỉ giữ lại các trường quan trọng như tên địa điểm, giá, thời lượng, khu vực, và ghi chú chính. Việc này không chỉ giúp đầu ra rõ ràng hơn mà còn giảm đáng kể số token phải đưa vào context, từ đó tiết kiệm chi phí và giảm nguy cơ agent bị nhiễu khi suy luận.
- **Tốc độ (Latency)**: Một điểm yếu rõ ràng của hệ thống hiện tại là lượng dữ liệu hạn chế, đặc biệt khi agent phải gọi tool liên tiếp để thu thập thông tin như khách sạn, phương tiện di chuyển, địa điểm tham quan. Những dữ liệu này cần được gọi qua API để thu thập được thông tin chính xác từ các nguồn tin cậy. 
- **Quan sát và giám sát hệ thống (Observability)**: Bản agent hiện đã có log, nhưng để dùng thực tế thì cần nâng cấp phần theo dõi vận hành. Mỗi phiên chạy nên được ghi lại rõ ràng theo các bước như LLM_RESPONSE, TOOL_EXECUTION, TOOL_SUCCESS, TOOL_ERROR, ANALYZE, và FINAL_ANSWER. Điều này giúp dễ debug, dễ đo reliability giữa các phiên bản agent, và cũng hỗ trợ đánh giá các lỗi như parser error, hallucination, hoặc timeout. Trong Production, các log này nên được chuẩn hóa và có thể đẩy lên dashboard hoặc hệ thống monitoring.
- **Chi phí token và context management**: Một rủi ro khác khi mở rộng hệ thống là số lượng token tăng rất nhanh nếu giữ toàn bộ observation thô, logs, và dữ liệu tìm kiếm trong cùng một vòng lặp. Khi agent phải xử lý nhiều địa điểm hoặc nhiều danh mục cùng lúc, context có thể phình to và làm tăng chi phí suy luận. Vì vậy, ngoài lớp làm sạch dữ liệu, nên có cơ chế tóm tắt observation theo từng bước, chỉ giữ lại các trường thật sự cần cho quyết định cuối cùng.

---

## 7. Group Insights / Bài học của nhóm

1. **Prompt tốt không chỉ là hướng dẫn, mà là cơ chế kiểm soát hành vi của agent.** Nhóm nhận ra rằng chỉ cần mô tả nhiệm vụ chung chung thì agent rất dễ trả lời sai format, gọi tool không đúng tham số, hoặc bỏ qua các bước cần thiết. Prompt hiệu quả phải đóng vai trò như một “quy trình vận hành”, quy định rõ thứ tự hành động, format output, và điều kiện để chuyển sang bước tiếp theo.

2. **Tool design ảnh hưởng trực tiếp đến chất lượng suy luận.** Agent không chỉ phụ thuộc vào LLM mà còn phụ thuộc mạnh vào cách thiết kế tool. Nếu tool có input mơ hồ, output thiếu trường quan trọng, hoặc đơn vị dữ liệu không nhất quán, agent sẽ dễ đưa ra kế hoạch sai hoặc tính budget sai. Chuẩn hóa schema của tool quan trọng không kém việc tinh chỉnh prompt.

3. **Không phải mọi lỗi đều là lỗi mô hình.** Ban đầu nhóm có xu hướng nghĩ sai sót chủ yếu do LLM “hallucinate”, nhưng sau khi debug kỹ hơn, nhiều lỗi thực tế đến từ parser, mapping tool, unit mismatch, hoặc logic vòng lặp — cần nhìn hệ thống như một pipeline hoàn chỉnh.

4. **So sánh chatbot và agent làm rõ trade-off.** Chatbot thường trả lời nhanh hơn; agent dùng dữ liệu có cấu trúc, kiểm tra budget, và lịch trình cụ thể hơn, nhưng phức tạp hơn về debugging, latency và xử lý lỗi.