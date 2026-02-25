"""
DeepRed v3.0 — Collaboration Routes
부서 간 협업, 프로젝트 배정
"""

import json
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from deps import (
    EMPLOYEES, PROJECTS, project_assignments, activity_log, tracker,
    db, memory, call_gemini, add_activity_log, parse_json_response,
    ICON_MAP, TYPE_MAP,
)

router = APIRouter(prefix="/api", tags=["collaboration"])


class CollaborateRequest(BaseModel):
    task: str
    project: str = ""


class AssignRequest(BaseModel):
    project: str
    employee_ids: list[str]


@router.post("/collaborate")
def collaborate(req: CollaborateRequest):
    """수진(COO)이 관련 부서 직원을 자동 배당하여 협업 결과 생성"""
    agent_list = "\n".join([
        f"- {a['name']}({a['role']}, {a['department_name']}): 스킬={', '.join(a.get('skills', [])[:3])}"
        for a in EMPLOYEES
    ])

    project_context = ""
    if req.project and req.project in PROJECTS:
        p = PROJECTS[req.project]
        assigned = project_assignments.get(req.project, [])
        assigned_names = [e["name"] for e in EMPLOYEES if e["id"] in assigned]
        project_context = f"\n프로젝트: {p['name']} ({p['status']})\n배정 인력: {', '.join(assigned_names)}"

    system_prompt = f"""당신은 딥레드(DeepRed) AI 스타트업의 총괄이사 '수진'(COO)입니다.
CEO가 업무를 지시하면, 관련 부서 직원 2~5명을 선별하여 순차적 협업 플로우를 설계합니다.

## 직원 목록
{agent_list}
{project_context}

## 규칙
1. CEO의 지시를 분석하여 관련 직원을 2~5명 선별
2. 각 직원이 순서대로 무엇을 할지 구체적으로 설명
3. 최종 결과 요약

반드시 아래 JSON으로만 응답:

{{
  "coordinator": "수진",
  "coordinator_comment": "수진의 한마디",
  "steps": [
    {{"employee": "이름", "department": "부서명", "action": "구체적 업무", "result": "예상 산출물"}}
  ],
  "summary": "전체 협업 결과 요약"
}}"""

    try:
        raw = call_gemini(
            system_prompt,
            f'CEO 지시: "{req.task}"',
            temperature=0.8, max_tokens=1500,
        )

        if raw.startswith("⚠️"):
            return _fallback_collaboration(req.task, raw)

        result = parse_json_response(raw)

        # 활동 로그
        collab_action = f"협업 플로우 설계 — '{req.task[:30]}' ({len(result.get('steps', []))}명 배정)"
        add_activity_log("sujin", "수진", "control", collab_action, "report", "🤝")
        tracker.record_activity("sujin", "collab")

        for step in result.get("steps", []):
            emp = next((e for e in EMPLOYEES if e["name"] == step.get("employee")), None)
            if emp:
                step_action = f"협업 참여 — {step.get('action', '')[:40]}"
                add_activity_log(
                    emp["id"], emp["name"], emp["department"],
                    step_action, TYPE_MAP.get(emp["department"], "report"),
                    ICON_MAP.get(emp["department"], "📋")
                )
                tracker.record_activity(emp["id"], "collab")

        # 협업 결과 문서 저장
        db.save_document(
            title=f"협업 결과 — {req.task[:50]}",
            content=json.dumps(result, ensure_ascii=False),
            doc_type="collaboration",
            author_id="sujin",
            author_name="수진",
            project=req.project or None,
        )
        memory.remember(
            f"협업: {req.task}. 결과: {result.get('summary', '')}",
            source_type="collaboration",
            employee_id="sujin",
        )

        return result

    except (json.JSONDecodeError, Exception) as e:
        return _fallback_collaboration(req.task, str(e))


def _fallback_collaboration(task: str, error: str = ""):
    return {
        "coordinator": "수진",
        "coordinator_comment": f"'{task}' 업무를 접수했습니다. 관련 부서에 배분하겠습니다.",
        "steps": [
            {"employee": "민수", "department": "기획실", "action": "업무 요구사항 분석", "result": "기획서 초안"},
            {"employee": "서윤", "department": "디자인 스튜디오", "action": "UI/UX 설계", "result": "와이어프레임"},
        ],
        "summary": f"기획 → 디자인 순서로 진행됩니다. (참고: {error[:100]})" if error else "기획 → 디자인 순서로 진행됩니다.",
    }


@router.post("/assign")
def assign_project(req: AssignRequest):
    """프로젝트에 직원 배정/해제"""
    if req.project not in PROJECTS:
        raise HTTPException(status_code=404, detail=f"프로젝트 '{req.project}'를 찾을 수 없습니다.")

    project_assignments[req.project] = req.employee_ids

    for emp in EMPLOYEES:
        if emp["id"] in req.employee_ids:
            if req.project not in emp.get("projects", []):
                emp.setdefault("projects", []).append(req.project)
        else:
            if req.project in emp.get("projects", []):
                emp["projects"].remove(req.project)

    assigned_employees = [e for e in EMPLOYEES if e["id"] in req.employee_ids]

    add_activity_log(
        "sujin", "수진", "control",
        f"'{req.project}' 프로젝트 인력 배정 변경 — {len(assigned_employees)}명", "report", "📋"
    )

    return {
        "project": req.project,
        "assignments": [
            {"employee_id": e["id"], "name": e["name"], "role": e["role"], "project": req.project}
            for e in assigned_employees
        ],
    }
