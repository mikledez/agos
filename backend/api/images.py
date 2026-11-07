from __future__ import annotations

from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import Response

from db import repository as repo
from services import humanization, image_service, storage

from .deps import get_current_user_id
from .schemas import (
    AnalyzeResponse,
    ChatExchangeOut,
    ChatMessageIn,
    ChatMessageOut,
    HumanizationIn,
    HumanizationOut,
    HumanizationUpdate,
    ImageDetail,
    ImageOut,
    ImageUpdate,
)
from .serializers import image_payload

router = APIRouter(tags=["images"])

def _owned_image(image_id: int, user_id: int) -> repo.Row:
    row = repo.get_image(image_id, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return row

def _active_image(image_id: int, user_id: int) -> repo.Row:
    row = _owned_image(image_id, user_id)
    repo.touch_image_activity(image_id, user_id)
    return row

def _image_file_response(contents: bytes | None, *, media_type: str, missing_detail: str) -> Response:
    if contents is None:
        raise HTTPException(status_code=404, detail=missing_detail)
    return Response(
        contents,
        media_type=media_type,
        headers={"Cache-Control": "private, max-age=3600"},
    )

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    file: UploadFile = File(...),
    phase: str = Form("toe_off"),
    direction: str = Form("ltr"),
    session_id: int | None = Form(None),
    user_id: int = Depends(get_current_user_id),
) -> dict:
    if session_id is not None and repo.get_session(session_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")

    contents = await file.read(image_service.MAX_UPLOAD_BYTES + 1)
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(contents) > image_service.MAX_UPLOAD_BYTES:
        megabytes = image_service.MAX_UPLOAD_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=413, detail=f"Image is larger than {megabytes} MB"
        )

    original_filename = Path((file.filename or "upload").replace("\\", "/")).name
    try:
        row, result, annotated = image_service.analyze_and_store(
            user_id,
            contents=contents,
            original_filename=original_filename,
            phase=phase,
            direction=direction,
            session_id=session_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "image_id": row["id"],
        "session_id": row["session_id"],
        "phase": phase,
        "direction": direction,
        "swing_leg": result["swing_leg"],
        "stance_leg": result["stance_leg"],
        "thigh_thigh_angle": result.get("thigh_thigh_angle"),
        "feedback": result["feedback"],
        "annotated_image": f"data:image/jpeg;base64,{annotated}",
        "original_url": f"/images/{row['id']}/file",
        "annotated_url": f"/images/{row['id']}/annotated",
    }

@router.get("/images", response_model=list[ImageOut])
def list_images(
    user_id: int = Depends(get_current_user_id),
    session_id: int | None = Query(default=None),
    root: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    if root and session_id is not None:
        raise HTTPException(
            status_code=400, detail="Use either root or session_id, not both"
        )
    if root:
        session_filter: object = None
    elif session_id is not None:
        if repo.get_session(session_id, user_id) is None:
            raise HTTPException(status_code=404, detail="Session not found")
        session_filter = session_id
    else:
        session_filter = repo.UNSET

    rows = repo.list_images(
        user_id, session_id=session_filter, limit=limit, offset=offset
    )
    return [image_payload(row) for row in rows]

@router.get("/images/{image_id}", response_model=ImageDetail)
def get_image(
    image_id: int, user_id: int = Depends(get_current_user_id)
) -> dict:
    row = _active_image(image_id, user_id)
    humanization = repo.get_humanization(image_id, user_id)
    return {"image": image_payload(row), "humanization": humanization}

@router.patch("/images/{image_id}", response_model=ImageOut)
def update_image(
    image_id: int,
    payload: ImageUpdate,
    user_id: int = Depends(get_current_user_id),
) -> dict:
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="No fields to update")
    if changes.get("session_id") is not None and (
        repo.get_session(changes["session_id"], user_id) is None
    ):
        raise HTTPException(status_code=404, detail="Session not found")
    if "original_filename" in changes:
        filename = (changes["original_filename"] or "").strip()
        if not filename:
            raise HTTPException(
                status_code=400, detail="original_filename is required"
            )
        changes["original_filename"] = filename

    row = repo.update_image(image_id, user_id, **changes)
    if row is None:
        raise HTTPException(status_code=404, detail="Image not found")
    repo.touch_image_activity(image_id, user_id)
    return image_payload(row)

@router.delete("/images/{image_id}", status_code=204)
def delete_image(
    image_id: int, user_id: int = Depends(get_current_user_id)
) -> None:
    if not image_service.delete_image(user_id, image_id):
        raise HTTPException(status_code=404, detail="Image not found")

@router.get(
    "/images/{image_id}/messages", response_model=list[ChatMessageOut]
)
def list_chat_messages(
    image_id: int, user_id: int = Depends(get_current_user_id)
) -> list[dict]:
    _owned_image(image_id, user_id)
    return repo.list_chat_messages(image_id, user_id, limit=50)


@router.post(
    "/images/{image_id}/messages", response_model=ChatExchangeOut
)
def create_chat_message(
    image_id: int,
    payload: ChatMessageIn,
    user_id: int = Depends(get_current_user_id),
) -> dict:
    image = _active_image(image_id, user_id)
    question = payload.content.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    history = repo.list_chat_messages(
        image_id, user_id, limit=humanization.MAX_CHAT_HISTORY_MESSAGES
    )
    feedback = repo.get_humanization(image_id, user_id)
    try:
        model, answer = humanization.answer_question(
            image,
            history,
            question,
            existing_feedback=(
                feedback["humanized_text"] if feedback else None
            ),
        )
    except humanization.HumanizationUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return repo.create_chat_exchange(
        image_id,
        user_id,
        user_content=question,
        assistant_content=answer,
        model=model,
    )


@router.delete("/images/{image_id}/messages", status_code=204)
def delete_chat_messages(
    image_id: int, user_id: int = Depends(get_current_user_id)
) -> None:
    _active_image(image_id, user_id)
    repo.clear_chat_messages(image_id, user_id)


@router.get("/images/{image_id}/file")
def get_image_file(
    image_id: int, user_id: int = Depends(get_current_user_id)
) -> Response:
    row = _owned_image(image_id, user_id)
    return _image_file_response(
        repo.get_original_file(image_id, user_id),
        media_type=storage.media_type_for(row["stored_filename"]),
        missing_detail="Image file missing",
    )

@router.get("/images/{image_id}/annotated")
def get_annotated_image(
    image_id: int, user_id: int = Depends(get_current_user_id)
) -> Response:
    row = _owned_image(image_id, user_id)
    if not row.get("annotated_path"):
        raise HTTPException(status_code=404, detail="Annotated image not found")
    return _image_file_response(
        repo.get_annotated_file(image_id, user_id),
        media_type="image/jpeg",
        missing_detail="Annotated image missing",
    )

@router.get(
    "/images/{image_id}/humanization", response_model=HumanizationOut
)
def get_humanization(
    image_id: int, user_id: int = Depends(get_current_user_id)
) -> repo.Row:
    _owned_image(image_id, user_id)
    humanization = repo.get_humanization(image_id, user_id)
    if humanization is None:
        raise HTTPException(status_code=404, detail="Humanization not found")
    return humanization

@router.post(
    "/images/{image_id}/humanization/generate",
    response_model=HumanizationOut,
)
def generate_humanization(
    image_id: int, user_id: int = Depends(get_current_user_id)
) -> repo.Row:
    row = _active_image(image_id, user_id)
    try:
        model, prompt, text = humanization.humanize_image(row)
    except humanization.HumanizationUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return repo.upsert_humanization(
        image_id,
        user_id,
        model=model,
        humanized_text=text,
        prompt=prompt,
    )

@router.put(
    "/images/{image_id}/humanization", response_model=HumanizationOut
)
def put_humanization(
    image_id: int,
    payload: HumanizationIn,
    user_id: int = Depends(get_current_user_id),
) -> repo.Row:
    _active_image(image_id, user_id)
    return repo.upsert_humanization(
        image_id,
        user_id,
        model=payload.model,
        humanized_text=payload.humanized_text,
        prompt=payload.prompt,
    )

@router.patch(
    "/images/{image_id}/humanization", response_model=HumanizationOut
)
def patch_humanization(
    image_id: int,
    payload: HumanizationUpdate,
    user_id: int = Depends(get_current_user_id),
) -> repo.Row:
    _active_image(image_id, user_id)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="No fields to update")
    humanization = repo.update_humanization(image_id, user_id, **changes)
    if humanization is None:
        raise HTTPException(status_code=404, detail="Humanization not found")
    return humanization

@router.delete("/images/{image_id}/humanization", status_code=204)
def delete_humanization(
    image_id: int, user_id: int = Depends(get_current_user_id)
) -> None:
    _active_image(image_id, user_id)
    if not repo.delete_humanization(image_id, user_id):
        raise HTTPException(status_code=404, detail="Humanization not found")
