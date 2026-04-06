# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Việt Quang
- **Student ID**: 2A202600243
- **Date**: 04/06/2026

---

## I. Technical Contribution (15 Points)

- **Modules Implemented**: `chatbot.py`, `tests/test_chatbot.py`
- **Code Highlights**:
	- `chatbot.py` implements the baseline chatbot entry point through `run_chatbot()` and the system prompt helper `build_chatbot_system_prompt()`.
	- It adds a guardrail in `_needs_agent_or_tools()` so the chatbot can detect requests that require live data, booking, or external verification.
	- It returns a structured handoff response from `_build_agent_handoff_response()` instead of producing a confident but unreliable answer.
	- It integrates telemetry with `logger.log_event()` and `tracker.track_request()` so chatbot runs can be compared fairly with the agent runs.
	- `tests/test_chatbot.py` runs the benchmark cases from `tests/chatbot_benchmark_data.py` and prints the response, latency, provider, and token usage for each case.
- **Documentation**: My contribution was focused on the chatbot baseline and its evaluation. I made sure the chatbot behaves as a clean comparison point for the ReAct agent: it answers normal travel questions directly, but it hands off when the request clearly needs tools or live information.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: The chatbot baseline could easily drift into answering requests that should have been handled by the ReAct agent, especially prompts that asked to search the web, verify availability, or check live prices.
- **Log Source**: The relevant events are written by `CHATBOT_GUARDRAIL` and `CHATBOT_START` / `CHATBOT_END` in the daily log files under `logs/`.
- **Diagnosis**: The failure was not in the agent loop itself. It was a baseline-design issue: without a guardrail, a plain chatbot can sound confident even when the request requires external data. That would weaken the evaluation because the baseline would be unfairly strong on tasks it should not solve directly.
- **Solution**: I added `_needs_agent_or_tools()` in `chatbot.py` and made it return a structured handoff response for live-data requests. This keeps the baseline honest, prevents hallucinated answers, and makes the comparison against the ReAct agent meaningful.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1.  **Reasoning**: The `Thought` block forces the agent to make its intermediate reasoning explicit before answering. Compared to a direct chatbot answer, this makes the agent more controllable because it can decide whether to search, estimate cost, or stop and answer with assumptions. For multi-step travel planning, that structure matters because the final answer depends on multiple sub-decisions.
2.  **Reliability**: The agent performed worse than the chatbot when it got stuck in formatting errors or repeated tool calls. In those cases, the chatbot could still give a decent direct answer, while the agent spent extra steps recovering from bad `Action:` output or looping on the same tool.
3.  **Observation**: Observations are the feedback loop of the agent. When the tool returned cost ranges, destination details, or a guardrail message, the next step became more grounded. That feedback is what lets the agent correct itself instead of continuing to guess.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Use an asynchronous queue for tool calls so multiple requests can be handled without blocking the whole agent pipeline.
- **Safety**: Add a supervisor layer that checks whether the agent is about to call the wrong tool or repeat the same action too many times.
- **Performance**: Use a lightweight retrieval layer or vector index to pick the right tool faster when the system grows to many tools.
