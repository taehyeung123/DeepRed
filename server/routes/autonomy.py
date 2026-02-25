"""
DeepRed v3.0 — Autonomy Routes
자율 행동 엔진 API: 상태, 이력, 수동 트리거 + 수진 자율 메시지
"""

from fastapi import APIRouter
from pydantic import BaseModel

from deps import EMPLOYEES, tracker, add_activity_log, memory
from autonomy import run_autonomous_tick, get_autonomy_status, get_autonomy_history
from proactive import (
    get_unread_messages, mark_messages_read, get_all_messages,
    run_sujin_proactive_check, add_proactive_message,
)

router = APIRouter(prefix="/api", tags=["autonomy"])


@router.get("/autonomy/status")
def autonomy_status():
    """자율 행동 엔진 상태"""
    return get_autonomy_status()


@router.get("/autonomy/history")
def autonomy_history(limit: int = 20):
    """자율 행동 이력"""
    return {"actions": get_autonomy_history(limit)}


@router.post("/autonomy/trigger")
def autonomy_trigger():
    """자율 행동 수동 트리거 (1회 틱)"""
    result = run_autonomous_tick(EMPLOYEES, tracker, add_activity_log, memory)
    return result


# ─── 수진 자율 메시지 API ─────────────────────────────────

@router.get("/proactive/messages")
def proactive_messages(employee_id: str = None):
    """읽지 않은 자율 메시지 반환"""
    msgs = get_unread_messages(employee_id)
    return {"messages": msgs, "count": len(msgs)}


@router.get("/proactive/all")
def proactive_all(limit: int = 20):
    """최근 자율 메시지 전체"""
    return {"messages": get_all_messages(limit)}


class MarkReadRequest(BaseModel):
    message_ids: list[str]

@router.post("/proactive/read")
def proactive_read(req: MarkReadRequest):
    """메시지 읽음 처리"""
    mark_messages_read(req.message_ids)
    return {"ok": True}


@router.post("/proactive/trigger")
def proactive_trigger():
    """수진 자율 체크 수동 트리거"""
    result = run_sujin_proactive_check()
    return result

