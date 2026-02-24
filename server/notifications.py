"""
DeepRed v3.0 — Phase 3: Notification System
텔레그램 봇 알림 전송 + 인앱 알림 관리
"""

import os
import asyncio
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ─── 인앱 알림 스토어 ──────────────────────────────────────
_notifications: list[dict] = []
_max_notifications = 100

# ─── 텔레그램 봇 ──────────────────────────────────────────
_telegram_available = False


def _check_telegram() -> bool:
    """텔레그램 설정 확인"""
    global _telegram_available
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    _telegram_available = bool(token and chat_id)
    return _telegram_available


def is_telegram_available() -> bool:
    return _check_telegram()


async def send_telegram(message: str, parse_mode: str = "HTML") -> bool:
    """텔레그램 메시지 전송"""
    if not _check_telegram():
        print(f"⚠️ 텔레그램 미설정. 메시지 스킵: {message[:50]}...")
        return False

    try:
        from telegram import Bot
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        bot = Bot(token=token)
        await bot.send_message(chat_id=chat_id, text=message, parse_mode=parse_mode)
        return True
    except ImportError:
        print("⚠️ python-telegram-bot 패키지가 없습니다.")
        return False
    except Exception as e:
        print(f"⚠️ 텔레그램 전송 실패: {e}")
        return False


def send_telegram_sync(message: str, parse_mode: str = "HTML") -> bool:
    """동기 텔레그램 전송 (asyncio 없는 환경용)"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(send_telegram(message, parse_mode))
            return True
        else:
            return loop.run_until_complete(send_telegram(message, parse_mode))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(send_telegram(message, parse_mode))
        return result


# ─── 알림 포맷터 ──────────────────────────────────────────
class NotificationFormatter:
    """알림 메시지 포맷팅"""

    @staticmethod
    def briefing(briefing_data: dict) -> str:
        """CEO 브리핑 알림"""
        greeting = briefing_data.get("greeting", "")
        summary = briefing_data.get("summary", "")
        highlights = briefing_data.get("highlights", [])

        msg = f"🏢 <b>DeepRed 일일 브리핑</b>\n\n"
        msg += f"{greeting}\n\n"
        msg += f"📋 {summary}\n\n"

        if highlights:
            msg += "📊 <b>프로젝트 현황</b>\n"
            for h in highlights:
                msg += f"  • {h.get('project', '')}: {h.get('status', '')} ({h.get('metric', '')})\n"

        issues = briefing_data.get("issues", [])
        if issues:
            msg += "\n⚠️ <b>이슈</b>\n"
            for issue in issues:
                level_icon = "🔴" if issue.get("level") == "critical" else "🟡" if issue.get("level") == "warning" else "🔵"
                msg += f"  {level_icon} {issue.get('message', '')}\n"

        recommendation = briefing_data.get("recommendation", "")
        if recommendation:
            msg += f"\n💡 <b>추천</b>: {recommendation}"

        return msg

    @staticmethod
    def collaboration(collab_data: dict) -> str:
        """협업 결과 알림"""
        comment = collab_data.get("coordinator_comment", "")
        steps = collab_data.get("steps", [])
        summary_text = collab_data.get("summary", "")

        msg = f"🤝 <b>협업 결과</b>\n\n"
        msg += f"수진: {comment}\n\n"

        for i, step in enumerate(steps, 1):
            msg += f"{i}. {step.get('employee', '')}({step.get('department', '')})\n"
            msg += f"   → {step.get('action', '')}\n"

        if summary_text:
            msg += f"\n📝 {summary_text}"

        return msg

    @staticmethod
    def alert(level: str, title: str, message: str) -> str:
        """일반 알림"""
        level_icons = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️", "success": "✅"}
        icon = level_icons.get(level, "📢")
        return f"{icon} <b>{title}</b>\n\n{message}"

    @staticmethod
    def meeting_summary(topic: str, responses: list, minutes: str) -> str:
        """회의 결과 알림"""
        yes = sum(1 for r in responses if r.get("decision") == "찬성")
        no = sum(1 for r in responses if r.get("decision") == "반대")
        hold = len(responses) - yes - no

        msg = f"🚨 <b>긴급 회의 결과</b>\n\n"
        msg += f"📋 안건: {topic}\n"
        msg += f"참석: {len(responses)}명 | 찬성: {yes} | 반대: {no} | 보류: {hold}\n\n"
        msg += minutes[:500]
        return msg


formatter = NotificationFormatter()


# ─── 인앱 알림 매니저 ──────────────────────────────────────
class NotificationManager:
    """인앱 알림 + 텔레그램 통합 관리"""

    def notify(self, level: str, title: str, message: str,
               send_to_telegram: bool = False) -> str:
        """알림 생성"""
        nid = f"n-{len(_notifications):04d}"
        notification = {
            "id": nid,
            "level": level,
            "title": title,
            "message": message,
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _notifications.insert(0, notification)

        if len(_notifications) > _max_notifications:
            _notifications.pop()

        # 텔레그램 알림
        if send_to_telegram:
            telegram_msg = formatter.alert(level, title, message)
            send_telegram_sync(telegram_msg)

        return nid

    def notify_briefing(self, briefing_data: dict):
        """브리핑 알림 (인앱 + 텔레그램)"""
        self.notify("info", "일일 브리핑", briefing_data.get("summary", ""), send_to_telegram=False)
        if is_telegram_available():
            telegram_msg = formatter.briefing(briefing_data)
            send_telegram_sync(telegram_msg)

    def notify_collaboration(self, collab_data: dict):
        """협업 결과 알림"""
        summary = collab_data.get("summary", "")
        self.notify("info", "협업 완료", summary, send_to_telegram=False)
        if is_telegram_available():
            telegram_msg = formatter.collaboration(collab_data)
            send_telegram_sync(telegram_msg)

    def notify_meeting(self, topic: str, responses: list, minutes: str):
        """회의 결과 알림"""
        self.notify("warning", "회의 완료", f"안건: {topic}", send_to_telegram=False)
        if is_telegram_available():
            telegram_msg = formatter.meeting_summary(topic, responses, minutes)
            send_telegram_sync(telegram_msg)

    def get_all(self, limit: int = 20, unread_only: bool = False) -> list[dict]:
        """알림 목록"""
        items = _notifications
        if unread_only:
            items = [n for n in items if not n["read"]]
        return items[:limit]

    def mark_read(self, notification_id: str) -> bool:
        """알림 읽음 처리"""
        for n in _notifications:
            if n["id"] == notification_id:
                n["read"] = True
                return True
        return False

    def mark_all_read(self):
        """전체 읽음 처리"""
        for n in _notifications:
            n["read"] = True

    def get_unread_count(self) -> int:
        return sum(1 for n in _notifications if not n["read"])

    def get_stats(self) -> dict:
        return {
            "total": len(_notifications),
            "unread": self.get_unread_count(),
            "telegram_available": is_telegram_available(),
        }


# 싱글톤
notifier = NotificationManager()
