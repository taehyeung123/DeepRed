"""
DeepRed v3.1 — Autonomy Routes
자율 행동 엔진 API: 상태, 이력, 수동 트리거 + 수진 자율 메시지 + 작업 큐
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from deps import EMPLOYEES, tracker, add_activity_log, memory
from autonomy import run_autonomous_tick, get_autonomy_status, get_autonomy_history
from proactive import (
    get_unread_messages, mark_messages_read, get_all_messages,
    run_sujin_proactive_check, add_proactive_message,
)
from task_queue import create_task, get_task, get_tasks, get_queue_stats, process_pending_tasks

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


# ─── 작업 큐 API ──────────────────────────────────────────

class TaskCreateRequest(BaseModel):
    assigned_to: str
    title: str
    instruction: str
    assigned_by: str = "ceo"


@router.get("/tasks")
def list_tasks(status: Optional[str] = None, assigned_to: Optional[str] = None, limit: int = 20):
    """작업 목록 조회 (필터링 가능)"""
    tasks = get_tasks(status=status, assigned_to=assigned_to, limit=limit)
    stats = get_queue_stats()
    return {"tasks": tasks, "stats": stats}


@router.post("/tasks")
def create_new_task(req: TaskCreateRequest):
    """작업 수동 생성 (CEO 직접 지시)"""
    # 직원 존재 확인
    emp = next((e for e in EMPLOYEES if e["id"] == req.assigned_to), None)
    if not emp:
        return {"error": f"직원 '{req.assigned_to}'을 찾을 수 없습니다."}
    
    task = create_task(
        assigned_to=req.assigned_to,
        title=req.title,
        instruction=req.instruction,
        assigned_by=req.assigned_by,
    )
    return {"ok": True, "task": task}


@router.get("/tasks/{task_id}")
def get_single_task(task_id: str):
    """개별 작업 조회"""
    task = get_task(task_id)
    if not task:
        return {"error": f"작업 '{task_id}'을 찾을 수 없습니다."}
    return {"task": task}


@router.post("/tasks/process")
def process_tasks_now():
    """대기 작업 수동 처리 (즉시 실행)"""
    result = process_pending_tasks(EMPLOYEES, max_per_batch=5)
    return result


@router.get("/tasks/stats/summary")
def task_stats():
    """작업 큐 통계"""
    return get_queue_stats()
