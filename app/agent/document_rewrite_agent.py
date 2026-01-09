import json
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
    """ Latest resume details in text format """
    data = ctx.deps.session_state.generated_document_data
    if not data: return "No latest resume details found"
    return f"Latest resume details: {json.dumps(data)}"


@document_rewrite_agent.tool
def job_requirement(ctx: RunContext[DocumentDependency]) -> str:
    """ Job requirement in text format """
    description = ctx.deps.session_state.job_description
    if not description: return "No job requirement found"
    return f"Job requirement: {description}"


@document_rewrite_agent.tool
def original_resume_content(ctx: RunContext[DocumentDependency]) -> str:
    """ Original resume content in text format """
    content = ctx.deps.session_state.document_parsed
    if not content: return "No original resume content found"
    return f"Original resume content: {content}"
