from typing import Literal
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter
from llama_cloud import ExtractConfig, ExtractMode
from llama_cloud_services import ExtractionAgent, LlamaExtract
from app.config import settings
from app.document.dto import DocumentData


def get_llama_extract_client() -> ExtractionAgent:
    agent_name = "resume-parser"
    config = ExtractConfig(extraction_mode=ExtractMode.FAST)
    extractor = LlamaExtract(api_key=settings.llama_cloud_api_key)
    agent = extractor.get_agent(name=agent_name)
    if agent is None: return extractor.create_agent(name=agent_name, config=config, template=DocumentData)
    return agent


class AIClients:
    @staticmethod
    def get_client(client_name: Literal['converter', 'extractor']) -> DocumentConverter | ExtractionAgent:
        if client_name == 'converter': return DocumentConverter()
        if client_name == 'extractor': return get_llama_extract_client()
