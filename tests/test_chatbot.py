import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot import run_chatbot
from src.telemetry.logger import logger


TEST_CASES = [
    "Plan a 2-day trip to Da Nang under $200",
    "Plan a 3-day trip to Hoi An for a couple with a budget of $300",
    "Suggest a 1-day food itinerary in Ho Chi Minh City under $40",
    "Plan a family-friendly 2-day trip to Da Lat with light sightseeing and local food",
    "Explain recursion in simple terms with one example.",
]


def run_chatbot_demo() -> None:
    print("--- Chatbot Demo ---")

    for index, prompt in enumerate(TEST_CASES, start=1):
        print(f"\n=== Test Case {index} ===")
        print(f"User: {prompt}")

        try:
            response = run_chatbot(prompt)
            print("Assistant:")
            print(response["content"])
            print(
                f"\n[provider={response['provider']} latency_ms={response['latency_ms']} "
                f"total_tokens={response['usage'].get('total_tokens', 0)}]"
            )
        except Exception as exc:
            logger.log_event("CHATBOT_ERROR", {"prompt": prompt, "error": str(exc)})
            print(f"Error while running chatbot baseline: {exc}")


if __name__ == "__main__":
    run_chatbot_demo()
