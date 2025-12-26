from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.nebius import NebiusProvider
from app.config import settings


class LLMModel:
    openai = OpenAIChatModel(
        settings.nebius_model,
        provider=NebiusProvider(api_key=settings.nebius_api_key),
    )
