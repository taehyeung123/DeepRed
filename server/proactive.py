"""
DeepRed — 수진 자율 메시지 시스템 (Proactive Messaging)
수진이가 주기적 + 이벤트 기반으로 대표님께 먼저 메시지를 보냄
"""

import threading
import json
from datetime import datetime, timedelta
from collections import deque

_lock = threading.Lock()
_message_queue: deque[dict] = deque(maxlen=50)  # 최대 50개 보관
_last_check: dict[str, datetime] = {}  # 마지막 체크 시각

# ─── 메시지 큐 관리 ──────────────────────────────────────

def add_proactive_message(employee_id: str, employee_name: str, text: str, 
                          category: str = "report", icon: str = "💬"):
    """수진이(또는 다른 직원)의 자율 메시지를 큐에 추가"""
    with _lock:
        msg = {
            "id": f"proactive-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(_message_queue)}",
            "employee_id": employee_id,
            "employee_name": employee_name,
            "text": text,
            "category": category,
            "icon": icon,
            "timestamp": datetime.now().isoformat(),
            "read": False,
        }
        _message_queue.append(msg)
        print(f"📢 자율 메시지 추가: [{employee_name}] {text[:50]}...")
        return msg


def get_unread_messages(employee_id: str = None) -> list[dict]:
    """읽지 않은 자율 메시지 반환 (특정 직원 또는 전체)"""
    with _lock:
        msgs = []
        for msg in _message_queue:
            if msg["read"]:
                continue
            if employee_id and msg["employee_id"] != employee_id:
                continue
            msgs.append(msg)
        return msgs


def mark_messages_read(message_ids: list[str]):
    """메시지를 읽음 처리"""
    with _lock:
        for msg in _message_queue:
            if msg["id"] in message_ids:
                msg["read"] = True


def get_all_messages(limit: int = 20) -> list[dict]:
    """최근 자율 메시지 전체 반환"""
    with _lock:
        return list(_message_queue)[-limit:]


# ─── 수진 자율 체크 로직 ─────────────────────────────────

def _should_check(check_type: str, interval_minutes: int = 10) -> bool:
    """해당 체크를 수행할 시간인지 확인"""
    last = _last_check.get(check_type)
    if not last:
        _last_check[check_type] = datetime.now()
        return True
    if datetime.now() - last >= timedelta(minutes=interval_minutes):
        _last_check[check_type] = datetime.now()
        return True
    return False


def run_sujin_proactive_check():
    """
    수진의 자율 체크 — 스케줄러에서 10분마다 실행.
    시스템 상태를 확인하고, 보고할 내용이 있으면 자율 메시지 생성.
    """
    from deps import EMPLOYEES, tracker
    from sujin_tools import execute_tool
    
    results = []
    now = datetime.now()
    hour = now.hour
    
    # ── 1. 아침 인사 (09:00~09:10) ──
    if hour == 9 and _should_check("morning_greeting", interval_minutes=720):
        text = _generate_morning_briefing()
        if text:
            add_proactive_message("sujin", "수진", text, "briefing", "☀️")
            results.append("morning_briefing")
    
    # ── 2. 시스템 헬스체크 (매 30분) ──
    if _should_check("health_check", interval_minutes=30):
        alert = _check_system_health()
        if alert:
            add_proactive_message("sujin", "수진", alert, "alert", "🚨")
            results.append("health_alert")
    
    # ── 3. 활동 요약 (14:00, 18:00) ──
    if hour in [14, 18] and _should_check(f"activity_summary_{hour}", interval_minutes=720):
        summary = _generate_activity_summary()
        if summary:
            add_proactive_message("sujin", "수진", summary, "summary", "📊")
            results.append("activity_summary")
    
    # ── 4. 퇴근 보고 (18:00~18:10) ──
    if hour == 18 and _should_check("evening_report", interval_minutes=720):
        text = _generate_evening_report()
        if text:
            add_proactive_message("sujin", "수진", text, "report", "🌙")
            results.append("evening_report")
    
    return {"checked": True, "generated": results, "timestamp": now.isoformat()}


def _generate_morning_briefing() -> str | None:
    """아침 브리핑 생성"""
    try:
        from sujin_tools import execute_tool
        # 시스템 상태 + 직원 현황 조회
        health = json.loads(execute_tool("get_system_health", {}))
        employees = json.loads(execute_tool("get_employees", {}))
        
        now = datetime.now()
        day_name = ["월", "화", "수", "목", "금", "토", "일"][now.weekday()]
        
        text = f"☀️ 대표님, 좋은 아침입니다! {now.month}월 {now.day}일 ({day_name})요일 모닝 브리핑입니다.\n\n"
        
        # 시스템 상태
        status = health.get("status", "unknown")
        if status == "healthy":
            text += "✅ 시스템 정상 가동 중입니다.\n"
        else:
            text += f"⚠️ 시스템 상태: {status}\n"
        
        text += f"👥 현재 {len(employees)}명의 직원이 근무 중입니다.\n"
        text += "\n오늘도 좋은 하루 되세요, 대표님! 궁금한 점 있으시면 언제든 말씀해주세요."
        
        return text
    except Exception as e:
        print(f"⚠️ 모닝 브리핑 생성 실패: {e}")
        return None


def _check_system_health() -> str | None:
    """시스템 헬스 체크 — 이상 있을 때만 메시지 생성"""
    try:
        from sujin_tools import execute_tool
        health = json.loads(execute_tool("get_system_health", {}))
        
        status = health.get("status", "unknown")
        if status == "healthy":
            return None  # 정상이면 메시지 안 보냄
        
        return f"🚨 대표님, 시스템 이상 감지되었습니다.\n상태: {status}\n확인이 필요합니다."
    except Exception as e:
        print(f"⚠️ 헬스체크 실패: {e}")
        return None


def _generate_activity_summary() -> str | None:
    """직원 활동 요약"""
    try:
        from sujin_tools import execute_tool
        logs = json.loads(execute_tool("get_activity_logs", {"limit": 10}))
        
        if not logs or (isinstance(logs, dict) and not logs.get("logs")):
            return None
        
        log_list = logs if isinstance(logs, list) else logs.get("logs", [])
        if len(log_list) < 3:
            return None
        
        text = "📊 대표님, 오늘 직원들 활동 현황입니다.\n\n"
        for log in log_list[:5]:
            name = log.get("employee_name", "?")
            action = log.get("action", "?")
            icon = log.get("icon", "📋")
            text += f"{icon} {name}: {action}\n"
        
        text += f"\n총 {len(log_list)}건의 활동이 기록되었습니다."
        return text
    except Exception as e:
        print(f"⚠️ 활동 요약 생성 실패: {e}")
        return None


def _generate_evening_report() -> str | None:
    """퇴근 보고"""
    try:
        now = datetime.now()
        text = f"🌙 대표님, 오늘 하루도 수고하셨습니다.\n\n"
        text += "오늘의 주요 활동과 내일 예정 사항이 궁금하시면 말씀해주세요.\n"
        text += "편안한 저녁 되세요!"
        return text
    except Exception as e:
        print(f"⚠️ 퇴근 보고 생성 실패: {e}")
        return None
