from src.tools.search_tool import search_travel_data
from src.tools.calculator_tool import calculate_trip_budget

attractions = search_travel_data("Da Nang", "attractions", 2)
print(attractions)

items = [
    {"name": "Budget Hotel", "estimated_cost": 50},
    {"name": "Food", "estimated_cost": 20},
    {"name": "Transport", "estimated_cost": 10}
]

result = calculate_trip_budget(items, budget=200, days=2, travelers=1)
print(result)