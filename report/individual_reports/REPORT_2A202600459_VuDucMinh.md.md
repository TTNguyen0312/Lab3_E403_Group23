# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Vũ Đức Minh
- **Student ID**: 2A202600459
- **Date**: 6th of April, 2026

---

## I. Technical Contribution (15 Points)

- **Modules Implementated**: 
  - `src/tools/search_tool.py`
  - `src/tools/calculator_tool.py`

- **Code Highlights**:
  - Xây dựng `search_tool` để truy vấn dữ liệu travel mock (địa điểm, chi phí, thời gian).
  - Tích hợp `calculator_tool` để tính tổng chi phí cho kế hoạch du lịch.
  - Thiết kế dữ liệu giả lập gồm ~100 data points cho Travel Planner.

- **Documentation**:
  - `search_tool` nhận input từ Agent (query về địa điểm/chi phí) → trả về danh sách kết quả phù hợp.
  - `calculator_tool` nhận input là các chi phí → tính tổng để kiểm tra budget.
  - Các tool được gọi trong vòng lặp ReAct thông qua:
    Thought → Action → Observation → Thought → Final Answer.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**:
  Agent bị lặp vô hạn với action:
  `Action: search(None)`

- **Log Source**:
  logs/2026-04-06.log:
  ```
  Thought: I should search for travel info
  Action: search(None)
  Observation: No results found
  ```

- **Diagnosis**:
  - LLM không hiểu rõ format input của tool.
  - Prompt chưa cung cấp ví dụ cụ thể về cách gọi tool.
  - Tool spec chưa rõ ràng về required parameters.

- **Solution**:
  - Cập nhật system prompt với ví dụ cụ thể:
    ```
    Action: search("Da Nang cost")
    ```
  - Thêm validation trong tool để tránh input None.
  - Ràng buộc format input rõ ràng hơn.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**:
   - Thought giúp Agent phân tích từng bước thay vì trả lời ngay.
   - Chatbot trả lời nhanh nhưng thiếu kiểm chứng.
   - ReAct cho phép "suy nghĩ + hành động" giống con người hơn.

2. **Reliability**:
   - Agent đôi khi tệ hơn chatbot khi:
     - Tool trả dữ liệu sai
     - Prompt không rõ ràng
   - Chatbot ổn định hơn trong câu hỏi đơn giản.

3. **Observation**:
   - Observation đóng vai trò cực kỳ quan trọng.
   - Nó giúp Agent điều chỉnh hành vi ở bước tiếp theo.
   - Nếu observation sai → toàn bộ reasoning sai theo.

---

## IV. Future Improvements (5 Points)

- **Scalability**:
  - Sử dụng queue bất đồng bộ cho tool calls.
  - Tách microservices cho từng tool.

- **Safety**:
  - Thêm lớp Supervisor Agent để kiểm tra hành động.
  - Giới hạn số lần gọi tool (tránh loop vô hạn).

- **Performance**:
  - Sử dụng Vector Database để tìm tool phù hợp.
  - Cache kết quả để giảm số lần gọi API.

---


