# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: [29]
- **Team Members**: [Nguyễn Thị Ngọc, Nguyễn Trọng Tiến, Vũ Đức Minh, Nguyễn Việt Quang]
- **Deployment Date**: [2026-04-06]

---

## 1. Executive Summary

Trọng tâm của đội là xây dựng một **Travel Planner Agent** có khả năng tự động lên lịch trình du lịch dựa trên ngân sách (Ví dụ: *"Plan a 2-day trip to Da Nang under $200"*). Agent sử dụng công cụ tìm kiếm để tra cứu địa điểm/giá cả và máy tính để cộng dồn chi phí.

- **Success Rate**: Đạt 80% (16/20 test cases thành công) trên bộ dữ liệu kiểm thử.
- **Key Outcome**: Agent khắc phục được bài toán lớn nhất của Chatbot thuần là tình trạng "ảo giác dữ liệu". Nhờ có vòng lặp ReAct kết hợp tool `search` và `calculator`, hệ thống đưa ra lịch trình có chi phí sát thực tế và luôn tuân thủ nghiêm ngặt ngân sách cho phép.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation
```mermaid
graph TD
    A([Nhận yêu cầu: Địa điểm, Ngày, Budget]) --> B{LLM Brain\n(Phân tích & Ra quyết định)}
    
    %% Vòng lặp với Search
    B -->|Action: Gọi Search Tool| C[Công cụ: Search API]
    C -->|Observation: Trả về Giá thực tế/Ước lượng| B
    
    %% Vòng lặp với Calculator
    B -->|Action: Gọi Calculator| D[Công cụ: Calculator]
    D -->|Observation: Trả về Tổng chi phí| B
    
    %% Logic suy luận (Thought)
    B --> E{LLM Reasoning:\nTổng chi phí <= Budget?}
    E -->|No: Tối ưu lại chi phí| B
    E -->|Yes: Tạo lịch trình| F([Final Answer: Trả về Lịch trình hoàn thiện])
    
    %% Cơ chế chống vòng lặp vô hạn (Guardrail)
    B -. Kiểm tra .-> G((Guardrail:\nLoops > max_steps?))
    G -. Vượt quá số lần lặp .-> H([Fallback: Báo cáo ngân sách bất khả thi])
    
    classDef brain fill:#f9d0c4,stroke:#333,stroke-width:2px;
    classDef tool fill:#d4e6f1,stroke:#333,stroke-width:2px;
    classDef io fill:#e8f8f5,stroke:#333,stroke-width:2px;
    classDef guard fill:#fef9e7,stroke:#333,stroke-dasharray: 5 5;
    
    class B,E brain;
    class C,D tool;
    class A,F io;
    class G,H guard;
```


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

### 2.3 LLM Providers Used
- **Primary**: OpenAI GPT-4o (hoặc Gemini 1.5 Pro) để có khả năng reasoning tốt phần toán học.
- **Secondary (Backup)**: Llama 3 / Phi-3 (Local) dùng làm fallback.

---

## 3. Telemetry & Performance Dashboard

- **Average Latency (P50)**: 4500ms (Trễ hơn Chatbot vì phải trải qua 4-5 bước Loop bao gồm cả gọi web search).
- **Max Latency (P99)**: 8200ms.
- **Average Tokens per Task**: 1250 tokens / query (Do Observation từ Search API quá dài).
- **Total Cost of Test Suite**: ~$0.08 cho toàn bộ 20 Test Cases (Tối ưu được chi phí nhờ dùng mô hình LLM nội bộ nhẹ nhàng ở các bước định tuyến).

---

## 4. Root Cause Analysis (RCA) - Failure Traces

*Phân tích điểm yếu (Weakness) mang tính đặc thù của team: "Less strict correctness" (Không cần đúng tuyệt đối 100%).*

### Case Study: Lỗi quá khắt khe với dữ liệu tìm kiếm
- **Input**: *"Plan trip to Da Nang under $200."*
- **Observation**: Agent gọi `search` tìm giá vé tham quan Bà Nà Hills, API trả ra text thông tin chung chung không có giá tiền rực tiếp (ví dụ: "Bà Nà Hills is great... ticket prices vary"). 
- **Root Cause**: Ở Agent v1, hệ thống cố gắng tìm *giá chính xác đến từng xu*. Khi không tìm thấy giá chính xác, vòng lặp ReAct bị fail hoặc gọi `search` lặp lại chục lần.
- **Fix (Hướng khắc phục)**: Nhóm đã cập nhật System Prompt để tận dụng điểm yếu (vốn dĩ là đặc thù) của bài toán hoạch định: *"Nếu công cụ tìm kiếm không trả về giá chính xác tuyệt đối, hãy ước lượng một mức giá phổ biến nhất dựa trên ngữ cảnh để tiếp tục tính toán, không cần chính xác 100% (Less strict correctness)."* Điều này giúp chu trình trơn tru hơn rất nhiều.

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

- **Data Parsing**: Kết quả từ `search` (Search Engine API) rất lộn xộn. Khi đưa lên Production, cần có 1 lớp làm sạch HTML/Text thừa trước khi đưa vào Observation để tiết kiệm Token.
- **Tốc độ (Latency)**: Điểm yếu là tốc độ chậm. Cần đưa thêm cơ chế hiển thị dạng "Thinking..." (Streaming logs) trên UI để giữ chân người dùng trong lúc chờ Agent thu thập giá cả phòng/vé.

---

## 7. Group Insights / Bài học của nhóm

**1. Tính linh hoạt trong độ chính xác (Less strict correctness):**
Với domain "Travel Planner", việc đòi hỏi chi phí phải chính xác tới từng cent là bất khả thi và dễ làm Agent sập (Infinite Loop). Bài học của nhóm là cấu hình System Prompt sao cho Agent biết cách "ước lượng" (Estimate) linh hoạt khi thông tin trả về thiếu hụt. Đây chính là nghệ thuật cân bằng giữa cấu trúc chặt chẽ (ReAct) và khả năng suy luận linh hoạt.

**2. LLM rất kém toán học (Tính toán ngân sách):**
Dù thông minh đến mấy, nếu không có tool `calculator`, LLM vẫn trừ sai tiền ngân sách cơ bản. Bài học là: Bất cứ thứ gì dính tới số liệu mang tính quyết định, bắt buộc phải biến nó thành Action gọi Tool bên ngoài.

**3. Khủng hoảng vòng lặp vô hạn (Infinite Loop) vì cố chấp:**
Khi ngân sách là $10 (quá vô lý cho 1 chuyến đi), Agent tự động thay đổi địa điểm và gọi `search` liên tục hàng chục lần nhằm cố tìm "cho bằng được" lịch trình thỏa mãn $10. Việc này ngốn vô số API Token. Để giải quyết, nhóm phải giới hạn `max_steps = 5` và hướng dẫn Agent trả lời ngay: *"Ngân sách này không khả thi"* thay vì tìm kiếm mù quáng.
