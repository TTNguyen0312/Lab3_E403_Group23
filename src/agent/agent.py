import os
import re
import json
from typing import TypedDict, List

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from src.core.openai_provider import OpenAIProvider
from src.tools.registry import get_tool_map
from src.tools.search_tool import SEARCH_TOOL_SPEC
from src.tools.calculator_tool import CALCULATOR_TOOL_SPEC
from src.prompt.system_prompt import SYSTEM_PROMPT_TEMPLATE
from src.telemetry.logger import logger


# ======================
# 🔹 LOAD ENV
# ======================
load_dotenv()

model_name = os.getenv("DEFAULT_MODEL", "gpt-4o")
api_key = os.getenv("OPENAI_API_KEY")

llm = OpenAIProvider(model_name=model_name, api_key=api_key)

# ======================
# 🔹 TOOLS
# ======================
tool_map = get_tool_map()


def get_tool_descriptions():
    tools = [SEARCH_TOOL_SPEC, CALCULATOR_TOOL_SPEC]

    return "\n\n".join([
        f"{tool['name']}:\n"
        f"{tool['description']}\n"
        f"Parameters:\n{json.dumps(tool['parameters'], indent=2)}"
        for tool in tools
    ])


def get_system_prompt():
    return SYSTEM_PROMPT_TEMPLATE.format(
        tool_descriptions=get_tool_descriptions()
    )


# ======================
# 🔹 STATE
# ======================
class AgentState(TypedDict):
    input: str
    messages: List[str]
    last_response: str
    tool_name: str
    tool_args: str
    observation: str
    used_tools: List[str]
    steps: int


MAX_STEPS = 10


# ======================
# 🔹 NODE 1: LLM
# ======================
def llm_node(state: AgentState) -> AgentState:
    prompt = state["input"]

    if state["messages"]:
        prompt += "\n" + "\n".join(state["messages"])

    result = llm.generate(prompt, system_prompt=get_system_prompt())
    response_text = result["content"]

    logger.log_event("LLM_RESPONSE", {"response": response_text})

    state["last_response"] = response_text
    state["messages"].append(response_text)
    state["steps"] += 1

    return state


# ======================
# 🔹 NODE 2: PARSE
# ======================
def parse_node(state: AgentState) -> AgentState:
    text = state["last_response"]

    match = re.search(
        r"Action:\s*([\w_]+)\s*\((\{.*?\})\)",
        text,
        re.DOTALL
    )

    if match:
        state["tool_name"] = match.group(1)
        state["tool_args"] = match.group(2)
    else:
        state["tool_name"] = ""
        state["tool_args"] = ""

    return state


# ======================
# 🔹 NODE 3: TOOL
# ======================
def tool_node(state: AgentState) -> AgentState:
    tool_name = state["tool_name"]
    args_str = state["tool_args"]

    logger.log_event("TOOL_EXECUTION", {
        "tool_name": tool_name,
        "args": args_str
    })

    if tool_name not in tool_map:
        state["observation"] = f"Error: Tool {tool_name} not found"
        state["messages"].append(f"Observation: {state['observation']}")
        return state

    # ✅ Safe JSON parsing
    try:
        parsed_args = json.loads(args_str) if isinstance(args_str, str) else args_str
    except Exception:
        state["observation"] = "Error: Invalid JSON format"
        state["messages"].append(f"Observation: {state['observation']}")
        return state

    try:
        if not isinstance(parsed_args, dict):
            raise ValueError("Tool arguments must be a dictionary")

        result = tool_map[tool_name](**parsed_args)

        # Ensure the result is returned in a structured format
        if isinstance(result, dict):
            state["observation"] = json.dumps(result, indent=2)
        else:
            state["observation"] = str(result)

        state["used_tools"].append(tool_name)

        logger.log_event("TOOL_SUCCESS", {
            "tool": tool_name,
            "args": parsed_args,
            "result": result
        })

    except Exception as e:
        state["observation"] = f"Error: {str(e)}"
        logger.log_event("TOOL_ERROR", {
            "tool": tool_name,
            "error": str(e)
        })

    # ✅ Better feedback loop
    state["messages"].append(
        f"Observation: {state['observation']}\n"
        "Use this information to continue reasoning."
    )

    return state


# ======================
# 🔹 ROUTER
# ======================
def should_continue(state: AgentState) -> str:
    if state["steps"] > MAX_STEPS:
        return "end"

    # If tool failed → let LLM fix it
    if "Error:" in state["observation"]:
        return "llm"

    # If tool detected → execute
    if state["tool_name"]:
        return "tool"

    # Final Answer → END
    if "Final Answer:" in state["last_response"]:
        return "end"

    return "llm"


# ======================
# 🔹 GRAPH
# ======================
graph = StateGraph(AgentState)

graph.add_node("llm", llm_node)
graph.add_node("parse", parse_node)
graph.add_node("tool", tool_node)

graph.set_entry_point("llm")

graph.add_edge("llm", "parse")

graph.add_conditional_edges(
    "parse",
    should_continue,
    {
        "tool": "tool",
        "llm": "llm",
        "end": END
    }
)

graph.add_edge("tool", "llm")

app = graph.compile()


# ======================
# 🔹 RUN
# ======================
if __name__ == "__main__":
    print("🌍 Travel Planning Agent (LangGraph)")
    print("-----------------------------------")

    while True:
        user_input = input("\nEnter your query (or type 'exit'): ")

        if user_input.lower() == "exit":
            print("Goodbye 👋")
            break

        state: AgentState = {
            "input": user_input,
            "messages": [],
            "last_response": "",
            "tool_name": "",
            "tool_args": "",
            "observation": "",
            "used_tools": [],
            "steps": 0,
        }

        result = app.invoke(state)

        print("\n✅ FINAL ANSWER:")
        print(result["last_response"])

        print("\n🛠 Tools used:", result["used_tools"])
        print("-----------------------------------")