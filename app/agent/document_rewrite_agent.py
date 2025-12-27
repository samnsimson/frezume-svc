from pydantic_ai import Agent, RunContext
from app.agent.dto import DocumentDependency
from app.agent.models import LLMModel
from app.document.dto import DocumentDataOutput
from app.agent.prompts import agent_prompts

document_rewrite_agent = Agent[DocumentDependency, DocumentDataOutput](
    name="document_rewrite_agent",
    model=LLMModel.openai,
    deps_type=DocumentDependency,
    output_type=DocumentDataOutput,
    system_prompt=agent_prompts["document_rewrite_agent"]["system_prompt"],
    instructions=agent_prompts["document_rewrite_agent"]["instructions"],
)


@document_rewrite_agent.tool
def resume_details(ctx: RunContext[DocumentDependency]) -> str:
    """ Resume content in text format """
    return ctx.deps.resume_content


@document_rewrite_agent.tool
def job_requirement(ctx: RunContext[DocumentDependency]) -> str:
    """ Job requirement in text format """
    return ctx.deps.job_requirement
