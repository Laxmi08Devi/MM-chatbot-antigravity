"""
Multimodal API endpoints: image understanding (vision) and image generation.
"""

import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.database.connection import get_db
from backend.database import repository
from backend.schemas.multimodal import (
    VisionResponse,
    ImageGenerationRequest,
    ImageGenerationResponse
)
from backend.services.multimodal_service import MultimodalService, ALLOWED_IMAGE_EXTENSIONS
from backend.services.document_service import sanitize_filename

router = APIRouter(prefix="/api/multimodal", tags=["Multimodal"])


@router.post("/vision", response_model=VisionResponse)
async def analyze_image(
    file: UploadFile = File(...),
    prompt: str = Form("Describe this image in detail and answer any relevant questions."),
    conversation_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Analyze an uploaded image using a vision-capable AI model.
    Validates file type and size before saving to disk.
    """
    raw_filename = file.filename or "image.png"
    ext = Path(raw_filename).suffix.lower()

    # 1. Reject unsupported file formats immediately before saving
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' is not supported. Allowed image formats: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"
        )

    # 2. Read bytes and enforce size limits
    image_bytes = await file.read()
    if not image_bytes or len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image file is empty."
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    # 3. Sanitize filename and save to disk only after successful validation
    safe_filename = sanitize_filename(raw_filename)
    upload_dir = settings.get_upload_path()
    saved_filename = f"img_{uuid.uuid4().hex[:8]}_{safe_filename}"
    saved_path = upload_dir / saved_filename
    with open(saved_path, "wb") as f:
        f.write(image_bytes)

    media_url = f"/media/uploads/{saved_filename}"

    # 4. Analyze image
    analysis = MultimodalService.analyze_image(
        image_bytes=image_bytes,
        filename=safe_filename,
        user_prompt=prompt
    )

    conv_id = conversation_id
    if conv_id:
        conv = repository.get_conversation(db, conv_id)
        if not conv:
            conv = repository.create_conversation(db, title=prompt[:40], mode="chat")
            conv_id = conv.id

        # Persist user image prompt
        repository.add_message(
            db=db,
            conversation_id=conv_id,
            role="user",
            content=prompt,
            message_type="image",
            media_url=media_url
        )
        # Persist assistant analysis
        repository.add_message(
            db=db,
            conversation_id=conv_id,
            role="assistant",
            content=analysis,
            message_type="image",
            media_url=media_url
        )

    return VisionResponse(
        analysis=analysis,
        image_url=media_url,
        conversation_id=conv_id
    )


@router.post("/generate-image", response_model=ImageGenerationResponse)
def generate_image(request: ImageGenerationRequest, db: Session = Depends(get_db)):
    """
    Generate an image from a text prompt using DALL-E.
    Returns the media URL for playback/preview and saves conversation turn if conversation_id is provided.
    """
    result = MultimodalService.generate_image(prompt=request.prompt)

    conv_id = request.conversation_id
    if conv_id and result["success"]:
        conv = repository.get_conversation(db, conv_id)
        if not conv:
            conv = repository.create_conversation(db, title=request.prompt[:40], mode="chat")
            conv_id = conv.id

        # Persist user prompt
        repository.add_message(
            db=db,
            conversation_id=conv_id,
            role="user",
            content=f"Generate image: {request.prompt}",
            message_type="image"
        )
        # Persist generated image message
        repository.add_message(
            db=db,
            conversation_id=conv_id,
            role="assistant",
            content=f"Here is your generated image for: *{request.prompt}*",
            message_type="image",
            media_url=result["media_url"]
        )

    return ImageGenerationResponse(
        success=result["success"],
        media_url=result["media_url"],
        message=result["message"],
        conversation_id=conv_id
    )

