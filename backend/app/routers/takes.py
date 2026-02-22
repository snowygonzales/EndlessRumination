from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import ProblemDB, TakeDB, UserDB, get_db
from app.models.schemas import (
    GenerateBatchRequest,
    GenerateTakeRequest,
    HistoryResponse,
    ProblemHistoryItem,
    TakeResponse,
)
from app.services.auth_service import get_current_user, require_user
from app.config import get_settings
from app.services.claude_service import generate_batch_streaming, generate_take, model_for_lens
from app.services.rate_limiter import check_rate_limit, increment_usage

router = APIRouter(prefix="/api/v1", tags=["takes"])


@router.post("/generate-take", response_model=TakeResponse)
async def generate_single_take(
    payload: GenerateTakeRequest,
    user: UserDB | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a single take from one lens. Non-streaming."""
    is_pro = user and user.subscription_tier == "pro"
    user_id = str(user.id) if user else "anonymous"

    # Rate limit check
    if user:
        limit = await check_rate_limit(user_id, is_pro, "takes")
        if not limit["allowed"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily take limit reached ({limit['limit']})",
            )

    model = model_for_lens(payload.lens_index, is_pro)
    result = await generate_take(payload.problem, payload.lens_index, model=model)

    # Increment usage
    if user:
        await increment_usage(user_id, "takes")

    # Save for Pro users
    if is_pro and user:
        problem = ProblemDB(user_id=user.id, text=payload.problem)
        db.add(problem)
        await db.flush()

        take = TakeDB(
            problem_id=problem.id,
            lens_index=result["lens_index"],
            headline=result["headline"],
            body=result["body"],
            wise=result.get("wise", True),
            saved=True,
        )
        db.add(take)
        await db.commit()

    return result


@router.post("/generate-batch")
async def generate_batch(
    payload: GenerateBatchRequest,
    user: UserDB | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate takes from multiple lenses. Returns SSE stream.

    Fires parallel Claude calls in batches and streams results as they complete.
    """
    is_pro = user and user.subscription_tier == "pro"
    user_id = str(user.id) if user else "anonymous"

    # Rate limit: check problems
    if user:
        problem_limit = await check_rate_limit(user_id, is_pro, "problems")
        if not problem_limit["allowed"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily problem limit reached ({problem_limit['limit']})",
            )
        await increment_usage(user_id, "problems")

    # Validate lens indices
    cfg = get_settings()
    indices = payload.lens_indices
    if not indices:
        indices = list(range(20)) if is_pro else list(range(cfg.free_lens_count))

    # Free users limited to first N lenses
    if not is_pro:
        indices = [i for i in indices if i < cfg.free_lens_count]

    for idx in indices:
        if not 0 <= idx <= 19:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid lens index: {idx}",
            )

    async def event_stream():
        async for event in generate_batch_streaming(payload.problem, indices, is_pro=is_pro):
            yield event
            # Increment take usage per result
            if user and not event.strip().endswith("[DONE]"):
                await increment_usage(user_id, "takes")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/takes/history", response_model=HistoryResponse)
async def get_history(
    user: UserDB = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Get take history for Pro users."""
    if user.subscription_tier != "pro":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="History is a Pro feature",
        )

    result = await db.execute(
        select(ProblemDB)
        .where(ProblemDB.user_id == user.id)
        .options(selectinload(ProblemDB.takes))
        .order_by(ProblemDB.created_at.desc())
        .limit(50)
    )
    problems = result.scalars().all()

    return {
        "problems": [
            ProblemHistoryItem(
                id=p.id,
                text=p.text,
                created_at=p.created_at,
                takes=[
                    TakeResponse(
                        lens_index=t.lens_index,
                        headline=t.headline,
                        body=t.body,
                        wise=t.wise,
                    )
                    for t in sorted(p.takes, key=lambda t: t.lens_index)
                ],
            )
            for p in problems
        ]
    }
