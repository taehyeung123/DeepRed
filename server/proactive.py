"""
DeepRed v3.1 — 수진 자율 메시지 시스템 (Proactive Messaging)
수진이가 주기적 + 이벤트 기반으로 대표님께 먼저 메시지를 보냄
v3.1: Claude chat_with_tools 기반 AI 분석 보고서 생성
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
    
    # ── 1. 아침 브리핑 (09:00~09:10) ── Claude AI 분석
    if hour == 9 and _should_check("morning_greeting", interval_minutes=720):
        text = _generate_morning_briefing_ai()
        if text:
            add_proactive_message("sujin", "수진", text, "briefing", "☀️")
            _send_telegram_notification("☀️ 아침 브리핑", text)
            results.append("morning_briefing")
    
    # ── 2. 시스템 헬스체크 (매 30분) ──
    if _should_check("health_check", interval_minutes=30):
        alert = _check_system_health()
        if alert:
            add_proactive_message("sujin", "수진", alert, "alert", "🚨")
            _send_telegram_notification("🚨 시스템 알림", alert)
            results.append("health_alert")
    
    # ── 3. 활동 요약 (14:00, 18:00) ──
    if hour in [14, 18] and _should_check(f"activity_summary_{hour}", interval_minutes=720):
        summary = _generate_activity_summary()
        if summary:
            add_proactive_message("sujin", "수진", summary, "summary", "📊")
            results.append("activity_summary")
    
    # ── 4. 퇴근 보고 (18:00~18:10) ── Claude AI 분석
    if hour == 18 and _should_check("evening_report", interval_minutes=720):
        text = _generate_evening_report_ai()
        if text:
            add_proactive_message("sujin", "수진", text, "report", "🌙")
            _send_telegram_notification("🌙 저녁 보고", text)
            results.append("evening_report")
    
    # ── 5. 작업 큐 현황 (매 30분) ──
    if _should_check("task_queue_status", interval_minutes=30):
        tq_msg = _check_task_queue_status()
        if tq_msg:
            add_proactive_message("sujin", "수진", tq_msg, "task_status", "📋")
            results.append("task_queue_status")
    
    return {"checked": True, "generated": results, "timestamp": now.isoformat()}


# ─── Claude AI 기반 브리핑 생성 ──────────────────────────

def _generate_morning_briefing_ai() -> str | None:
    """아침 브리핑 — Claude chat_with_tools로 AI 분석 보고서 생성"""
    try:
        from llm_router import _get_claude, is_claude_available
        from sujin_tools import chat_with_tools

        if not is_claude_available():
            print("  ⚠️ Claude 미사용 → 하드코딩 브리핑 폴백")
            return _generate_morning_briefing_fallback()

        client = _get_claude()

        system_prompt = (
            "당신은 딥레드 AI 회사의 COO 수진입니다. "
            "매일 아침 09:00에 CEO 대표님께 브리핑을 올립니다.\n\n"
            "[지시사항]\n"
            "1. get_employees, get_system_health, get_activity_log 도구를 호출해서 현재 상태를 파악하세요.\n"
            "2. 파악한 데이터를 분석하여 간결하고 유용한 아침 브리핑을 작성하세요.\n"
            "3. 형식: 이모지 포함 마크다운, 핵심 2~3줄 + 상세 항목\n"
            "4. 톤: 밝고 프로페셔널한 COO의 보고체\n"
            "5. 500자 이내로 작성하세요."
        )
        user_message = "오늘 아침 브리핑을 생성해주세요."

        text, model = chat_with_tools(client, system_prompt, user_message,
                                       temperature=0.7, max_tokens=2048)
        print(f"  ✅ AI 아침 브리핑 생성 완료 ({model}, {len(text)}자)")
        return text

    except Exception as e:
        print(f"  ⚠️ AI 아침 브리핑 실패: {e} → 폴백")
        return _generate_morning_briefing_fallback()


def _generate_evening_report_ai() -> str | None:
    """저녁 보고 — Claude chat_with_tools로 AI 분석 보고서 생성"""
    try:
        from llm_router import _get_claude, is_claude_available
        from sujin_tools import chat_with_tools

        if not is_claude_available():
            return _generate_evening_report_fallback()

        client = _get_claude()

        system_prompt = (
            "당신은 딥레드 AI 회사의 COO 수진입니다. "
            "매일 18:00에 CEO 대표님께 저녁 보고를 올립니다.\n\n"
            "[지시사항]\n"
            "1. get_activity_log, get_system_health 도구를 호출해서 오늘의 성과를 파악하세요.\n"
            "2. 오늘 하루 활동 요약 + 내일 예상 업무를 보고하세요.\n"
            "3. 형식: 이모지 포함 마크다운, 핵심 요약 + 상세\n"
            "4. 톤: 따뜻하면서도 프로페셔널한 저녁 보고\n"
            "5. 400자 이내로 작성하세요."
        )
        user_message = "오늘 하루 저녁 보고를 생성해주세요."

        text, model = chat_with_tools(client, system_prompt, user_message,
                                       temperature=0.7, max_tokens=2048)
        print(f"  ✅ AI 저녁 보고 생성 완료 ({model}, {len(text)}자)")
        return text

    except Exception as e:
        print(f"  ⚠️ AI 저녁 보고 실패: {e} → 폴백")
        return _generate_evening_report_fallback()


# ─── 폴백 브리핑 (Claude 미사용 시) ──────────────────────

def _generate_morning_briefing_fallback() -> str | None:
    """아침 브리핑 폴백 — Claude 없을 때 하드코딩 버전"""
    try:
        from sujin_tools import execute_tool
        health = json.loads(execute_tool("get_system_health", {}))
        employees = json.loads(execute_tool("get_employees", {}))
        
        now = datetime.now()
        day_name = ["월", "화", "수", "목", "금", "토", "일"][now.weekday()]
        
        text = f"☀️ 대표님, 좋은 아침입니다! {now.month}월 {now.day}일 ({day_name})요일 모닝 브리핑입니다.\n\n"
        
        status = health.get("status", "unknown")
        if status in ("ok", "healthy"):
            text += "✅ 시스템 정상 가동 중입니다.\n"
        else:
            text += f"⚠️ 시스템 상태: {status}\n"
        
        text += f"👥 현재 {len(employees)}명의 직원이 근무 중입니다.\n"
        text += "\n오늘도 좋은 하루 되세요, 대표님! 궁금한 점 있으시면 언제든 말씀해주세요."
        
        return text
    except Exception as e:
        print(f"⚠️ 모닝 브리핑 폴백 생성 실패: {e}")
        return None


def _generate_evening_report_fallback() -> str | None:
    """퇴근 보고 폴백"""
    try:
        now = datetime.now()
        text = f"🌙 대표님, 오늘 하루도 수고하셨습니다.\n\n"
        text += "오늘의 주요 활동과 내일 예정 사항이 궁금하시면 말씀해주세요.\n"
        text += "편안한 저녁 되세요!"
        return text
    except Exception as e:
        print(f"⚠️ 퇴근 보고 폴백 생성 실패: {e}")
        return None


# ─── 헬스체크 + 기타 ─────────────────────────────────────

def _check_system_health() -> str | None:
    """시스템 헬스 체크 — 이상 있을 때만 메시지 생성"""
    try:
        from sujin_tools import execute_tool
        health = json.loads(execute_tool("get_system_health", {}))
        
        status = health.get("status", "unknown")
        if status in ("ok", "healthy"):
            return None  # 정상이면 메시지 안 보냄
        
        return f"🚨 대표님, 시스템 이상 감지되었습니다.\n상태: {status}\n확인이 필요합니다."
    except Exception as e:
        print(f"⚠️ 헬스체크 실패: {e}")
        return None


def _generate_activity_summary() -> str | None:
    """직원 활동 요약"""
    try:
        from sujin_tools import execute_tool
        logs = json.loads(execute_tool("get_activity_log", {"limit": 10}))
        
        if not logs:
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


def _check_task_queue_status() -> str | None:
    """작업 큐 현황 체크 — 대기/진행 중 작업이 있을 때만 보고"""
    try:
        from task_queue import get_queue_stats
        stats = get_queue_stats()
        
        pending = stats.get("pending", 0)
        in_progress = stats.get("in_progress", 0)
        done = stats.get("done", 0)
        
        if pending == 0 and in_progress == 0:
            return None  # 할 일 없으면 조용히
        
        text = f"📋 작업 큐 현황\n\n"
        text += f"⏳ 대기: {pending}건\n"
        text += f"🔄 진행 중: {in_progress}건\n"
        text += f"✅ 완료: {done}건\n"
        
        if pending > 5:
            text += "\n⚠️ 대기 작업이 많습니다. 처리 속도 점검이 필요합니다."
        
        return text
    except Exception as e:
        print(f"⚠️ 작업 큐 상태 확인 실패: {e}")
        return None


# ─── 텔레그램 알림 전송 ──────────────────────────────────

def _send_telegram_notification(title: str, body: str):
    """브리핑/보고 생성 시 텔레그램으로 알림 전송"""
    try:
        from notifications import is_telegram_available, send_telegram_sync
        if not is_telegram_available():
            return
        
        # HTML 포맷으로 전송
        message = f"<b>{title}</b>\n\n{body[:500]}"
        send_telegram_sync(message, parse_mode="HTML")
        print(f"  📱 텔레그램 전송 완료: {title}")
    except Exception as e:
        print(f"  ⚠️ 텔레그램 전송 실패: {e}")
