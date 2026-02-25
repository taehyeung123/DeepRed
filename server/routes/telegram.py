"""
DeepRed v3.0 — Telegram Routes
텔레그램 양방향 연동: 폴링, 상태, 메시지 조회, 포워딩
"""

import os
import json
import time
import threading
import urllib.request
import urllib.error
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

from deps import EMPLOYEES, memory, route_call

router = APIRouter(prefix="/api", tags=["telegram"])


class TelegramForwardRequest(BaseModel):
    ceo_message: str
    sujin_response: str


# ─── 텔레그램 상태 ───────────────────────────────
_telegram_inbox: list[dict] = []
_max_inbox = 200
_telegram_last_update_id = 0
_telegram_poller_running = False


def _telegram_poll_loop():
    """백그라운드 텔레그램 getUpdates 폴링 (webhook 대체)"""
    global _telegram_last_update_id, _telegram_poller_running

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("⚠️ 텔레그램 폴링 중단: 토큰 또는 CHAT_ID 미설정")
        return

    _telegram_poller_running = True
    base_url = f"https://api.telegram.org/bot{token}"

    # webhook 충돌 방지
    try:
        del_url = f"{base_url}/deleteWebhook"
        del_req = urllib.request.Request(del_url)
        with urllib.request.urlopen(del_req, timeout=10) as resp:
            del_result = json.loads(resp.read().decode())
            print(f"🔧 Webhook 삭제: {del_result}")
    except Exception as e:
        print(f"⚠️ Webhook 삭제 실패 (계속 진행): {e}")

    print(f"📱 텔레그램 폴링 시작 (chat_id={chat_id})")

    while _telegram_poller_running:
        try:
            offset = _telegram_last_update_id + 1 if _telegram_last_update_id else 0
            url = f"{base_url}/getUpdates?timeout=5&offset={offset}"

            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())

            if data.get("ok") and data.get("result"):
                print(f"📩 getUpdates: {len(data['result'])}개 업데이트 수신 (offset={offset})")
                for update in data["result"]:
                    _telegram_last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    sender = msg.get("from", {})
                    msg_chat_id = str(msg.get("chat", {}).get("id", ""))

                    if msg_chat_id != str(chat_id) or not text.strip():
                        continue
                    if sender.get("is_bot", False):
                        continue

                    sender_name = sender.get("first_name", "CEO")

                    entry = {
                        "id": f"tg-{update['update_id']}",
                        "text": text,
                        "sender": "telegram_user",
                        "sender_name": sender_name,
                        "timestamp": datetime.now().isoformat(),
                        "update_id": update["update_id"],
                    }
                    _telegram_inbox.insert(0, entry)
                    if len(_telegram_inbox) > _max_inbox:
                        _telegram_inbox.pop()

                    print(f"📨 텔레그램 수신: [{sender_name}] {text[:50]}")

        except Exception as e:
            err_str = str(e)
            if "409" in err_str:
                print(f"⚠️ 409 Conflict — 15초 후 재시도...")
                try:
                    del_url = f"{base_url}/deleteWebhook"
                    del_req = urllib.request.Request(del_url)
                    urllib.request.urlopen(del_req, timeout=10)
                except Exception:
                    pass
                time.sleep(15)
                continue
            elif "timed out" not in err_str.lower():
                print(f"⚠️ 텔레그램 폴링 오류: {e}")

        time.sleep(3)


def start_telegram_polling():
    """텔레그램 폴링 시작 (백그라운드 스레드)"""
    global _telegram_poller_running
    if _telegram_poller_running:
        return {"status": "already_running"}

    thread = threading.Thread(target=_telegram_poll_loop, daemon=True)
    thread.start()
    return {"status": "started"}


def stop_telegram_polling():
    """텔레그램 폴링 중지"""
    global _telegram_poller_running
    _telegram_poller_running = False


@router.post("/telegram/forward")
async def telegram_forward(req: TelegramForwardRequest):
    """수진 대화를 텔레그램으로 포워딩"""
    from notifications import send_telegram, is_telegram_available

    if not is_telegram_available():
        return {"sent": False, "reason": "telegram_not_configured"}

    msg = (
        f"💬 <b>CEO → 수진 대화</b>\n\n"
        f"👤 CEO: {req.ceo_message}\n\n"
        f"🤖 수진: {req.sujin_response}"
    )

    try:
        result = await send_telegram(msg)
        return {"sent": result}
    except Exception as e:
        return {"sent": False, "reason": str(e)}


@router.get("/telegram/status")
def telegram_status():
    """텔레그램 봇 상태 확인"""
    from notifications import is_telegram_available
    return {
        "available": is_telegram_available(),
        "bot_token_set": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "chat_id_set": bool(os.getenv("TELEGRAM_CHAT_ID")),
        "polling_active": _telegram_poller_running,
        "inbox_count": len(_telegram_inbox),
    }


@router.get("/telegram/updates")
def telegram_updates(limit: int = 20, after: str = None):
    """텔레그램에서 수신된 메시지 목록"""
    items = _telegram_inbox
    if after:
        idx = next((i for i, m in enumerate(items) if m["id"] == after), -1)
        if idx >= 0:
            items = items[:idx]
    return {"messages": items[:limit], "polling_active": _telegram_poller_running}


@router.post("/telegram/start-polling")
def api_start_telegram_polling():
    """텔레그램 폴링 수동 시작"""
    return start_telegram_polling()
