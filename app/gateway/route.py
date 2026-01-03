import asyncio
from asyncio import Queue
from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from app.gateway.dto import ProcessInputDto
from app.gateway.service import GatewayService
from app.lib.annotations import AuthSession, TransactionSession

router = APIRouter(tags=['Gateway'])


@router.post('/process-input-data', operation_id='processInputData')
async def process_input_data(
        session: TransactionSession,
        user_session: AuthSession,
        template_name: str = Form(...),
        job_description: str = Form(...),
        file: UploadFile = File(...)):
    queue = Queue(maxsize=10)
    gateway_service = GatewayService(session, queue)
    data = ProcessInputDto(template_name=template_name, job_description=job_description)
    task = asyncio.create_task(gateway_service.process_input_data(file, data, user_session.user, user_session.session))
    stream_headers = {"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    return StreamingResponse(gateway_service._process_stream(task), media_type='text/event-stream', headers=stream_headers)
