import asyncio
import json
import logging
from uuid import UUID
from asyncio import Queue, Task
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Session, User
from app.document.dto import DocumentData, UploadDocumentResult
from app.document.service import DocumentService
from app.gateway.dto import EventStatus, ProcessInputDto, EventResponse
from app.gateway.emitter import ProgressEmitter
from app.session_state.dto import SessionStateDto
from app.session_state.service import SessionStateService


class GatewayService:
    logger = logging.getLogger(__name__)

    def __init__(self, session: AsyncSession, queue: Queue):
        self.queue = queue
        self.session = session
        self.emitter = ProgressEmitter(queue)
        self.document_service = DocumentService(session)
        self.session_state_service = SessionStateService(session)

    def _get_session_state_dto(self, upload_result: UploadDocumentResult, parsed_content: str, extracted_data: DocumentData, data: ProcessInputDto, session: Session) -> SessionStateDto:
        return SessionStateDto(
            session_id=session.id,
            document_name=upload_result.filename,
            document_url=upload_result.file_url,
            document_parsed=parsed_content,
            document_data=extracted_data,
            job_description=data.job_description,
        )

    async def _process_stream(self, task: Task):
        while True:
            try:
                message = await asyncio.wait_for(self.queue.get(), timeout=60.0)
                if message is None: break
                if isinstance(message, EventResponse): message_json = message.model_dump_json()
                else: message_json = json.dumps(message)
                yield f"data: {message_json}\n\n"
            except asyncio.TimeoutError:
                self.logger.warning("Queue timeout, ending stream")
                if not task.done(): task.cancel()
                break
            except asyncio.CancelledError:
                self.logger.info("Stream cancelled by client")
                if not task.done(): task.cancel()
                break
            except Exception as e:
                self.logger.error(f"Error in stream: {str(e)}")
                if not task.done(): task.cancel()
                yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
                break

    async def upload(self, file: UploadFile, user_id: UUID):
        await file.seek(0)
        await self.emitter.emit(EventStatus.uploading)
        return await self.document_service.upload_document(file, user_id)

    async def save(self, data: SessionStateDto):
        await self.emitter.emit(EventStatus.saving)
        return await self.session_state_service.create_or_update_session_state(data)

    async def parse(self, file: UploadFile):
        await file.seek(0)
        await self.emitter.emit(EventStatus.parsing)
        return await self.document_service.parse_document(file)

    async def extract(self, parsed_content: str):
        await self.emitter.emit(EventStatus.extracting)
        return await self.document_service.extract_document(parsed_content)

    async def process_input_data(self, file: UploadFile, data: ProcessInputDto, user: User, session: Session):
        try:
            upload_result = await self.upload(file, user.id)
            parsed_content = await self.parse(file)
            extracted_data = await self.extract(parsed_content)
            session_state_dto = self._get_session_state_dto(upload_result, parsed_content, extracted_data, data, session)
            await self.save(session_state_dto)
            await self.emitter.emit(EventStatus.success)
        except Exception as e:
            self.logger.error(f"Error processing input data: {str(e)}")
            await self.emitter.emit(EventStatus.failed, {"error": str(e)})
        finally:
            await self.emitter.close()
