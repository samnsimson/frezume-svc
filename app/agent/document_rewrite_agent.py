from pydantic_ai import Agent, RunContext
from app.agent.dto import DocumentDependency
from app.agent.models import LLMModel
from app.document.dto import DocumentDataOutput
from app.agent.prompts import document_system_prompt, document_instructions

document_rewrite_agent = Agent(
    name="document_rewrite_agent",
    model=LLMModel.openai,
    deps_type=DocumentDependency,
    output_type=DocumentDataOutput,
    system_prompt=document_system_prompt,
    instructions=document_instructions,
)


@document_rewrite_agent.tool
def resume_details(ctx: RunContext[DocumentDependency]) -> str:
    """ Resume content in text format """
    return ctx.deps.resume_content


@document_rewrite_agent.tool
def job_requirement(ctx: RunContext[DocumentDependency]) -> str:
    """ Job requirement in text format """
    return ctx.deps.job_requirement
