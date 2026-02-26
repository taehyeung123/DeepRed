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
    {
        "name": "assign_task",
        "description": "직원에게 업무를 지시합니다. 작업 큐에 추가되어 자동 실행됩니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "담당 직원 ID (예: eunseo, doyun, siwoo 등)",
                },
                "title": {
                    "type": "string",
                    "description": "작업 제목",
                },
                "instruction": {
                    "type": "string",
                    "description": "작업 내용 및 지시사항 (상세할수록 좋음)",
                },
            },
            "required": ["employee_id", "title", "instruction"],
        },
    },
    {
        "name": "get_task_status",
        "description": "작업 큐 현황 조회. 대기/진행/완료된 작업 목록과 통계",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "필터 (pending, in_progress, done, failed). 생략 시 전체",
                },
                "limit": {
                    "type": "integer",
                    "description": "가져올 작업 수 (기본 10)",
                },
            },
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

        elif tool_name == "assign_task":
            try:
                from task_queue import create_task
                employee_id = tool_input.get("employee_id", "")
                title = tool_input.get("title", "")
                instruction = tool_input.get("instruction", "")
                if not employee_id or not title:
                    return json.dumps({"error": "employee_id와 title은 필수입니다."}, ensure_ascii=False)
                # 직원 존재 확인
                emp = next((e for e in EMPLOYEES if e["id"] == employee_id), None)
                if not emp:
                    return json.dumps({"error": f"직원 '{employee_id}'을 찾을 수 없습니다."}, ensure_ascii=False)
                task = create_task(
                    assigned_to=employee_id,
                    title=title,
                    instruction=instruction,
                    assigned_by="sujin",
                )
                return json.dumps({
                    "success": True,
                    "task_id": task["task_id"],
                    "message": f"{emp['name']}에게 '{title}' 작업을 지시했습니다. 5분 내 자동 실행됩니다.",
                }, ensure_ascii=False)
            except Exception as ex:
                return json.dumps({"error": f"작업 지시 실패: {str(ex)[:100]}"}, ensure_ascii=False)

        elif tool_name == "get_task_status":
            try:
                from task_queue import get_tasks, get_queue_stats
                status_filter = tool_input.get("status")
                limit = tool_input.get("limit", 10)
                tasks = get_tasks(status=status_filter, limit=limit)
                stats = get_queue_stats()
                result = {
                    "stats": stats,
                    "tasks": [
                        {
                            "task_id": t["task_id"],
                            "title": t["title"],
                            "assigned_to": t["assigned_to"],
                            "status": t["status"],
                            "result": (t.get("result") or "")[:200] if t.get("result") else None,
                            "created_at": t["created_at"],
                        }
                        for t in tasks
                    ],
                }
                return json.dumps(result, ensure_ascii=False)
            except Exception as ex:
                return json.dumps({"error": f"작업 현황 조회 실패: {str(ex)[:100]}"}, ensure_ascii=False)

        else:
            return json.dumps({"error": f"알 수 없는 도구: {tool_name}"}, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"tool 실행 오류: {str(e)[:200]}"}, ensure_ascii=False)


# ─── Claude Tool Use 대화 (multi-turn) ──────────────────
def chat_with_tools(client, system_prompt: str, user_message: str,
                    temperature: float = 0.8, max_tokens: int = 8192) -> tuple[str, str]:
    """
    Claude tool_use를 사용한 대화. 수진이 필요한 데이터를 자율적으로 조회.
    """
    messages = [{"role": "user", "content": user_message}]
    model = "claude-sonnet-4-20250514"

    # 최대 5회 tool use 반복
    last_response = None
    for i in range(5):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=messages,
                tools=SUJIN_TOOLS,
                temperature=temperature,
            )
            last_response = response
        except Exception as e:
            print(f"⚠️ chat_with_tools 호출 실패 (round {i}): {str(e)[:200]}")
            break

        # 텍스트 추출
        text_parts = [b.text for b in response.content if hasattr(b, "text")]
        tool_blocks = [b for b in response.content if b.type == "tool_use"]

        # tool_use가 없으면 → 최종 응답
        if not tool_blocks:
            text = "".join(text_parts).strip()
            if text:
                return text, "claude-sonnet"
            print(f"⚠️ chat_with_tools: 텍스트 비어있음 (stop={response.stop_reason})")
            break

        # tool_use 처리
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in tool_blocks:
            result = execute_tool(block.name, block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })
            print(f"  🔧 tool: {block.name} → {len(result)}자 결과")

        messages.append({"role": "user", "content": tool_results})

        # 텍스트도 함께 있었으면 tool 완료 후 최종 응답 대기
        if text_parts and not tool_blocks:
            text = "".join(text_parts).strip()
            if text:
                return text, "claude-sonnet"

    # 루프 종료 후: 마지막 응답에서 텍스트 추출 시도
    if last_response:
        text = "".join(b.text for b in last_response.content if hasattr(b, "text")).strip()
        if text:
            return text, "claude-sonnet"

    # 최종 시도: tool 포함한 상태로 한번 더 호출
    try:
        print("⚠️ chat_with_tools: 최종 재호출 시도")
        final = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt + "\n\n[지시] 지금까지 조회한 데이터를 바탕으로 대표님께 보고하세요.",
            messages=messages,
            tools=SUJIN_TOOLS,
            temperature=temperature,
        )
        text = "".join(b.text for b in final.content if hasattr(b, "text")).strip()
        if text:
            return text, "claude-sonnet"
        print(f"⚠️ chat_with_tools: 최종 재호출도 텍스트 없음 (stop={final.stop_reason})")
    except Exception as e:
        print(f"⚠️ chat_with_tools 최종 재호출 실패: {str(e)[:200]}")

    return "죄송합니다 대표님, 시스템 데이터 조회 중 문제가 발생했습니다. 다시 한번 말씀해주시겠습니까?", "claude-sonnet"


