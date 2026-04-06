import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.chatbot import run_chatbot
from src.telemetry.logger import logger
from tests.chatbot_benchmark_data import CHATBOT_BENCHMARK_CASES


def run_chatbot_demo() -> None:
    print("--- Chatbot Demo ---")

    for index, case in enumerate(CHATBOT_BENCHMARK_CASES, start=1):
        prompt = case["prompt"]
        print(f"\n=== Test Case {index} ===")
        print(f"Case ID: {case['id']}")
        print(f"Category: {case['category']}")
        print(f"Difficulty: {case['difficulty']}")
        print(f"Expected Winner: {case['expected_winner']}")
        print(f"User: {prompt}")

        try:
            response = run_chatbot(prompt)
            print("Assistant:")
            print(response["content"])
            print(f"\nExpected signals: {', '.join(case['expected_signals'])}")
            print(
                f"\n[provider={response['provider']} mode={response.get('mode', 'standard')} latency_ms={response['latency_ms']} "
                f"total_tokens={response['usage'].get('total_tokens', 0)}]"
            )
        except Exception as exc:
            logger.log_event("CHATBOT_ERROR", {"prompt": prompt, "error": str(exc)})
            print(f"Error while running chatbot baseline: {exc}")


if __name__ == "__main__":
    run_chatbot_demo()
