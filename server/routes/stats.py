"""
DeepRed v3.0 — Stats Routes
KPI, 부서통계, 탑퍼포머, 프로젝트 진행률, 출석부, 활동이력, 활동로그
"""

from datetime import datetime
from fastapi import APIRouter

from deps import (
    EMPLOYEES, PROJECTS, project_assignments, activity_log, tracker,
)

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/attendance")
def get_attendance():
    """AI 직원 출근 현황 — 실제 활동 기반"""
    attendance = tracker.get_attendance()
    return {"attendance": attendance, "total": len(attendance), "timestamp": datetime.now().isoformat()}


@router.get("/stats/kpi")
def get_kpi_stats():
    """Dashboard 실시간 KPI"""
    return tracker.get_kpi()


@router.get("/stats/departments")
def get_department_stats():
    """부서별 실시간 생산성"""
    return tracker.get_department_stats()


@router.get("/stats/top-performers")
def get_top_performers(limit: int = 5):
    """실제 활동 기반 탑 퍼포머"""
    return tracker.get_top_performers(limit)


@router.get("/stats/projects")
def get_project_stats():
    """프로젝트별 실시간 진행률"""
    return tracker.get_project_progress(PROJECTS, project_assignments)


@router.get("/stats/activity-history")
def get_activity_history(days: int = 7):
    """주간 일별 활동 히스토리"""
    return tracker.get_activity_history(days)


@router.get("/activity-log")
def get_activity_log(limit: int = 20):
    """실제 활동 로그만 반환"""
    return {"logs": activity_log[:limit]}


@router.get("/redrank/stats")
def get_redrank_stats(employee_id: str = "sujin"):
    """레드랭크 운영 데이터 (직원별 권한 기반)"""
    try:
        from redrank_data import (
            get_total_users, get_revenue_stats,
            get_usage_stats, get_activity_overview,
            EMPLOYEE_DATA_ACCESS, is_available,
        )
        if not is_available():
            return {"available": False, "message": "RedRank Supabase 미연결"}

        access = EMPLOYEE_DATA_ACCESS.get(employee_id, [])
        result = {"available": True, "employee_id": employee_id}

        if "users" in access:
            result["users"] = get_total_users()
        if "revenue" in access:
            result["revenue"] = get_revenue_stats()
        if "usage" in access:
            result["usage"] = get_usage_stats()
        if "activity" in access:
            result["activity"] = get_activity_overview()

        return result
    except Exception as e:
        return {"available": False, "error": str(e)[:200]}
