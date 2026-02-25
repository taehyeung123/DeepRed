"""
DeepRed v3.0 — Security & Monitoring Routes
태현(보안 담당자) 전용 보안 스캔, 알림, 서버 모니터링 API
"""

import os
import time
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter

from deps import EMPLOYEES, activity_log, add_activity_log

router = APIRouter(prefix="/api/security", tags=["security"])

# ─── 보안 알림 저장소 (인메모리) ─────────────────────────────
_security_alerts: list[dict] = []
_last_scan_result: dict = {}
_last_scan_time: float = 0


# ─── 보안 스캔 ──────────────────────────────────────────────

def _check_env_security() -> list[dict]:
    """환경 변수 보안 점검"""
    findings = []
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')

    # .env 파일 존재 여부
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                content = f.read()
            lines = content.strip().split('\n')

            # 비어있는 키 확인
            empty_keys = []
            set_keys = []
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if not value:
                        empty_keys.append(key)
                    else:
                        set_keys.append(key)

            if empty_keys:
                findings.append({
                    "level": "info",
                    "category": "env",
                    "message": f"빈 환경변수 {len(empty_keys)}개: {', '.join(empty_keys[:5])}",
                })

            # 필수 키 확인
            required = ["GEMINI_API_KEY", "CLAUDE_API_KEY", "GITHUB_TOKEN"]
            missing = [k for k in required if k not in set_keys]
            if missing:
                findings.append({
                    "level": "warning",
                    "category": "env",
                    "message": f"필수 API 키 누락: {', '.join(missing)}",
                })
            else:
                findings.append({
                    "level": "ok",
                    "category": "env",
                    "message": f"API 키 {len(required)}개 모두 설정됨",
                })

        except Exception as e:
            findings.append({
                "level": "error",
                "category": "env",
                "message": f".env 파일 읽기 실패: {str(e)[:100]}",
            })
    else:
        findings.append({
            "level": "warning",
            "category": "env",
            "message": ".env 파일 없음 — 환경변수가 시스템에 직접 설정됐을 수 있음",
        })

    return findings


def _check_api_endpoints() -> list[dict]:
    """API 엔드포인트 보안 점검"""
    findings = []

    # 인증 없이 접근 가능한 엔드포인트 체크 (현재 모든 엔드포인트가 미인증)
    findings.append({
        "level": "warning",
        "category": "api",
        "message": "API 인증 미적용 — 모든 엔드포인트가 공개 상태. Bearer token 또는 API key 인증 권장",
    })

    # CORS 설정 확인
    findings.append({
        "level": "info",
        "category": "api",
        "message": "CORS: 현재 allow_origins=['*'] — 프로덕션에서는 특정 도메인만 허용 권장",
    })

    return findings


def _check_llm_security() -> list[dict]:
    """LLM 관련 보안 점검"""
    findings = []

    try:
        from llm_router import get_router_stats
        stats = get_router_stats()
        findings.append({
            "level": "ok",
            "category": "llm",
            "message": f"LLM 라우터 정상 — 호출 {stats.get('total_calls', 0)}회, "
                       f"Claude {stats.get('claude_calls', 0)}회, Gemini {stats.get('gemini_calls', 0)}회",
        })

        # 비정상적 호출량 체크
        total = stats.get('total_calls', 0)
        if total > 1000:
            findings.append({
                "level": "warning",
                "category": "llm",
                "message": f"LLM 호출 {total}회 — 비용 확인 필요",
            })
    except Exception:
        findings.append({
            "level": "error",
            "category": "llm",
            "message": "LLM 라우터 상태 확인 실패",
        })

    return findings


def _check_github_security() -> list[dict]:
    """GitHub 관련 보안 점검"""
    findings = []

    try:
        from github_reader import GITHUB_TOKEN, REPOS, get_cache_stats
        if GITHUB_TOKEN:
            findings.append({
                "level": "ok",
                "category": "github",
                "message": f"GitHub 토큰 설정됨 — 리포 {len(REPOS)}개 등록",
            })
            cache = get_cache_stats()
            findings.append({
                "level": "info",
                "category": "github",
                "message": f"캐시: {cache.get('total_cached', 0)}개 항목, "
                           f"유효: {cache.get('valid_entries', 0)}개",
            })
        else:
            findings.append({
                "level": "warning",
                "category": "github",
                "message": "GITHUB_TOKEN 미설정 — 코드 읽기 불가",
            })
    except Exception:
        findings.append({
            "level": "error",
            "category": "github",
            "message": "GitHub 모듈 로드 실패",
        })

    return findings


def _check_server_status() -> dict:
    """서버 상태 점검"""
    import sys

    status = {
        "python_version": sys.version.split()[0],
        "uptime_info": "서버 재시작 이후 활동 로그 기반",
        "activity_log_count": len(activity_log),
        "employee_count": len(EMPLOYEES),
        "timestamp": datetime.now().isoformat(),
    }

    # 메모리 사용 (가능한 경우)
    try:
        import resource
        mem = resource.getrusage(resource.RUSAGE_SELF)
        status["memory_mb"] = round(mem.ru_maxrss / 1024, 1)
    except Exception:
        status["memory_mb"] = "N/A (Windows)"

    # DB 상태
    try:
        from database import is_db_available
        status["database"] = "connected" if is_db_available() else "disconnected"
    except Exception:
        status["database"] = "unknown"

    # RedRank 연결
    try:
        from redrank_data import is_available
        status["redrank_connection"] = "connected" if is_available() else "disconnected"
    except Exception:
        status["redrank_connection"] = "unknown"

    return status


def run_full_scan() -> dict:
    """전체 보안 스캔 실행"""
    global _last_scan_result, _last_scan_time

    findings = []
    findings.extend(_check_env_security())
    findings.extend(_check_api_endpoints())
    findings.extend(_check_llm_security())
    findings.extend(_check_github_security())

    server = _check_server_status()

    # 심각도 카운트
    severity_count = {"ok": 0, "info": 0, "warning": 0, "error": 0, "critical": 0}
    for f in findings:
        level = f.get("level", "info")
        severity_count[level] = severity_count.get(level, 0) + 1

    result = {
        "timestamp": datetime.now().isoformat(),
        "findings": findings,
        "server": server,
        "summary": severity_count,
        "total_findings": len(findings),
    }

    _last_scan_result = result
    _last_scan_time = time.time()

    # 경고/에러 발견 시 알림 생성
    warn_count = severity_count.get("warning", 0) + severity_count.get("error", 0)
    if warn_count > 0:
        _add_alert(
            f"보안 스캔 완료 — 경고 {warn_count}건 발견",
            "scan",
            "warning" if severity_count.get("error", 0) == 0 else "error",
            findings=[f for f in findings if f["level"] in ("warning", "error")],
        )

    return result


def _add_alert(message: str, category: str, level: str = "warning",
               findings: list = None):
    """보안 알림 추가"""
    alert = {
        "id": f"alert-{int(time.time() * 1000)}",
        "message": message,
        "category": category,
        "level": level,
        "timestamp": datetime.now().isoformat(),
        "findings": findings or [],
        "acknowledged": False,
    }
    _security_alerts.insert(0, alert)
    # 최대 100개 유지
    if len(_security_alerts) > 100:
        _security_alerts.pop()


# ─── API 엔드포인트 ──────────────────────────────────────────

@router.get("/scan")
def security_scan():
    """보안 스캔 실행 (결과 캐시 5분)"""
    global _last_scan_result, _last_scan_time

    # 5분 이내 스캔 결과가 있으면 캐시 반환
    if _last_scan_result and (time.time() - _last_scan_time) < 300:
        return {**_last_scan_result, "cached": True}

    result = run_full_scan()

    add_activity_log(
        "taehyun", "태현", "security",
        f"보안 스캔 실행 — {result['summary'].get('warning', 0)}건 경고",
        "security", "🔒"
    )

    return {**result, "cached": False}


@router.get("/alerts")
def get_alerts(limit: int = 20, unacknowledged_only: bool = False):
    """보안 알림 목록"""
    alerts = _security_alerts
    if unacknowledged_only:
        alerts = [a for a in alerts if not a.get("acknowledged")]
    return {
        "alerts": alerts[:limit],
        "total": len(alerts),
        "unacknowledged": sum(1 for a in _security_alerts if not a.get("acknowledged")),
    }


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str):
    """알림 확인 처리"""
    for alert in _security_alerts:
        if alert["id"] == alert_id:
            alert["acknowledged"] = True
            return {"success": True}
    return {"success": False, "error": "알림을 찾을 수 없습니다"}


@router.get("/server-status")
def server_status():
    """서버 상태 모니터링"""
    return _check_server_status()


@router.get("/summary")
def security_summary():
    """태현 채팅용 보안 요약 (텍스트 형태)"""
    # 최근 스캔이 없으면 실행
    if not _last_scan_result or (time.time() - _last_scan_time) > 600:
        run_full_scan()

    scan = _last_scan_result
    parts = ["[보안 현황]"]

    # 스캔 요약
    summary = scan.get("summary", {})
    parts.append(
        f"\n🔒 마지막 스캔: {scan.get('timestamp', 'N/A')}"
        f"\n   결과: ✅{summary.get('ok', 0)} | ℹ️{summary.get('info', 0)} | "
        f"⚠️{summary.get('warning', 0)} | ❌{summary.get('error', 0)}"
    )

    # 미확인 알림
    unack = sum(1 for a in _security_alerts if not a.get("acknowledged"))
    if unack > 0:
        parts.append(f"\n🚨 미확인 보안 알림: {unack}건")
        for a in _security_alerts[:3]:
            if not a.get("acknowledged"):
                parts.append(f"   - [{a['level']}] {a['message']}")

    # 서버 상태
    server = scan.get("server", {})
    parts.append(
        f"\n🖥️ 서버: Python {server.get('python_version', '?')}"
        f" | DB: {server.get('database', '?')}"
        f" | RedRank: {server.get('redrank_connection', '?')}"
    )

    # 주요 경고만 포함
    warnings = [f for f in scan.get("findings", []) if f["level"] in ("warning", "error")]
    if warnings:
        parts.append("\n⚠️ 주요 경고:")
        for w in warnings[:5]:
            parts.append(f"   - {w['message'][:100]}")

    return {"text": "\n".join(parts)}
