# src/tools/search_tool.py

from typing import Dict, Any, List
from src.data.mock import MOCK_TRAVEL_DATA


SEARCH_TOOL_SPEC = {
    "name": "search_travel_data",
    "description": (
        "Searches structured travel data for a given city and category. "
        "Use this tool to find attractions, food, hotels, or transport options with estimated costs. "
        "Input: city (string), category (string), max_results (int, optional), query (string, optional). "
        "Returns a JSON object containing a list of items, each with name, type, estimated_cost, duration_hours, and notes."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string"},
            "category": {"type": "string"},
            "max_results": {"type": "integer", "default": 5},
            "query": {"type": "string"}
        },
        "required": ["city", "category"]
    }
}


def search_travel_data(
    city: str,
    category: str,
    max_results: int = 5,
    query: str = ""
) -> Dict[str, Any]:
    """
    Search travel data by city and category.

    Args:
        city (str): City name (e.g., "Da Nang")
        category (str): One of ["attractions", "food", "hotels", "transport"]
        max_results (int): Max number of results (default 5)
        query (str): Optional keyword filter

    Returns:
        Dict with keys: city, category, count, results[]
    """
    city_key = city.strip().lower()
    category_key = category.strip().lower()

    city_data = MOCK_TRAVEL_DATA.get(city_key, {})
    results = city_data.get(category_key, [])

    if query:
        q = query.lower()
        filtered = []
        for item in results:
            text = f"{item['name']} {item['notes']} {item['type']}".lower()
            if q in text:
                filtered.append(item)
        results = filtered

    # Ensure the return format matches the expected structure
    return {
        "city": city,
        "category": category,
        "count": len(results[:max_results]),
        "results": [
            {
                "name": item.get("name"),
                "type": item.get("type"),
                "estimated_cost": item.get("estimated_cost_usd"),  # Map cost field
                "duration_hours": item.get("duration_hours"),
                "notes": item.get("notes")
            }
            for item in results[:max_results]
        ]
    }