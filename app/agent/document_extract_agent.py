from pydantic_ai import Agent, RunContext
from app.agent.models import LLMModel
from app.document.dto import DocumentData
from app.agent.prompts import agent_prompts

document_extract_agent = Agent[str, DocumentData](
    name="document_extract_agent",
    model=LLMModel.openai,
    deps_type=str,
    output_type=DocumentData,
    system_prompt=agent_prompts["document_extract_agent"]["system_prompt"],
    instructions=agent_prompts["document_extract_agent"]["instructions"],
)


@document_extract_agent.tool
def resume_content(ctx: RunContext[str]) -> str:
    """ Resume content in text format """
    return f"Resume content: {ctx.deps}"
