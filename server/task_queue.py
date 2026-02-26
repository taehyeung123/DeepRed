"""
DeepRed v3.1 — 직원 작업 큐 시스템 (Task Queue)
수진(COO)이 직원에게 업무를 지시하고, 스케줄러가 자동 처리
"""

import uuid
import threading
from datetime import datetime
from typing import Optional


_lock = threading.Lock()
_task_queue: list[dict] = []
_max_tasks = 200


# ─── 작업 생성 ────────────────────────────────────────────
def create_task(
    assigned_to: str,
    title: str,
    instruction: str,
    assigned_by: str = "sujin",
) -> dict:
    """새 작업 생성하여 큐에 추가"""
    with _lock:
        task = {
            "task_id": f"task-{uuid.uuid4().hex[:8]}",
            "assigned_to": assigned_to,
            "assigned_by": assigned_by,
            "title": title,
            "instruction": instruction,
            "status": "pending",       # pending → in_progress → done / failed
            "result": None,
            "model_used": None,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "error": None,
        }
        _task_queue.append(task)

        # 최대 개수 초과 시 가장 오래된 완료 작업 제거
        if len(_task_queue) > _max_tasks:
            completed = [t for t in _task_queue if t["status"] in ("done", "failed")]
            if completed:
                _task_queue.remove(completed[0])

        print(f"📋 작업 생성: [{title}] → {assigned_to}")
        return task


# ─── 작업 조회 ────────────────────────────────────────────
def get_task(task_id: str) -> Optional[dict]:
    """특정 작업 조회"""
    with _lock:
        return next((t for t in _task_queue if t["task_id"] == task_id), None)


def get_tasks(
    status: str = None,
    assigned_to: str = None,
    limit: int = 20,
) -> list[dict]:
    """작업 목록 조회 (필터링 가능)"""
    with _lock:
        tasks = list(_task_queue)

    if status:
        tasks = [t for t in tasks if t["status"] == status]
    if assigned_to:
        tasks = [t for t in tasks if t["assigned_to"] == assigned_to]

    return tasks[-limit:]


def get_queue_stats() -> dict:
    """큐 통계"""
    with _lock:
        total = len(_task_queue)
        by_status = {}
        for t in _task_queue:
            by_status[t["status"]] = by_status.get(t["status"], 0) + 1
        return {
            "total": total,
            "by_status": by_status,
            "pending": by_status.get("pending", 0),
            "in_progress": by_status.get("in_progress", 0),
            "done": by_status.get("done", 0),
            "failed": by_status.get("failed", 0),
        }


# ─── 작업 실행 엔진 ───────────────────────────────────────
def _execute_task(task: dict, employees: list) -> dict:
    """
    단일 작업 실행: 직원 AI에게 전달하고 결과 수집.
    llm_router.route_call()로 Tier별 자동 라우팅.
    """
    employee_id = task["assigned_to"]
    employee = next((e for e in employees if e["id"] == employee_id), None)

    if not employee:
        task["status"] = "failed"
        task["error"] = f"직원 '{employee_id}' 찾을 수 없음"
        task["completed_at"] = datetime.now().isoformat()
        return task

    task["status"] = "in_progress"
    task["started_at"] = datetime.now().isoformat()

    try:
        from llm_router import route_call

        # 직원 성격 기반 시스템 프롬프트 구성
        system_prompt = (
            f"당신은 {employee['name']}({employee['role']})입니다. "
            f"부서: {employee.get('department_name', '')}. "
            f"스킬: {', '.join(employee.get('skills', [])[:5])}. "
            f"성격: {employee.get('personality', '')[:100]}. "
            f"\n\n수진 총괄이사의 업무 지시를 받았습니다. "
            f"업무를 충실히 수행하고 결과를 보고하세요. "
            f"보고 형식: 마크다운, 핵심 요약 포함."
        )

        user_message = (
            f"[업무 지시]\n"
            f"제목: {task['title']}\n"
            f"내용: {task['instruction']}\n\n"
            f"위 업무를 수행하고 결과를 보고해주세요."
        )

        result = route_call(
            employee_id=employee_id,
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.7,
            max_tokens=2000,
        )

        task["status"] = "done"
        task["result"] = result.get("response", "")
        task["model_used"] = result.get("model", "unknown")
        task["completed_at"] = datetime.now().isoformat()

        print(f"  ✅ 작업 완료: [{task['title']}] by {employee['name']} ({task['model_used']})")

    except Exception as e:
        task["status"] = "failed"
        task["error"] = str(e)[:300]
        task["completed_at"] = datetime.now().isoformat()
        print(f"  ❌ 작업 실패: [{task['title']}] — {str(e)[:100]}")

    return task


def process_pending_tasks(employees: list, max_per_batch: int = 3) -> dict:
    """
    대기(pending) 작업을 순차 실행. 스케줄러에서 5분마다 호출.
    max_per_batch: 한 번에 처리할 최대 작업 수 (API 비용 제한용)
    """
    with _lock:
        pending = [t for t in _task_queue if t["status"] == "pending"]

    if not pending:
        return {"processed": 0, "message": "대기 작업 없음"}

    batch = pending[:max_per_batch]
    results = []

    for task in batch:
        result = _execute_task(task, employees)
        results.append({
            "task_id": result["task_id"],
            "title": result["title"],
            "status": result["status"],
            "assigned_to": result["assigned_to"],
        })

        # 완료된 작업 → 활동 로그 + 수진 보고
        if result["status"] == "done":
            try:
                from proactive import add_proactive_message
                from deps import add_activity_log

                employee = next((e for e in employees if e["id"] == result["assigned_to"]), None)
                emp_name = employee["name"] if employee else result["assigned_to"]
                dept = employee.get("department", "unknown") if employee else "unknown"

                # 활동 로그
                add_activity_log(
                    result["assigned_to"], emp_name, dept,
                    f"작업 완료: {result['title']}", "task", "✅"
                )

                # 수진에게 완료 보고
                report = (
                    f"📋 작업 완료 보고\n\n"
                    f"담당: {emp_name}\n"
                    f"제목: {result['title']}\n"
                    f"결과: {(result.get('result', '') or '')[:200]}"
                )
                add_proactive_message("sujin", "수진", report, "task_complete", "✅")

            except Exception as e:
                print(f"  ⚠️ 작업 완료 보고 실패: {e}")

    return {
        "processed": len(results),
        "results": results,
        "remaining_pending": len(pending) - len(batch),
    }
