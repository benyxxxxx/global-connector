from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import inspect

# Import the new intent engine's main function
from app.intent.engine import decide_intent as _decide_intent

router = APIRouter(prefix="/intent", tags=["intent"])

class IntentIn(BaseModel):
    message: str
    lang_hint: str | None = None

@router.post("/recognize", summary="Recognize intent (POST)")
async def recognize(payload: IntentIn):
    try:
        # This handles both sync and async decide_intent implementations
        if inspect.iscoroutinefunction(_decide_intent):
            return await _decide_intent(payload.message, payload.lang_hint)
        result = _decide_intent(payload.message, payload.lang_hint)
        if inspect.isawaitable(result):
            result = await result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recognize", summary="Recognize intent (GET)")
async def recognize_get(message: str, lang_hint: str | None = None):
    try:
        if inspect.iscoroutinefunction(_decide_intent):
            return await _decide_intent(message, lang_hint)
        result = _decide_intent(message, lang_hint)
        if inspect.isawaitable(result):
            result = await result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))