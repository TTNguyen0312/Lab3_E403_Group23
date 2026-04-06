# src/tools/registry.py

from src.tools.search_tool import SEARCH_TOOL_SPEC, search_travel_data
from src.tools.calculator_tool import CALCULATOR_TOOL_SPEC, calculate_trip_budget


TOOLS = [
    {
        "spec": SEARCH_TOOL_SPEC,
        "function": search_travel_data
    },
    {
        "spec": CALCULATOR_TOOL_SPEC,
        "function": calculate_trip_budget
    }
]


def get_tool_specs():
    return [tool["spec"] for tool in TOOLS]


def get_tool_map():
    return {tool["spec"]["name"]: tool["function"] for tool in TOOLS}