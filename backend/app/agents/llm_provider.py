"""
LLM provider abstraction (Section 12).

Nothing else in the codebase should import ChatGoogleGenerativeAI,
ChatOpenAI, or ChatAnthropic directly — everything calls get_llm()
instead, so switching providers is a config change, not a code change.
"""

from langchain_core.language_models import BaseChatModel

from app.config import settings


def get_llm(purpose: str = "reasoning") -> BaseChatModel:
    """Returns a chat model for the given purpose: 'fast' or 'reasoning'.
    Which underlying provider/model is used is controlled entirely by
    LLM_PROVIDER and LLM_MODEL_* in .env — this function doesn't hard-code
    any provider-specific defaults (Section 13)."""

    model_name = settings.llm_model_fast if purpose == "fast" else settings.llm_model_reasoning

    if settings.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.gemini_api_key,
            temperature=0.2,
        )

    if settings.llm_provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_name,
            api_key=settings.openai_api_key,
            temperature=0.2,
        )

    if settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model_name,
            api_key=settings.anthropic_api_key,
            temperature=0.2,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider!r}")