"""
DeepRed v3.0 — Meeting Routes
긴급 회의, 일일 브리핑
"""

import json
import time
import uuid
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

from deps import (
    EMPLOYEES, PROJECTS, activity_log, tracker, db, memory,
    call_gemini, add_activity_log, parse_json_response,
)

router = APIRouter(prefix="/api", tags=["meeting"])


class MeetingRequest(BaseModel):
    topic: str


@router.post("/meeting")
def run_meeting(req: MeetingRequest):
    """긴급 회의 — 전 에이전트 의견 + 회의록"""
    agent_list = "\n".join([f"- {a['name']}({a['role']}): {a['personality'][:60]}" for a in EMPLOYEES])

    system_prompt = f"""당신은 딥레드(DeepRed) AI 스타트업 회의 시뮬레이터입니다.

## 직원 목록
{agent_list}

## 규칙
1. 모든 직원이 각자 성격/전문에 맞게 안건에 의견을 밝힙니다.
2. 각자 찬성/반대/보류 중 택1 → 2~3문장 이유.
3. 반드시 아래 JSON 배열로만 응답:

[{{"name":"이름","decision":"찬성","reason":"이유"}}]

모든 직원({len(EMPLOYEES)}명 전원)이 포함되어야 합니다."""

    try:
        raw = call_gemini(system_prompt, f'긴급 회의 안건: "{req.topic}"',
                          temperature=0.8, max_tokens=2500)
        if raw.startswith("⚠️"):
            return {"responses": [{"name": a["name"], "decision": "오류", "reason": raw} for a in EMPLOYEES],
                    "minutes": raw}

        results = parse_json_response(raw)
        responses = []
        for r in results:
            name = r.get("name", "???")
            responses.append({
                "name": name,
                "decision": r.get("decision", "보류"),
                "reason": r.get("reason", ""),
            })

        responded = {r["name"] for r in responses}
        for a in EMPLOYEES:
            if a["name"] not in responded:
                responses.append({"name": a["name"], "decision": "보류", "reason": "(응답 누락)"})

    except json.JSONDecodeError:
        responses = [{"name": a["name"], "decision": "보류", "reason": raw[:100] if raw else "파싱 오류"} for a in EMPLOYEES]
    except Exception as e:
        responses = [{"name": a["name"], "decision": "오류", "reason": str(e)[:100]} for a in EMPLOYEES]

    # 활동 로그
    add_activity_log(
        "sujin", "수진", "control",
        f"긴급 회의 소집 — '{req.topic[:30]}' 안건 16명 전원 참석", "report", "🚨"
    )

    # 실시간 통계: 전원 회의 참석
    for r in responses:
        emp = next((e for e in EMPLOYEES if e["name"] == r.get("name")), None)
        if emp:
            tracker.record_activity(emp["id"], "meeting")

    # 회의록 생성
    time.sleep(2)
    opinions = "\n".join([f"- {r['name']}: [{r['decision']}] {r['reason']}" for r in responses])
    try:
        minutes = call_gemini(
            f"""딥레드 총괄이사 수진(COO). 회의록 작성.
안건: "{req.topic}"
의견:\n{opinions}

형식:
📋 회의록 — [안건]
참석: [N]명 | 찬성: [N] | 반대: [N] | 보류: [N]
핵심: (2줄)
수진 의견: (1문장)""",
            "작성", temperature=0.7, max_tokens=600)
    except:
        yes = sum(1 for r in responses if r["decision"] == "찬성")
        no = sum(1 for r in responses if r["decision"] == "반대")
        hold = len(responses) - yes - no
        minutes = f"📋 회의록 — {req.topic}\n참석: {len(responses)}명 | 찬성: {yes} | 반대: {no} | 보류: {hold}"

    return {"responses": responses, "minutes": minutes}


@router.post("/briefing")
def generate_briefing():
    """수진(COO)이 CEO에게 일일 브리핑 생성"""
    project_info = "\n".join([
        f"- {p['name']}({p['icon']}): {p['status']}, 설명: {p['description']}"
        for p in PROJECTS.values()
    ])

    dept_status = {}
    for e in EMPLOYEES:
        d = e["department_name"]
        if d not in dept_status:
            dept_status[d] = []
        dept_status[d].append(f"{e['name']}({e['role']})")
    dept_text = "\n".join([f"- {k}: {', '.join(v)}" for k, v in dept_status.items()])

    recent_logs = activity_log[:10]
    log_text = "\n".join([f"- {l['employee_name']}: {l['action']}" for l in recent_logs]) if recent_logs else "- (최근 활동 없음)"

    system_prompt = f"""당신은 딥레드(DeepRed) AI 스타트업의 총괄이사 '수진'(COO)입니다.
매일 아침 CEO에게 전체 회사 상황을 브리핑합니다.

## 프로젝트 현황
{project_info}

## 부서별 인력
{dept_text}

## 최근 활동 로그
{log_text}

## 규칙
1. 반드시 아래 JSON 형식으로만 응답하세요.
2. **절대 가상 데이터를 만들지 마세요.** DAU, 리텐션, 전환율, 매출 등 실제 데이터가 제공되지 않은 수치는 절대 만들거나 추정하지 마세요.
3. 최근 활동 로그가 없으면 "아직 오늘 기록된 활동이 없습니다"라고 솔직히 말하세요.
4. metric 필드에는 활동 로그에서 직접 확인 가능한 사실만 적으세요.
5. MVP는 실제 활동이 기록된 직원 중에서만 선정하세요. 활동이 없으면 mvp를 null로 설정하세요.

{{
  "greeting": "사장님, 좋은 아침입니다. 수진입니다.",
  "summary": "전체 현황 요약 2~3줄",
  "highlights": [
    {{"project": "프로젝트명", "status": "실제 상태", "metric": "실제 활동 기반 수치만"}}
  ],
  "issues": [
    {{"level": "info", "message": "실제 확인된 이슈만"}}
  ],
  "recommendation": "수진의 추천 액션 1줄",
  "mvp": null
}}"""

    try:
        raw = call_gemini(system_prompt, "오늘의 CEO 브리핑을 작성해주세요.", temperature=0.7, max_tokens=1000)

        if raw.startswith("⚠️"):
            return _fallback_briefing(raw)

        briefing = parse_json_response(raw)

        # 활동 로그
        add_activity_log("sujin", "수진", "control", "CEO 일일 브리핑 생성 완료 ✅", "report", "📊")
        tracker.record_activity("sujin", "briefing")

        # 브리핑 문서 저장
        db.save_document(
            title=f"CEO 브리핑 — {datetime.now().strftime('%Y-%m-%d')}",
            content=json.dumps(briefing, ensure_ascii=False),
            doc_type="briefing",
            author_id="sujin",
            author_name="수진",
        )
        memory.remember(
            f"수진의 CEO 브리핑: {briefing.get('summary', '')}",
            source_type="briefing",
            employee_id="sujin",
        )

        return briefing

    except (json.JSONDecodeError, Exception) as e:
        return _fallback_briefing(str(e))


def _fallback_briefing(error_msg: str = ""):
    """브리핑 생성 실패 시 폴백"""
    return {
        "greeting": "사장님, 수진입니다.",
        "summary": f"AI 브리핑 생성에 실패했습니다. 현재 활동 로그 {len(activity_log)}건이 기록되어 있습니다.",
        "highlights": [
            {"project": p["name"], "status": p["status"], "metric": "활동 데이터 수집 중"}
            for p in PROJECTS.values()
        ],
        "issues": [{"level": "info", "message": error_msg if error_msg else "브리핑 생성 실패"}],
        "recommendation": "잠시 후 새 브리핑을 다시 요청해주세요.",
        "mvp": None,
    }
