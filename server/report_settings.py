"""
DeepRed v3.2 — 보고 설정 (Report Settings)
웹 대시보드에서 보고 항목/시간/채널을 설정할 수 있음.
JSON 파일 기반 저장 — Docker volume으로 영구 보존.
"""

import os
import json
import threading
from copy import deepcopy

_DATA_DIR = os.getenv("DATA_DIR", ".")
_SETTINGS_FILE = os.path.join(_DATA_DIR, "report_settings.json")
_lock = threading.Lock()

# ─── 기본 설정 ────────────────────────────────────────────

DEFAULT_SETTINGS = {
    "report_items": {
        "api_usage": {
            "label": "API 사용량 · 비용",
            "description": "Claude/Gemini 호출 횟수와 예상 비용",
            "enabled": True,
            "icon": "💰",
        },
        "employee_activity": {
            "label": "직원 업무 성과",
            "description": "각 AI 직원이 수행한 작업 요약",
            "enabled": True,
            "icon": "👥",
        },
        "system_health": {
            "label": "시스템 상태",
            "description": "서버, DB, Redis 연결 상태",
            "enabled": True,
            "icon": "🖥️",
        },
        "task_queue": {
            "label": "작업 큐 현황",
            "description": "대기/진행/완료 작업 통계",
            "enabled": True,
            "icon": "📋",
        },
        "security": {
            "label": "보안 스캔 결과",
            "description": "보안 점검 및 위협 감지 현황",
            "enabled": True,
            "icon": "🛡️",
        },
        "project_progress": {
            "label": "프로젝트 진행 상황",
            "description": "댕냥/레드랭크 등 프로젝트별 상태",
            "enabled": True,
            "icon": "📈",
        },
    },
    "schedule": {
        "morning_hour": 9,
        "morning_minute": 0,
        "evening_hour": 18,
        "evening_minute": 0,
    },
    "channels": {
        "telegram": True,
        "kakao": True,
        "web": True,
    },
}


# ─── 설정 로드/저장 ───────────────────────────────────────

_settings: dict = {}


def _load_settings():
    """파일에서 설정 로드 — 없으면 기본값 사용"""
    global _settings
    try:
        if os.path.exists(_SETTINGS_FILE):
            with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # 기본값과 병합 (새 항목이 추가됐을 때 대비)
            merged = deepcopy(DEFAULT_SETTINGS)
            for section in ["report_items", "schedule", "channels"]:
                if section in saved:
                    if isinstance(saved[section], dict):
                        merged[section].update(saved[section])
            _settings = merged
            print("📋 보고 설정 로드됨")
        else:
            _settings = deepcopy(DEFAULT_SETTINGS)
            print("📋 보고 설정 기본값 사용")
    except Exception as e:
        print(f"⚠️ 보고 설정 로드 실패: {e}")
        _settings = deepcopy(DEFAULT_SETTINGS)


def _save_settings():
    """설정을 파일에 저장"""
    try:
        os.makedirs(os.path.dirname(_SETTINGS_FILE) or ".", exist_ok=True)
        with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(_settings, f, ensure_ascii=False, indent=2)
        print("📋 보고 설정 저장됨")
    except Exception as e:
        print(f"⚠️ 보고 설정 저장 실패: {e}")


# 시작 시 로드
_load_settings()


# ─── 공개 API ─────────────────────────────────────────────

def get_settings() -> dict:
    """현재 설정 반환"""
    with _lock:
        return deepcopy(_settings)


def update_settings(new_settings: dict) -> dict:
    """설정 업데이트"""
    with _lock:
        for section in ["report_items", "schedule", "channels"]:
            if section in new_settings:
                if isinstance(new_settings[section], dict):
                    _settings[section].update(new_settings[section])
        _save_settings()
        return deepcopy(_settings)


def get_enabled_items() -> list[str]:
    """활성화된 보고 항목 ID 목록"""
    with _lock:
        items = _settings.get("report_items", {})
        return [k for k, v in items.items() if v.get("enabled", False)]


def get_channel_config() -> dict:
    """채널 설정"""
    with _lock:
        return deepcopy(_settings.get("channels", {}))


def get_schedule_config() -> dict:
    """스케줄 설정"""
    with _lock:
        return deepcopy(_settings.get("schedule", {}))
