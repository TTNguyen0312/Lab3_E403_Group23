# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Thị Ngọc 
- **Student ID**: 2A202600405
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

*Đóng góp cụ thể vào kiến trúc và tích hợp hệ thống của Travel Planner Agent.*

- **Backend & API Web Server (`app.py`)**: 
  - Trực tiếp đảm nhận thiết kế và xây dựng module Web App bằng framework Flask (`app.py`).
  - Gói mã nguồn AI lõi thành dịch vụ API. Đã xây dựng endpoint `/api/query` có khả năng bóc tách payload JSON từ Frontend và linh hoạt định tuyến (routing) lời gọi hàm đến `run_chatbot` hoặc `run_agent` dựa trên tham số `mode`. Điều này giúp hệ thống mô phỏng đúng môi trường Production UI và tạo điều kiện lý tưởng để nhóm thực hiện A/B testing hiệu năng trực quan.
- **Architecture & System Design (Flowchart/Mermaid)**: 
  - Chịu trách nhiệm kiến trúc hệ thống và trực quan hóa luồng tư duy ReAct (tham chiếu file đính kèm `travel planner agent_flowchart_23.png` do tôi khởi tạo).
  - Đã chuyển đổi lưu đồ đó thành mã Mermaid chuyên nghiệp nhúng trong báo cáo nhóm (Group Report). Sơ đồ đã bóc tách rõ ràng các thành phần phức tạp: Node LLM Brain xử lý Reasoning, Request/Response tới khối External Tools (Search, Calculator), và luồng Guardrail (giám sát số vòng lặp tối đa để tránh lỗi ngốn credit API).
- **Technical Writing & Performance Evaluation (Group Report)**:
  - Đảm nhận vai trò viết chính (Lead Writer) khởi tạo và hoàn thiện báo cáo chung của toàn đội (`GROUP_REPORT_29.md`).
  - Trực tiếp tổng hợp các số liệu Telemetry & Performance (Latency, Token cost) và thiết kế hệ thống thực nghiệm song song (Ablation Studies) để chứng minh tính hiệu quả vượt trội (và phân tích cả nhược điểm) của mô hình ReAct Agent so với Chatbot truyền thống.


---

## II. Debugging Case Study (10 Points)

*Phân tích lỗi (Failure event) thông qua hệ thống log và phương pháp khắc phục.*

- **Problem Description**: Hệ thống Agent bị kẹt vào vòng lặp vô hạn (Infinite Loop) kèm theo hành động rỗng: `Action: calculator(None)`.
- **Log Source / Traces**: Phân tích file lưu log trong `logs/2026-04-06.log`: Hệ thống báo cờ `LOG_EVENT: ERROR - json.decoder.JSONDecodeError`. Sau lỗi này, Agent lưu giữ (hallucinate) `Thought` sai cũ và lặp lại y hệt 5 vòng liên tiếp cho tới khi chương trình dừng.
- **Root Cause & Diagnosis**: 
  - Quá trình tra cứu Search API thường trả về dữ liệu rỗng hoặc không có số liệu tiền bạc cụ thể gây bối rối cho LLM. Nó sinh ra khối `Action` nhưng **quay cuồng và quên điền tham số (Argument)**.
  - Khi code Python nhận được chuỗi rỗng để phân tích JSON, chương trình quăng ngoại lệ vỡ hệ thống (Error Traceback) quá dài và vô hồn vào `Observation`, khiến LLM mất phương hướng.
- **Solution & Fixes**:
  1. **Prompt Guardrail**: Trực tiếp can thiệp lại *System Prompt*, cung cấp luật Few-shot mạnh mẽ hơn: *"Khi gọi tính toán, tham số bắt buộc là biểu thức string (VD: '100 + 50'). Tuyệt đối không để trống"*. 
  2. **Exception Handling**: Thêm khối `try...except` vào hệ thống ReAct execution. Thay vì để văng lỗi Python Crash sập chương trình, nếu `parse` sai, hệ thống gửi lại cho tác nhân một `Observation` thân thiện: *"Lệnh JSON gửi tới Tool sai định dạng, vui lòng suy nghĩ lại và truyền lại tham số chuẩn"*. Tối ưu hóa này giúp AI tự biết sửa lỗi của nó trong step tiếp theo.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Góc nhìn thực tiễn về sự khác biệt giữa mô hình Chatbot tĩnh và Agent động.*

1. **Reasoning (Khả năng suy luận & Phân rã tác vụ)**: 
   - Bài toán xếp đặt lịch trình bộc lộ điểm yếu của **Chatbot** thuần túy: Nó thích làm ngơ yêu cầu ngân sách nghiêm ngặt (Less strict correctness) và tự nhắm mắt ước lượng một chi phí ảo.
   - Ngược lại, **ReAct Agent** tỏa sáng với chuỗi *Reasoning (Thought block)*. Agent biết suy ngẫm mưu lược: *"Tôi cần tra giá vé máy bay trước. Nếu vé tốn $150, tôi chỉ còn dư $50 để ăn uống"*. Luồng ý nghĩ này là cốt lõi để tháo gỡ các bài toán đa biến logic phức tạp.
2. **Reliability & Hallucination Mitigation (Độ tin cậy)**: 
   - Đổi lại, khi đòi hỏi khả năng sáng tạo như một đoạn văn miêu tả tâm thế du lịch, **Chatbot** mang lại độ mượt mà tuyệt đối cùng độ trễ (latency) thấp nhờ tri thức nén khổng lồ. ReAct Agent thực tế lại *yếu thế hơn* và xử lý lề mề đi rõ ràng trong nhiệm vụ này, do thường loay hoay gọi external tools.
   - Nhưng khi dính tới số liệu mang tính tài chính, mô hình tự tạo Tool `calculator` và `search` chặn đứng hoàn toàn rủi ro **Hallucination** (Ảo giác), cải thiện độ tin cậy tiệm cận mức chính xác.
3. **Observation (Khả năng thấu hiểu môi trường thực)**: 
   - Đây là cái giúp AI nhận thức được thực tại. Ví dụ: Nếu nó tìm thử phòng resort và nhận về Output giá báo là $500/đêm, tác nhân tiếp nhận `Observation` đó và hiểu chi phí bị lố. Nó thiết lập luồng "quay xe" tự động điều hướng sang tìm loại phòng tập thể (Hostel). Nhờ thuộc tính này thay vì khư khư bám víu một ý định ban đầu, nó giống như một trợ lý tự giác đích thực.

---

## IV. Future Improvements (5 Points)

*Đề xuất kiến trúc để mở rộng cho một Production-Grade System.*

- **Scalability (Cải thiện TTFT bằng RAG)**: Nâng cấp module tìm kiếm (`search_tool`) bằng cấu trúc dữ liệu RAG (Retrieval-Augmented Generation) chạy trên Vector DB (VD: Chroma). Bằng cách cào (crawl) trước những điểm giá từ Agoda/Booking và lưu vào database, ta có thể giảm bớt sự phụ thuộc của Agent vào Live Google Search vốn đẩy Latency trễ rất dài.
- **Safety (Multi-Agent Supervisor)**: Bổ sung một luồng kiến trúc **Supervisor Agent** (Ai làm nhiệm vụ kiểm toán). Trước khi xuất *Final Answer* (Lịch trình sau cùng) cho khách hàng, Supervisor Agent đọc lại tổng thể chi phí và tiến hành tự cộng chéo. Nếu Agent chuyên viên điền sai ngân sách $200, Supervisor sẽ chặn luồng trả và buộc Agent đầu làm lại.
- **Performance (Kiến trúc đồ thị LangGraph)**: Thiết kế ReAct cũ bắt buộc phải chạy tuần tự (Sequential loop). Nhằm tiến đến Production với trải nghiệm tối ưu, chúng ta nên chuyển đổi sử dụng bộ khung **LangGraph**. Mạng luồng Graph cho phép khởi tạo tác vụ song song (Parallel execution) để tiến hành tìm giá vé máy bay và tra tiền khách sạn cùng một lúc ngay trong một step. Trải nghiệm hệ thống nhờ đó sẽ nhanh gấp đôi.
- **Telemetry UI**: Tích hợp nền tảng Monitor giao diện mở như *LangSmith* thay thế việc đọc thủ công các file `.log` JSON để dễ dàng minh họa Data-driven report.
