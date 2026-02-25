"""
DeepRed v3.0 — System Routes
스케줄러, 도구, 알림
"""

from fastapi import APIRouter

from deps import (
    get_scheduler_status, run_job_now,
    get_available_tools, run_tool,
    notifier,
)

router = APIRouter(prefix="/api", tags=["system"])


# ─── 스케줄러 ────────────────────────────────────
@router.get("/scheduler/status")
def scheduler_status():
    """스케줄러 상태"""
    return get_scheduler_status()


@router.post("/scheduler/run/{job_id}")
def run_scheduled_job(job_id: str):
    """작업 즉시 실행"""
    return run_job_now(job_id)


# ─── 도구 ────────────────────────────────────────
@router.get("/tools")
def list_tools():
    """사용 가능한 도구 목록"""
    return {"tools": get_available_tools()}


@router.post("/tools/{tool_name}")
def execute_tool(tool_name: str):
    """도구 실행"""
    return run_tool(tool_name)


# ─── 알림 ────────────────────────────────────────
@router.get("/notifications")
def get_notifications(limit: int = 20, unread_only: bool = False):
    """알림 목록"""
    return {
        "notifications": notifier.get_all(limit, unread_only),
        "unread_count": notifier.get_unread_count(),
    }


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: str):
    """알림 읽음 처리"""
    success = notifier.mark_read(notification_id)
    return {"success": success}


@router.post("/notifications/read-all")
def mark_all_read():
    """전체 알림 읽음"""
    notifier.mark_all_read()
    return {"success": True}
