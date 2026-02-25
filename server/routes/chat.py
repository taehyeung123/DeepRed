"""
DeepRed v3.0 — Chat Routes
1:1 채팅, 수진 이중엔진, 단체 채팅, 대화 저장/불러오기
"""

import os
import json
import uuid
import threading
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from deps import (
    EMPLOYEES, activity_log, tracker, db, memory,
    call_gemini, add_activity_log, parse_json_response,
    route_call,
)

router = APIRouter(prefix="/api", tags=["chat"])


# ─── 타입 ──────────────────────────────────────
class ChatRequest(BaseModel):
    employee_id: str
    employee_name: str
    employee_role: str
    message: str
    history: list[dict] = []


class GroupChatRequest(BaseModel):
    message: str
    history: list[dict] = []


class SaveConversationRequest(BaseModel):
    messages: list[dict] = []
    conv_id: str = None
    employee_name: str = ""


# ─── 대화 저장/불러오기 ───────────────────────────
@router.get("/conversations/{employee_id}")
def get_conversations(employee_id: str):
    """직원별 대화 내역 불러오기"""
    convs = db.get_conversations_by_employee(employee_id, limit=1)
    if convs:
        return {"messages": convs[0].get("messages", []), "conv_id": convs[0]["id"]}
    return {"messages": [], "conv_id": None}


@router.post("/conversations/{employee_id}")
def save_conversations(employee_id: str, body: SaveConversationRequest):
    """대화 내역 저장"""
    result_id = db.save_conversation(
        employee_id, body.employee_name or employee_id,
        "chat", body.messages, body.conv_id
    )
    return {"conv_id": result_id, "saved": len(body.messages)}


# ─── 1:1 채팅 ────────────────────────────────────
@router.post("/chat")
def chat(req: ChatRequest):
    """개별 직원 1:1 채팅"""
    agent = next((e for e in EMPLOYEES if e["id"] == req.employee_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.")

    # 수진(COO)은 이중 엔진
    if req.employee_id == "sujin":
        return _chat_sujin(req, agent)

    # 일반 직원
    history_text = ""
    if req.history:
        for msg in req.history[-30:]:
            if msg.get("isUser"):
                history_text += f"\n대표님: {msg.get('content', '')}"
            else:
                history_text += f"\n{agent['name']}: {msg.get('content', '')}"

    # 코드 컨텍스트 주입 (직원별 권한 기반)
    code_context = ""
    try:
        from github_reader import get_code_context
        code_context = get_code_context(req.message, employee_id=agent["id"])
    except Exception:
        pass

    # 레드랭크 운영 데이터 주입 (직원별 권한 기반)
    data_context = ""
    try:
        from redrank_data import get_data_for_employee
        data_context = get_data_for_employee(agent["id"])
    except Exception:
        pass

    system_prompt = f"""당신은 딥레드(DeepRed) AI 스타트업의 직원 '{agent['name']}'입니다.
직책: {agent['role']} | 부서: {agent['department_name']}
성격: {agent['personality']}
스킬: {', '.join(agent.get('skills', []))}
담당 프로젝트: {', '.join(agent.get('projects', []))}

규칙:
1. 자신의 전문 분야에 맞게 2~3문장으로 간결하게 답합니다.
2. 대표님(CEO)의 지시는 반드시 따릅니다.
3. 자연스럽고 전문적인 톤으로 자기 성격에 맞게 대화합니다.
4. 다른 부서와 관련된 질문이면 해당 부서 직원을 추천할 수 있습니다.
5. [코드 참조] 섹션이 있으면, 해당 코드를 참고하여 전문적으로 답변합니다.
6. [레드랭크 운영 현황] 섹션이 있으면, 실제 데이터를 기반으로 답변합니다."""

    if code_context:
        system_prompt += f"\n\n{code_context}"
    if data_context:
        system_prompt += f"\n\n{data_context}"

    human = f"{history_text}\n\n대표님: {req.message}" if history_text else f"대표님: {req.message}"

    result = route_call(
        employee_id=agent["id"],
        system_prompt=system_prompt,
        user_message=human,
        temperature=0.8,
        max_tokens=500,
    )
    response = result["response"]

    # 활동 로그
    add_activity_log(
        agent["id"], agent["name"], agent["department"],
        f"CEO와 1:1 대화 — '{req.message[:30]}...' 응답 완료", "report", "💬"
    )
    tracker.record_activity(agent["id"], "chat")

    # 대화 기억 저장
    conv_summary = f"CEO가 {agent['name']}({agent['role']})에게 '{req.message[:80]}'에 대해 물어봄. 응답: {response[:200]}"
    memory.remember(conv_summary, source_type="chat", employee_id=agent["id"])

    # 대화 이력 DB 저장
    messages = req.history + [
        {"isUser": True, "content": req.message},
        {"isUser": False, "name": agent["name"], "content": response}
    ]
    db.save_conversation(agent["id"], agent["name"], "chat", messages)

    return {"name": agent["name"], "message": response}


def _chat_sujin(req: ChatRequest, agent: dict):
    """
    수진(COO) 채팅 — 이중 엔진 아키텍처
    Gemini(무료) = 메모리 엔진: 전체 대화 분석 → 컨텍스트 압축
    Claude(유료) = 대화 엔진: 압축된 컨텍스트로 응답 생성
    """
    import json as _json
    from memory import build_context_for_claude, summarize_session

    sujin = next(e for e in EMPLOYEES if e["id"] == "sujin")

    # 1단계: Gemini(무료)로 컨텍스트 압축
    context = build_context_for_claude("sujin", req.message, req.history or [])

    # 2단계: 수진 시스템 프롬프트
    system_prompt = f"""당신은 딥레드(DeepRed) AI 스타트업의 COO 박수진입니다.
직책: {sujin['role']}
성격: {sujin['personality']}
스킬: {', '.join(sujin.get('skills', []))}

대표님과 1:1 대화 중입니다. 자연스럽게, 진짜 사람처럼 대화하세요.
형식적인 보고체가 아니라, 실제 임원이 CEO에게 말하듯이 자연스럽게.
상황에 따라 짧게 답할 수도, 길게 분석할 수도 있습니다.

당신은 회사의 GitHub 리포지토리에 읽기 권한이 있습니다.
[코드 참조] 섹션이 제공되면, 해당 코드를 자연스럽게 참조하여 답변하세요.
코드를 그대로 복붙하지 말고, 핵심을 파악해서 사람 말투로 설명하세요."""

    # 3단계: Claude에 압축된 컨텍스트만 전송
    human = f"{context}\n\n대표님: {req.message}" if context else f"대표님: {req.message}"

    result = route_call(
        employee_id="sujin",
        system_prompt=system_prompt,
        user_message=human,
        temperature=0.8,
        max_tokens=800,
    )
    response = result["response"]
    model_used = result["model"]

    # 활동 로그
    add_activity_log(
        "sujin", "수진", agent["department"],
        f"CEO와 1:1 대화 — '{req.message[:30]}...' ({model_used})", "report", "💬"
    )
    tracker.record_activity("sujin", "chat")

    # 대화 기억 저장
    conv_summary = f"CEO가 수진(COO)에게 '{req.message[:80]}'에 대해 물어봄. 응답: {response[:200]}"
    memory.remember(conv_summary, source_type="chat", employee_id="sujin")

    # 대화 이력 DB 저장
    messages = (req.history or []) + [
        {"isUser": True, "content": req.message},
        {"isUser": False, "name": "수진", "content": response}
    ]
    db.save_conversation("sujin", "수진", "chat", messages)

    # 세션 요약 생성 (10개마다)
    if len(messages) % 10 == 0 and len(messages) >= 10:
        threading.Thread(
            target=summarize_session,
            args=("sujin", messages, "수진"),
            daemon=True,
        ).start()

    # 텔레그램 기록 동기화
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        def _send_tg():
            try:
                import urllib.request
                send_url = f"https://api.telegram.org/bot{token}/sendMessage"
                tg_text = f"💬 웹 대화\n👤 CEO: {req.message}\n🤖 수진: {response}"
                send_data = _json.dumps({
                    "chat_id": chat_id,
                    "text": tg_text,
                }).encode()
                send_req = urllib.request.Request(
                    send_url, data=send_data,
                    headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(send_req, timeout=5)
            except Exception:
                pass
        threading.Thread(target=_send_tg, daemon=True).start()

    return {
        "name": "수진",
        "message": response,
        "model": model_used,
        "telegram_synced": bool(token and chat_id),
    }


# ─── 단체 채팅 ───────────────────────────────────
@router.post("/group-chat")
def group_chat(req: GroupChatRequest):
    """단체 채팅방 — 2~4명 반응"""
    agent_list = "\n".join([f"- {a['name']}({a['role']}): {a['personality'][:60]}" for a in EMPLOYEES])
    history_text = ""
    if req.history:
        for msg in req.history[-8:]:
            if msg.get("isUser"):
                history_text += f"\n대표님: {msg.get('content', '')}"
            else:
                history_text += f"\n{msg.get('name', '')}: {msg.get('content', '')}"

    system_prompt = f"""당신은 딥레드(DeepRed) AI 스타트업의 단체 채팅방을 시뮬레이션합니다.

## 직원 목록
{agent_list}

## 규칙
1. 대표님이 메시지를 보내면, 관련된 2~4명이 자연스럽게 반응합니다.
2. 각 직원은 자기 성격/말투로 1~2문장 짧게 답합니다.
3. 반드시 아래 JSON 배열로만 응답하세요 (다른 텍스트 없이):

[{{"name":"이름","message":"응답"}}]"""

    human = f"{history_text}\n\n대표님: {req.message}" if history_text else f"대표님: {req.message}"

    try:
        raw = call_gemini(system_prompt, human, temperature=0.9, max_tokens=1200)
        if raw.startswith("⚠️"):
            return {"responses": [{"name": "시스템", "message": raw}]}

        results = parse_json_response(raw)

        # 활동 로그 + 실시간 통계
        for r in (results if isinstance(results, list) else []):
            emp = next((e for e in EMPLOYEES if e["name"] == r.get("name")), None)
            if emp:
                add_activity_log(
                    emp["id"], emp["name"], emp["department"],
                    "단체 채팅 참여 — 응답 완료", "report", "💬"
                )
                tracker.record_activity(emp["id"], "group_chat")

        return {"responses": results if isinstance(results, list) else [{"name": "시스템", "message": "형식 오류"}]}
    except json.JSONDecodeError:
        return {"responses": [{"name": "수진", "message": raw[:200] if raw else "응답 없음"}]}
    except Exception as e:
        return {"responses": [{"name": "시스템", "message": f"⚠️ {str(e)[:150]}"}]}
