"""
DeepRed v3.0 — 수진 COO 전용 Tool System
Claude tool_use를 통해 수진이 내부 API를 자율적으로 호출
"""

import json
import os
from datetime import datetime
from deps import (
    EMPLOYEES, PROJECTS, project_assignments, activity_log,
    db, memory, get_router_stats,
)


# ─── Tool 정의 (Claude tool_use 스펙) ────────────────────
SUJIN_TOOLS = [
    {
        "name": "get_employees",
        "description": "전체 직원 명단 조회. 이름, 직책, 부서, 성격, 스킬 등 포함",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_employee_detail",
        "description": "특정 직원의 상세 정보 조회 (코드 접근 권한 포함)",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "직원 ID (예: sujin, minsu, siwoo 등)",
                }
            },
            "required": ["employee_id"],
        },
    },
    {
        "name": "get_projects",
        "description": "진행 중인 프로젝트 목록 조회. 프로젝트별 담당 인원, 기술 스택 포함",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_system_health",
        "description": "시스템 전체 상태 확인. DB, LLM 라우터, GitHub 연동, 메모리 등",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_activity_log",
        "description": "최근 활동 로그 조회. 직원들의 업무 활동 기록",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "가져올 로그 수 (기본 20)",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_conversations_stats",
        "description": "대화 이력 통계 조회. 전체 대화 수, 직원별 대화 로그, 업무일지 등",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_department_summary",
        "description": "부서별 요약 조회. 각 부서의 인원 구성, 프로젝트, LLM 티어 등",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_work_logs",
        "description": "직원별 업무일지 조회",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "직원 ID (생략 시 전체 조회)",
                },
                "limit": {
                    "type": "integer",
                    "description": "가져올 일지 수 (기본 10)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_redrank_data",
        "description": "레드랭크 운영 데이터 조회 (매출, 사용자, 구독 현황 등)",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_security_status",
        "description": "보안 현황 요약 조회 (환경변수, API 인증, 서버 상태 등)",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# ─── Tool 실행기 ─────────────────────────────────────────
def execute_tool(tool_name: str, tool_input: dict) -> str:
    """수진의 tool 호출을 실행하고 결과를 JSON 문자열로 반환"""
    try:
        if tool_name == "get_employees":
            result = [
                {
                    "id": e["id"], "name": e["name"], "role": e["role"],
                    "department": e.get("department_name", ""),
                    "personality": e.get("personality", "")[:50],
                    "skills": e.get("skills", [])[:5],
                    "projects": e.get("projects", []),
                }
                for e in EMPLOYEES
            ]
            return json.dumps(result, ensure_ascii=False)

        elif tool_name == "get_employee_detail":
            eid = tool_input.get("employee_id", "")
            agent = next((e for e in EMPLOYEES if e["id"] == eid), None)
            if not agent:
                return json.dumps({"error": f"직원 '{eid}'을 찾을 수 없습니다."}, ensure_ascii=False)
            result = {**agent}
            try:
                from github_reader import get_employee_access_info
                result["code_access"] = get_employee_access_info(eid)
            except Exception:
                result["code_access"] = {"has_access": False}
            return json.dumps(result, ensure_ascii=False)

        elif tool_name == "get_projects":
            result = []
            for key, proj in PROJECTS.items():
                assigned = project_assignments.get(key, [])
                assigned_emps = [e for e in EMPLOYEES if e["id"] in assigned]
                result.append({
                    **proj,
                    "assigned_count": len(assigned_emps),
                    "assigned_employees": [
                        {"id": e["id"], "name": e["name"], "role": e["role"]}
                        for e in assigned_emps
                    ],
                })
            return json.dumps(result, ensure_ascii=False)

        elif tool_name == "get_system_health":
            db_stats = db.get_stats()
            mem_stats = memory.get_stats()
            router_stats = get_router_stats()
            result = {
                "status": "ok",
                "version": "3.0.0",
                "employees": len(EMPLOYEES),
                "database": db_stats,
                "memory": mem_stats,
                "llm_router": router_stats,
                "timestamp": datetime.now().isoformat(),
            }
            try:
                from github_reader import get_cache_stats
                result["github_reader"] = get_cache_stats()
            except Exception:
                pass
            return json.dumps(result, ensure_ascii=False)

        elif tool_name == "get_activity_log":
            limit = tool_input.get("limit", 20)
            recent = activity_log[-limit:] if activity_log else []
            return json.dumps(recent, ensure_ascii=False)

        elif tool_name == "get_conversations_stats":
            stats = db.get_stats()
            return json.dumps(stats, ensure_ascii=False)

        elif tool_name == "get_department_summary":
            from llm_router import TIER_MAP
            dept_map: dict[str, list] = {}
            for e in EMPLOYEES:
                d = e.get("department_name", "기타")
                tier = TIER_MAP.get(e["id"], "gemini")
                dept_map.setdefault(d, []).append({
                    "name": e["name"],
                    "role": e["role"],
                    "llm_tier": tier,
                    "projects": e.get("projects", []),
                })
            return json.dumps(dept_map, ensure_ascii=False)

        elif tool_name == "get_work_logs":
            eid = tool_input.get("employee_id")
            limit = tool_input.get("limit", 10)
            if eid:
                logs = db.get_work_logs_by_employee(eid, limit=limit) if hasattr(db, 'get_work_logs_by_employee') else []
            else:
                logs = db.get_recent_work_logs(limit=limit) if hasattr(db, 'get_recent_work_logs') else []
            return json.dumps(logs, ensure_ascii=False) if logs else json.dumps({"info": "업무일지 조회 기능 준비 중"}, ensure_ascii=False)

        elif tool_name == "get_redrank_data":
            try:
                from redrank_data import get_data_for_employee
                data = get_data_for_employee("sujin")
                return data if data else json.dumps({"info": "레드랭크 데이터 없음"}, ensure_ascii=False)
            except Exception as ex:
                return json.dumps({"error": f"레드랭크 데이터 조회 실패: {str(ex)[:100]}"}, ensure_ascii=False)

        elif tool_name == "get_security_status":
            try:
                from routes.security import security_summary
                return json.dumps(security_summary(), ensure_ascii=False)
            except Exception as ex:
                return json.dumps({"error": f"보안 상태 조회 실패: {str(ex)[:100]}"}, ensure_ascii=False)

        else:
            return json.dumps({"error": f"알 수 없는 도구: {tool_name}"}, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"tool 실행 오류: {str(e)[:200]}"}, ensure_ascii=False)


# ─── Claude Tool Use 대화 (multi-turn) ──────────────────
def chat_with_tools(client, system_prompt: str, user_message: str,
                    temperature: float = 0.8, max_tokens: int = 1500) -> tuple[str, str]:
    """
    Claude tool_use를 사용한 대화. 수진이 필요한 데이터를 자율적으로 조회.
    tool 호출 시 max_tokens=400 (짧은 tool_use 블록), 최종 응답 시 max_tokens=1500 (데이터 포함 답변)

    Returns:
        (response_text, model_name)
    """
    messages = [{"role": "user", "content": user_message}]
    model = "claude-sonnet-4-20250514"

    # 최대 3회 tool use 반복
    for i in range(3):
        response = client.messages.create(
            model=model,
            max_tokens=500,  # tool 호출용 — 짧은 블록
            system=system_prompt,
            messages=messages,
            tools=SUJIN_TOOLS,
            temperature=temperature,
        )

        # tool_use가 없으면 최종 응답 — 토큰 넉넉하게 재요청
        if response.stop_reason != "tool_use":
            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text += block.text
            if text.strip():
                return text.strip(), "claude-sonnet"
            # 텍스트가 비어있으면 아래 최종 호출로

        # tool_use 처리
        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})

        tool_results = []
        for block in assistant_content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    # 최종 응답: tool 없이 텍스트만 생성 — 토큰 충분히 할당
    try:
        final = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
            temperature=temperature,
        )
        text = ""
        for block in final.content:
            if hasattr(block, "text"):
                text += block.text
        if text.strip():
            return text.strip(), "claude-sonnet"
    except Exception as e:
        print(f"⚠️ chat_with_tools 최종 응답 실패: {str(e)[:100]}")

    return "시스템 데이터를 조회했으나 응답 생성에 실패했습니다. 다시 질문해주세요.", "claude-sonnet"

