"""
DeepRed v3.0 — Phase 3: Scheduler
APScheduler 기반 자율 에이전트 크론잡
자동 브리핑, 보안 스캔, 활동 모니터링 등
"""

import os
from datetime import datetime, timezone
from typing import Optional

# ─── 스케줄러 인스턴스 ────────────────────────────────────
_scheduler = None
_scheduler_available = False
_job_history: list[dict] = []
_max_history = 50


def _get_scheduler():
    """APScheduler 싱글톤"""
    global _scheduler, _scheduler_available
    if _scheduler is not None:
        return _scheduler

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        _scheduler = BackgroundScheduler(timezone="Asia/Seoul")
        _scheduler_available = True
        return _scheduler
    except ImportError:
        print("⚠️ apscheduler 패키지가 없습니다. `pip install apscheduler` 후 재시작하세요.")
        _scheduler_available = False
        return None


def is_scheduler_available() -> bool:
    _get_scheduler()
    return _scheduler_available


def _record_job(job_name: str, status: str, detail: str = ""):
    """작업 실행 이력 기록"""
    entry = {
        "job": job_name,
        "status": status,
        "detail": detail,
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }
    _job_history.insert(0, entry)
    if len(_job_history) > _max_history:
        _job_history.pop()


# ─── 자동화 작업 정의 ─────────────────────────────────────
def job_morning_briefing():
    """09:00 CEO 아침 브리핑 자동 생성"""
    try:
        import requests
        resp = requests.post("http://localhost:8000/api/briefing", timeout=60)
        if resp.status_code == 200:
            briefing = resp.json()
            # 텔레그램 알림
            try:
                from notifications import notifier
                notifier.notify_briefing(briefing)
            except Exception:
                pass
            _record_job("morning_briefing", "success", briefing.get("summary", "")[:100])
        else:
            _record_job("morning_briefing", "failed", f"HTTP {resp.status_code}")
    except Exception as e:
        _record_job("morning_briefing", "error", str(e)[:100])


def job_security_scan():
    """매일 10:00 보안 스캔"""
    try:
        from tools import run_tool
        result = run_tool("security_scan")
        if result.get("status") == "success":
            scan = result["result"]
            _record_job("security_scan", "success",
                        f"점수: {scan.get('score', 0)}, 등급: {scan.get('grade', 'N/A')}")
            # 점수 낮으면 알림
            if scan.get("score", 100) < 70:
                try:
                    from notifications import notifier
                    notifier.notify("warning", "보안 점수 하락",
                                    f"보안 점수 {scan['score']}점 — 긴급 점검 필요",
                                    send_to_telegram=True)
                except Exception:
                    pass
        else:
            _record_job("security_scan", "failed", result.get("error", ""))
    except Exception as e:
        _record_job("security_scan", "error", str(e)[:100])


def job_activity_monitor():
    """매시간 활동 모니터링"""
    try:
        import requests
        resp = requests.get("http://localhost:8000/api/activity-log?limit=5", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            count = len(data.get("logs", []))
            _record_job("activity_monitor", "success", f"최근 활동 {count}건 확인")
        else:
            _record_job("activity_monitor", "failed", f"HTTP {resp.status_code}")
    except Exception as e:
        _record_job("activity_monitor", "error", str(e)[:100])


def job_kpi_snapshot():
    """18:00 KPI 스냅샷"""
    try:
        from tools import run_tool
        result = run_tool("kpi_report")
        if result.get("status") == "success":
            kpi = result["result"]
            _record_job("kpi_snapshot", "success",
                        f"DAU: {kpi.get('dau', 0)}, MRR: {kpi.get('mrr_formatted', '')}")
            # DB에 저장
            try:
                from database import db
                import json
                db.save_document(
                    title=f"KPI 스냅샷 — {datetime.now().strftime('%Y-%m-%d')}",
                    content=json.dumps(kpi, ensure_ascii=False),
                    doc_type="report",
                    author_id="yejun",
                    author_name="예준",
                )
            except Exception:
                pass
        else:
            _record_job("kpi_snapshot", "failed", result.get("error", ""))
    except Exception as e:
        _record_job("kpi_snapshot", "error", str(e)[:100])


# ─── 스케줄러 관리 ────────────────────────────────────────
SCHEDULED_JOBS = [
    {
        "id": "morning_briefing",
        "name": "아침 CEO 브리핑",
        "function": job_morning_briefing,
        "trigger": "cron",
        "hour": 9, "minute": 0,
        "description": "매일 09:00 — 수진(COO)이 CEO에게 일일 브리핑 생성",
    },
    {
        "id": "security_scan",
        "name": "보안 스캔",
        "function": job_security_scan,
        "trigger": "cron",
        "hour": 10, "minute": 0,
        "description": "매일 10:00 — 태현(보안관)이 보안 점검 실행",
    },
    {
        "id": "activity_monitor",
        "name": "활동 모니터링",
        "function": job_activity_monitor,
        "trigger": "interval",
        "hours": 1,
        "description": "매시간 — 전체 활동 상태 확인",
    },
    {
        "id": "kpi_snapshot",
        "name": "KPI 스냅샷",
        "function": job_kpi_snapshot,
        "trigger": "cron",
        "hour": 18, "minute": 0,
        "description": "매일 18:00 — 예준(데이터분석가)이 KPI 스냅샷 생성",
    },
]


def start_scheduler():
    """스케줄러 시작 (모든 크론잡 등록)"""
    scheduler = _get_scheduler()
    if not scheduler:
        print("⚠️ 스케줄러를 시작할 수 없습니다.")
        return False

    for job in SCHEDULED_JOBS:
        try:
            if job["trigger"] == "cron":
                scheduler.add_job(
                    job["function"],
                    "cron",
                    id=job["id"],
                    hour=job.get("hour", 0),
                    minute=job.get("minute", 0),
                    replace_existing=True,
                )
            elif job["trigger"] == "interval":
                scheduler.add_job(
                    job["function"],
                    "interval",
                    id=job["id"],
                    hours=job.get("hours", 1),
                    replace_existing=True,
                )
            print(f"  📅 {job['name']} → 등록 완료")
        except Exception as e:
            print(f"  ⚠️ {job['name']} 등록 실패: {e}")

    scheduler.start()
    print("✅ 스케줄러 시작 완료")
    _record_job("scheduler_start", "success", f"{len(SCHEDULED_JOBS)}개 작업 등록")
    return True


def stop_scheduler():
    """스케줄러 중지"""
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        _record_job("scheduler_stop", "success", "")
        print("⏹ 스케줄러 중지")


def run_job_now(job_id: str) -> dict:
    """특정 작업 즉시 실행"""
    job = next((j for j in SCHEDULED_JOBS if j["id"] == job_id), None)
    if not job:
        return {"error": f"작업 '{job_id}'를 찾을 수 없습니다."}

    try:
        job["function"]()
        return {"status": "success", "job": job_id, "name": job["name"]}
    except Exception as e:
        return {"status": "error", "job": job_id, "error": str(e)}


def get_scheduler_status() -> dict:
    """스케줄러 상태"""
    running = _scheduler.running if _scheduler else False
    return {
        "running": running,
        "available": _scheduler_available,
        "jobs": [
            {
                "id": j["id"],
                "name": j["name"],
                "description": j["description"],
                "trigger": j["trigger"],
            }
            for j in SCHEDULED_JOBS
        ],
        "history": _job_history[:10],
    }
