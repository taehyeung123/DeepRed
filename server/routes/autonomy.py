"""
DeepRed v3.0 — Autonomy Routes
자율 행동 엔진 API: 상태, 이력, 수동 트리거
"""

from fastapi import APIRouter

from deps import EMPLOYEES, tracker, add_activity_log, memory
from autonomy import run_autonomous_tick, get_autonomy_status, get_autonomy_history

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
