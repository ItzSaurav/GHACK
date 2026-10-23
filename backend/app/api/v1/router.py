"""FastAPI Router for V1 API endpoints."""

import resource
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Query, Response, UploadFile, status
from pydantic import BaseModel, Field

from backend.app.conversation.dialogue import dialogue_manager
from backend.app.conversation.indian_accent_llm import indian_accent_llm
from backend.app.conversation.session import MessageRecord, session_store
from backend.app.core.logging import logger
from backend.app.forms.assistance import (
    FormPreview,
    FormSubmissionReceipt,
    FormSubmissionRequest,
    form_service,
)
from backend.app.schemes.catalogue import catalogue
from backend.app.schemes.engine import check_scheme_eligibility
from backend.app.schemes.models import SchemeDefinition
from backend.app.voice.adapters import TranscriptionResult, asr_adapter, synthesize_speech_edge_tts

router = APIRouter()


class HealthCheckResponse(BaseModel):
    status: str
    version: str
    schemes_count: int
    adapters: dict[str, str]
    system_memory_rss_mb: float
    max_upload_size_mb: int = 5


class StartConversationRequest(BaseModel):
    language: str = Field(default="hi", pattern="^(en|kn|hi|gu|ta|te|ur|or|mr|ml)$")


class StartConversationResponse(BaseModel):
    session_id: str
    language: str
    greeting: str
    current_question_key: str
    options: list[str]


class SendMessageRequest(BaseModel):
    session_id: str
    text: str = Field(default="", max_length=500)
    source: str = Field(default="text", pattern="^(text|voice)$")
    audio_confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class SendMessageResponse(BaseModel):
    session_id: str
    reply: str
    current_question_key: str | None
    options: list[str]
    facts: dict[str, Any]
    evaluation: list[dict[str, Any]]
    is_completed: bool
    tool_eligibility: dict[str, Any] | None = None
    detected_language: str | None = None
    open_form_scheme_id: str | None = None


class FormPreviewRequest(BaseModel):
    session_id: str
    scheme_id: str


@router.get("/health", response_model=HealthCheckResponse)
def get_health() -> HealthCheckResponse:
    # Measure resident memory (RSS) in MB using standard OS resource API
    usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    usage_mb = round(usage_kb / 1024.0, 2)

    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        schemes_count=catalogue.count(),
        adapters={
            "asr": asr_adapter.name,
            "browser_speech_bridge": "supported",
            "eligibility_engine": "deterministic_v1",
        },
        system_memory_rss_mb=usage_mb,
        max_upload_size_mb=5,
    )


@router.get("/schemes", response_model=list[SchemeDefinition])
def list_schemes() -> list[SchemeDefinition]:
    return catalogue.get_all()


@router.get("/schemes/{scheme_id}", response_model=SchemeDefinition)
def get_scheme(scheme_id: str) -> SchemeDefinition:
    scheme = catalogue.get_by_id(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{scheme_id}' was not found in the verified catalogue.",
        )
    return scheme


@router.post("/conversation/start", response_model=StartConversationResponse)
def start_conversation(req: StartConversationRequest) -> StartConversationResponse:
    sess = session_store.get_or_create(language=req.language)
    sess.current_question_key = "age"

    q = dialogue_manager.get_question("age", req.language)
    greeting = indian_accent_llm.format_greeting(req.language) + " " + q["text"]

    sess.messages.append(
        MessageRecord(role="assistant", text=greeting, language=req.language, source="system")
    )

    logger.info(f"Started new Seva Vaani conversation session: {sess.session_id} [lang={req.language}]")

    return StartConversationResponse(
        session_id=sess.session_id,
        language=req.language,
        greeting=greeting,
        current_question_key="age",
        options=q["options"],
    )


@router.post("/conversation/message", response_model=SendMessageResponse)
def send_message(req: SendMessageRequest) -> SendMessageResponse:
    sess = session_store.get(req.session_id)
    if not sess:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session expired or not found. Please start a new session.",
        )

    logger.info(f"Processing message for session: {sess.session_id} [source={req.source}]")
    result = dialogue_manager.process_message(
        session=sess,
        user_text=req.text,
        source=req.source,
        audio_confidence=req.audio_confidence,
    )

    return SendMessageResponse(
        session_id=sess.session_id,
        reply=result["reply"],
        current_question_key=result["current_question_key"],
        options=result["options"],
        facts=result["facts"],
        evaluation=result["evaluation"],
        is_completed=result["is_completed"],
        tool_eligibility=result.get("tool_eligibility"),
        detected_language=result.get("detected_language", sess.language),
        open_form_scheme_id=result.get("open_form_scheme_id"),
    )


@router.post("/schemes/check-eligibility")
def check_scheme_eligibility_endpoint(facts: dict[str, Any]) -> dict[str, Any]:
    """Structured tool endpoint to evaluate scheme eligibility against deterministic rules."""
    return check_scheme_eligibility(**facts)


@router.post("/conversation/voice")
async def process_voice(
    session_id: str = Form(...),
    language: str = Form("hi"),
    audio: UploadFile = File(...),  # noqa: B008
) -> dict[str, Any]:
    sess = session_store.get(session_id)
    if not sess:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired.",
        )

    # Read bounded audio bytes (max 5 MB)
    audio_bytes = await audio.read(5 * 1024 * 1024 + 1)
    if len(audio_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio upload exceeds maximum 5MB size limit.",
        )

    # Transcribe via ASR adapter
    transcription: TranscriptionResult = asr_adapter.transcribe(
        audio_bytes=audio_bytes,
        content_type=audio.content_type or "audio/wav",
        language=language,
    )

    if transcription.is_silent_or_low_energy or not transcription.text:
        return {
            "success": False,
            "transcription": transcription.model_dump(),
            "dialogue_response": None,
            "message": transcription.warning_message or "Low audio volume or silence detected. Please speak louder.",
        }

    # Automatically pass recognized transcript into dialogue manager
    dialogue_res = dialogue_manager.process_message(
        session=sess,
        user_text=transcription.text,
        source="voice",
        audio_confidence=transcription.confidence,
    )

    return {
        "success": True,
        "transcription": transcription.model_dump(),
        "dialogue_response": dialogue_res,
    }


@router.get("/voice/tts")
async def text_to_speech(
    text: str = Query(..., min_length=1, max_length=1000),
    language: str = Query("hi", pattern="^(en|kn|hi|gu|ta|te|ur|or|mr|ml)$"),
) -> Response:
    audio_bytes, media_type = await synthesize_speech_edge_tts(text=text, language=language)
    return Response(content=audio_bytes, media_type=media_type)



@router.post("/forms/preview", response_model=FormPreview)
def get_form_preview(req: FormPreviewRequest) -> FormPreview:
    sess = session_store.get(req.session_id)
    if not sess:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired.",
        )

    scheme = catalogue.get_by_id(req.scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{req.scheme_id}' does not exist.",
        )

    return form_service.generate_preview(
        scheme_id=scheme.id,
        scheme_name=scheme.name,
        facts=sess.facts,
        language=sess.language,
    )


@router.post("/forms/submit", response_model=FormSubmissionReceipt)
def submit_form(req: FormSubmissionRequest) -> FormSubmissionReceipt:
    try:
        receipt = form_service.submit_form(req)
        logger.info(f"Form submission recorded: tracking_id={receipt.tracking_id} scheme={req.scheme_id}")
        return receipt
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
