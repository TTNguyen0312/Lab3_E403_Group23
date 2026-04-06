# src/tools/calculator_tool.py

from typing import Dict, Any, List


CALCULATOR_TOOL_SPEC = {
    "name": "calculate_trip_budget",
    "description": (
        "Calculates the total trip cost and checks whether the plan fits within the user's budget. "
        "Use this tool after collecting cost items from travel search results. "
        "Input: items (list of objects with estimated_cost), budget (float), days (int), travelers (int). "
        "Returns subtotal, total, remaining budget, and within_budget."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "items": {"type": "array"},
            "budget": {"type": "number"},
            "days": {"type": "integer", "default": 1},
            "travelers": {"type": "integer", "default": 1}
        },
        "required": ["items", "budget"]
    }
}


def calculate_trip_budget(
    items: List[Dict[str, Any]],
    budget: float,
    days: int = 1,
    travelers: int = 1
) -> Dict[str, Any]:
    """
    Calculate total trip cost.

    Args:
        items: List of items (must contain estimated_cost)
        budget: Total budget
        days: Number of days
        travelers: Number of travelers

    Returns:
        subtotal, total, remaining, within_budget
    """

    if not isinstance(items, list):
        raise ValueError("items must be a list")

    subtotal = 0.0

    for item in items:
        try:
            cost = float(item.get("estimated_cost", 0))
            subtotal += cost
        except Exception:
            continue  # ignore bad items

    total = subtotal * max(travelers, 1)
    remaining = float(budget) - total

    return {
        "subtotal": round(subtotal, 2),
        "total": round(total, 2),
        "budget": round(float(budget), 2),
        "remaining": round(remaining, 2),
        "within_budget": remaining >= 0
    }