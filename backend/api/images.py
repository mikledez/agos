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
from fastapi.responses import FileResponse

from db import repository as repo
from services import humanization, image_service, storage

from .deps import get_current_user_id
from .schemas import (
    AnalyzeResponse,
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
    row = _owned_image(image_id, user_id)
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

    row = repo.update_image(image_id, user_id, **changes)
    if row is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return image_payload(row)

@router.delete("/images/{image_id}", status_code=204)
def delete_image(
    image_id: int, user_id: int = Depends(get_current_user_id)
) -> None:
    if not image_service.delete_image(user_id, image_id):
        raise HTTPException(status_code=404, detail="Image not found")

@router.get("/images/{image_id}/file")
def get_image_file(
    image_id: int, user_id: int = Depends(get_current_user_id)
) -> FileResponse:
    row = _owned_image(image_id, user_id)
    try:
        path = storage.resolve(row["stored_filename"])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Image not found") from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Image file missing")
    return FileResponse(
        path, media_type=storage.media_type_for(row["stored_filename"])
    )

@router.get("/images/{image_id}/annotated")
def get_annotated_image(
    image_id: int, user_id: int = Depends(get_current_user_id)
) -> FileResponse:
    row = _owned_image(image_id, user_id)
    if not row.get("annotated_path"):
        raise HTTPException(status_code=404, detail="Annotated image not found")
    try:
        path = storage.resolve(row["annotated_path"])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Image not found") from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Annotated image missing")
    return FileResponse(path, media_type="image/jpeg")

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
    row = _owned_image(image_id, user_id)
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
    _owned_image(image_id, user_id)
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
    _owned_image(image_id, user_id)
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
    _owned_image(image_id, user_id)
    if not repo.delete_humanization(image_id, user_id):
        raise HTTPException(status_code=404, detail="Humanization not found")
