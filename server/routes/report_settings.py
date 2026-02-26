"""
DeepRed v3.2 — 보고 설정 API 라우트
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from report_settings import get_settings, update_settings
from kakao import get_kakao_status

router = APIRouter(prefix="/api/report-settings", tags=["report-settings"])


@router.get("")
def get_report_settings():
    """현재 보고 설정 조회"""
    settings = get_settings()
    settings["kakao_status"] = get_kakao_status()
    return settings


class ReportSettingsUpdate(BaseModel):
    report_items: Optional[dict] = None
    schedule: Optional[dict] = None
    channels: Optional[dict] = None


@router.put("")
def update_report_settings(req: ReportSettingsUpdate):
    """보고 설정 변경"""
    updates = {}
    if req.report_items is not None:
        updates["report_items"] = req.report_items
    if req.schedule is not None:
        updates["schedule"] = req.schedule
    if req.channels is not None:
        updates["channels"] = req.channels

    result = update_settings(updates)
    return {"success": True, "settings": result}
