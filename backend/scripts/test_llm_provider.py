"""
Smoke test for the LLM provider abstraction — confirms we can actually
get a response from the configured provider (Gemini, by default).

Run from backend/ with venv active:
    python -m scripts.test_llm_provider
"""

from app.agents.llm_provider import get_llm


def main() -> None:
    print(f"Testing LLM provider call...")
    llm = get_llm(purpose="fast")

    response = llm.invoke("Reply with exactly one sentence confirming you received this message.")

    print(f"\nResponse: {response.content}")
    print("\n✅ LLM PROVIDER TEST PASSED")


if __name__ == "__main__":
    main()