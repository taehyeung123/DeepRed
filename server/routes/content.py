"""
DeepRed v3.0 — Content Routes
공지사항 CRUD, 좋아요, 문서 조회/검색, 글로벌 검색, 기억/DB 통계
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from deps import (
    EMPLOYEES, announcements, db, memory,
    add_activity_log,
)

router = APIRouter(prefix="/api", tags=["content"])


class AnnouncementRequest(BaseModel):
    title: str
    content: str
    type: str = "notice"  # notice | mvp | update
    author_name: str = "CEO"
    pinned: bool = False


# ─── 공지사항 ────────────────────────────────────
@router.get("/announcements")
def list_announcements(limit: int = 30):
    """공지사항 목록 조회"""
    return {"announcements": announcements[:limit], "total": len(announcements)}


@router.post("/announcements")
def create_announcement(req: AnnouncementRequest):
    """공지사항 생성"""
    entry = {
        "id": str(uuid.uuid4())[:8],
        "type": req.type,
        "title": req.title,
        "content": req.content,
        "authorName": req.author_name,
        "timestamp": datetime.now().isoformat(),
        "likes": 0,
        "comments": 0,
        "pinned": req.pinned,
    }
    announcements.insert(0, entry)
    if len(announcements) > 200:
        announcements.pop()

    add_activity_log(
        "ceo", req.author_name, "control",
        f"공지사항 등록: {req.title}", "report", "📢"
    )

    return entry


@router.post("/announcements/{ann_id}/like")
def like_announcement(ann_id: str):
    """공지사항 좋아요 토글"""
    for ann in announcements:
        if ann["id"] == ann_id:
            ann["likes"] = ann.get("likes", 0) + 1
            return {"id": ann_id, "likes": ann["likes"]}
    raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다.")


# ─── 글로벌 검색 ──────────────────────────────────
@router.get("/search")
def global_search(q: str = "", limit: int = 10):
    """직원, 문서, 공지사항 통합 검색"""
    if not q.strip():
        return {"results": [], "total": 0}

    query = q.strip().lower()
    results = []

    for emp in EMPLOYEES:
        if query in emp["name"].lower() or query in emp["role"].lower() or query in emp.get("department_name", "").lower():
            results.append({
                "type": "employee",
                "id": emp["id"],
                "title": emp["name"],
                "subtitle": f"{emp['role']} · {emp.get('department_name', emp['department'])}",
                "icon": "👤",
            })

    for ann in announcements:
        if query in ann.get("title", "").lower() or query in ann.get("content", "").lower():
            results.append({
                "type": "announcement",
                "id": ann["id"],
                "title": ann["title"],
                "subtitle": ann.get("content", "")[:60],
                "icon": "📢",
            })

    try:
        docs = db.search_documents(query, limit=5)
        for doc in docs:
            results.append({
                "type": "document",
                "id": doc.get("id", ""),
                "title": doc.get("title", "문서"),
                "subtitle": doc.get("content", "")[:60],
                "icon": "📄",
            })
    except Exception:
        pass

    return {"results": results[:limit], "total": len(results)}


# ─── 문서 조회 ───────────────────────────────────
@router.get("/documents")
def get_documents(doc_type: str = None, project: str = None, limit: int = 10):
    """문서 조회"""
    return {"documents": db.get_documents(doc_type, project, limit)}


@router.get("/documents/search")
def search_documents(query: str, limit: int = 5):
    """문서 검색"""
    return {"query": query, "results": db.search_documents(query, limit)}


# ─── 기억/DB 통계 ────────────────────────────────
@router.get("/memory/search")
def search_memory(query: str, limit: int = 5, source_type: str = None):
    """기억 검색 — 유사도 기반"""
    results = memory.recall(query, limit=limit, source_type=source_type)
    return {"query": query, "results": results}


@router.get("/memory/stats")
def memory_stats():
    """기억 시스템 통계"""
    return memory.get_stats()


@router.get("/db/stats")
def database_stats():
    """DB 통계"""
    return db.get_stats()
