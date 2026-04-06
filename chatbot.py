from typing import Dict, Any, Optional

from src.core.llm_provider import LLMProvider
from src.core.provider_factory import create_provider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


SYSTEM_PROMPT = (
    "You are a helpful travel planning assistant. "
    "Help users create practical itineraries, suggest places to visit, food, transport, "
    "and budget-friendly options. "
    "When relevant, organize the answer by day, estimate costs in USD, "
    "highlight assumptions clearly, and keep the plan realistic and concise. "
    "If the request clearly needs external tools, strict budget validation, or multi-step action planning, "
    "do not invent a full answer. Say it should be handled by the ReAct agent."
)


def build_chatbot_system_prompt() -> str:
    return SYSTEM_PROMPT


def _needs_agent_or_tools(prompt: str) -> bool:
    normalized_prompt = prompt.lower()
    high_risk_patterns = [
        "plan a ",
        "itinerary",
        "under $",
        "budget",
        "compare",
        "cheapest",
        "calculate",
        "total cost",
        "step by step",
        "find the best",
    ]
    return any(pattern in normalized_prompt for pattern in high_risk_patterns)


def _build_agent_handoff_response(prompt: str) -> Dict[str, Any]:
    return {
        "content": (
            "This request looks like it needs tools or a ReAct agent for grounded planning, "
            "budget checking, or multi-step reasoning. Please use the agent pipeline instead "
            "of the baseline chatbot for this prompt."
        ),
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "latency_ms": 0,
        "provider": "baseline_guardrail",
        "mode": "agent_handoff",
        "original_prompt": prompt,
    }


def run_chatbot(
    prompt: str,
    provider: Optional[LLMProvider] = None,
    system_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    if _needs_agent_or_tools(prompt):
        result = _build_agent_handoff_response(prompt)
        logger.log_event(
            "CHATBOT_GUARDRAIL",
            {
                "prompt": prompt,
                "reason": "requires_agent_or_tools",
                "mode": result["mode"],
            },
        )
        return result

    llm = provider or create_provider("openai")
    prompt_to_use = system_prompt or build_chatbot_system_prompt()

    logger.log_event("CHATBOT_START", {"model": llm.model_name, "prompt": prompt})
    result = llm.generate(prompt, system_prompt=prompt_to_use)
    tracker.track_request(
        provider=result["provider"],
        model=llm.model_name,
        usage=result["usage"],
        latency_ms=result["latency_ms"],
    )
    logger.log_event(
        "CHATBOT_END",
        {
            "model": llm.model_name,
            "latency_ms": result["latency_ms"],
            "usage": result["usage"],
        },
    )
    return result
