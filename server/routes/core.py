"""
DeepRed v3.0 — Core Routes
health, employees, projects
"""

from datetime import datetime
from fastapi import APIRouter

from deps import (
    EMPLOYEES, PROJECTS, project_assignments, activity_log,
    db, memory, api_key, get_router_stats,
)

router = APIRouter(prefix="/api", tags=["core"])


@router.get("/health")
def health():
    db_stats = db.get_stats()
    mem_stats = memory.get_stats()
    result = {
        "status": "ok",
        "version": "3.0.0",
        "employees": len(EMPLOYEES),
        "api_key_set": bool(api_key),
        "projects": list(PROJECTS.keys()),
        "activity_log_count": len(activity_log),
        "database": db_stats,
        "memory": mem_stats,
        "llm_router": get_router_stats(),
    }
    try:
        from github_reader import get_cache_stats
        result["github_reader"] = get_cache_stats()
    except Exception:
        result["github_reader"] = {"status": "not loaded"}
    return result


@router.get("/employees")
def get_employees():
    return EMPLOYEES


@router.get("/projects")
def get_projects():
    result = []
    for key, proj in PROJECTS.items():
        assigned = project_assignments.get(key, [])
        assigned_employees = [e for e in EMPLOYEES if e["id"] in assigned]
        result.append({
            **proj,
            "assigned_count": len(assigned_employees),
            "assigned_employees": [{"id": e["id"], "name": e["name"], "role": e["role"]} for e in assigned_employees],
        })
    return result
