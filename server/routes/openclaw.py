"""
DeepRed v3.0 — OpenClaw Gateway Routes
OpenClaw 채팅, 상태, 히스토리
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

from deps import EMPLOYEES, activity_log, memory, route_call, add_activity_log

router = APIRouter(prefix="/api", tags=["openclaw"])


class OpenClawChatRequest(BaseModel):
    message: str
    session_id: str = "web-main"


OPENCLAW_BRIDGE_URL = os.getenv(
    "OPENCLAW_BRIDGE_URL",
    "http://172.17.0.1:18800"
)


def _openclaw_bridge_call(path: str, data: dict = None, timeout: int = 90):
    """OpenClaw Bridge HTTP 호출"""
    url = f"{OPENCLAW_BRIDGE_URL}{path}"
    try:
        if data:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json"},
            )
        else:
            req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode()), resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        try:
            return json.loads(body), e.code
        except:
            return {"error": body[:200]}, e.code
    except Exception as e:
        return {"error": str(e)[:200]}, 0


def _sujin_claude_fallback(message: str, error_info: str = ""):
    """수진 Claude 직접 호출 폴백"""
    agent = next((e for e in EMPLOYEES if e["id"] == "sujin"), None)
    if not agent:
        return {"name": "수진", "message": "⚠️ 수진 에이전트를 찾을 수 없습니다.", "source": "error"}

    result = route_call(
        employee_id="sujin",
        system_prompt=f"""당신은 딥레드(DeepRed) AI 스타트업의 총괄이사 '수진'(COO)입니다.
직책: {agent['role']} | 부서: {agent['department_name']}
성격: {agent['personality']}
규칙: 대표님에게 존댓말. 간결하고 핵심만 보고. 한국어로만.""",
        user_message=f"대표님: {message}",
        temperature=0.8,
        max_tokens=500,
    )
    return {
        "name": "수진",
        "message": result["response"],
        "source": "claude-fallback" if error_info else "claude-direct",
    }


@router.post("/openclaw/chat")
def openclaw_chat(req: OpenClawChatRequest):
    """웹 → OpenClaw Bridge → Gateway → 수진"""
    data, status = _openclaw_bridge_call(
        "/chat",
        {"message": req.message, "session_id": req.session_id},
        timeout=90,
    )

    if status == 0:
        return _sujin_claude_fallback(req.message, data.get("error", "bridge unreachable"))

    if status == 200 and data.get("response"):
        response_text = data["response"]

        add_activity_log(
            "sujin", "수진", "control",
            f"웹 채팅 (OpenClaw) — '{req.message[:30]}' 응답", "report", "🤖"
        )

        memory.remember(
            f"웹 채팅(OpenClaw): 대표님이 수진에게 '{req.message[:80]}'. 응답: {response_text[:200]}",
            source_type="chat",
            employee_id="sujin",
        )

        return {"name": "수진", "message": response_text, "source": "openclaw"}

    return _sujin_claude_fallback(req.message, data.get("error", f"status {status}"))


@router.get("/openclaw/status")
def openclaw_status():
    """OpenClaw Gateway 상태 확인"""
    data, status = _openclaw_bridge_call("/status", timeout=10)
    if status == 0:
        return {"status": "bridge_unreachable", "bridge_url": OPENCLAW_BRIDGE_URL}
    return data


@router.get("/openclaw/history")
def openclaw_history(after: str = None, limit: int = 50):
    """OpenClaw 세션 대화 이력 조회"""
    params = f"?limit={limit}"
    if after:
        params += f"&after={after}"
    data, status = _openclaw_bridge_call(f"/history{params}", timeout=15)
    if status == 0:
        return {"messages": [], "error": "bridge_unreachable"}
    return data
