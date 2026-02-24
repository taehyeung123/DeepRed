"""
DeepRed v3.0 — Phase 1: Database Module
Supabase REST API 직접 호출 (requests 기반) + InMemory 폴백
supabase pip 패키지 없이 동작
"""

import os
import json
import uuid
import requests
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ─── Supabase REST 클라이언트 ──────────────────────────────
_supabase_available = False


def _get_url():
    return os.getenv("SUPABASE_URL", "").rstrip("/")


def _get_key():
    return os.getenv("SUPABASE_KEY", "")


def _headers():
    """Supabase REST API 공통 헤더"""
    key = _get_key()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _rest_url(table: str) -> str:
    return f"{_get_url()}/rest/v1/{table}"


def _check_supabase() -> bool:
    """Supabase 연결 확인"""
    global _supabase_available
    url = _get_url()
    key = _get_key()
    if not url or not key:
        _supabase_available = False
        return False
    try:
        resp = requests.get(
            f"{url}/rest/v1/",
            headers={"apikey": key},
            timeout=5,
        )
        _supabase_available = resp.status_code < 500
        if _supabase_available:
            print(f"✅ Supabase 연결 성공: {url}")
        return _supabase_available
    except Exception as e:
        print(f"⚠️ Supabase 연결 실패: {e}")
        _supabase_available = False
        return False


def is_db_available() -> bool:
    """DB 사용 가능 여부"""
    if _supabase_available:
        return True
    return _check_supabase()


# ─── REST CRUD 헬퍼 ──────────────────────────────────────
def _insert(table: str, data: dict) -> Optional[dict]:
    """테이블에 데이터 삽입"""
    try:
        resp = requests.post(_rest_url(table), headers=_headers(),
                             json=data, timeout=10)
        if resp.status_code in (200, 201):
            results = resp.json()
            return results[0] if isinstance(results, list) and results else results
        else:
            print(f"⚠️ INSERT {table} 실패: {resp.status_code} {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"⚠️ INSERT {table} 오류: {e}")
        return None


def _select(table: str, params: dict = None, limit: int = 20) -> list[dict]:
    """테이블에서 데이터 조회"""
    try:
        headers = _headers()
        headers["Prefer"] = ""
        p = params or {}
        p["limit"] = limit
        resp = requests.get(_rest_url(table), headers=headers,
                            params=p, timeout=10)
        if resp.status_code == 200:
            return resp.json() if isinstance(resp.json(), list) else []
        return []
    except Exception:
        return []


def _update(table: str, match_col: str, match_val: str, data: dict) -> Optional[dict]:
    """테이블 데이터 업데이트"""
    try:
        url = f"{_rest_url(table)}?{match_col}=eq.{match_val}"
        resp = requests.patch(url, headers=_headers(), json=data, timeout=10)
        if resp.status_code in (200, 204):
            results = resp.json() if resp.text else None
            return results[0] if isinstance(results, list) and results else results
        return None
    except Exception:
        return None


# ─── 인메모리 폴백 스토어 ────────────────────────────────────
class InMemoryStore:
    """Supabase 없을 때 사용하는 인메모리 폴백"""

    def __init__(self):
        self.conversations: dict[str, dict] = {}
        self.work_logs: list[dict] = []
        self.documents: list[dict] = []
        self.max_logs = 200

    def save_conversation(self, employee_id, employee_name, conv_type, messages, conv_id=None):
        cid = conv_id or str(uuid.uuid4())
        self.conversations[cid] = {
            "id": cid, "employee_id": employee_id,
            "employee_name": employee_name, "type": conv_type,
            "messages": messages,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        return cid

    def get_conversation(self, conv_id):
        return self.conversations.get(conv_id)

    def get_conversations_by_employee(self, employee_id, limit=10):
        result = [c for c in self.conversations.values() if c["employee_id"] == employee_id]
        result.sort(key=lambda x: x["updated_at"], reverse=True)
        return result[:limit]

    def save_work_log(self, log_entry):
        lid = str(uuid.uuid4())[:8]
        log_entry["id"] = lid
        log_entry["created_at"] = datetime.now(timezone.utc).isoformat()
        self.work_logs.insert(0, log_entry)
        if len(self.work_logs) > self.max_logs:
            self.work_logs = self.work_logs[:self.max_logs]
        return lid

    def get_work_logs(self, limit=20, employee_id=None, department=None):
        logs = self.work_logs
        if employee_id:
            logs = [l for l in logs if l.get("employee_id") == employee_id]
        if department:
            logs = [l for l in logs if l.get("department") == department]
        return logs[:limit]

    def save_document(self, title, content, doc_type, author_id=None,
                      author_name=None, project=None, tags=None, metadata=None):
        did = str(uuid.uuid4())
        self.documents.insert(0, {
            "id": did, "title": title, "content": content,
            "doc_type": doc_type, "author_id": author_id,
            "author_name": author_name, "project": project,
            "tags": tags or [], "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return did

    def get_documents(self, doc_type=None, project=None, limit=10):
        docs = self.documents
        if doc_type:
            docs = [d for d in docs if d.get("doc_type") == doc_type]
        if project:
            docs = [d for d in docs if d.get("project") == project]
        return docs[:limit]

    def search_documents(self, query, limit=5):
        q = query.lower()
        return [d for d in self.documents
                if q in f"{d.get('title', '')} {d.get('content', '')}".lower()][:limit]


# ─── 통합 DB 인터페이스 ──────────────────────────────────────
_memory_store = InMemoryStore()


class DeepRedDB:
    """Supabase REST / InMemory 통합 DB 인터페이스"""

    @staticmethod
    def save_conversation(employee_id, employee_name, conv_type="chat",
                          messages=None, conv_id=None):
        msgs = messages or []
        if is_db_available():
            data = {
                "employee_id": employee_id,
                "employee_name": employee_name,
                "type": conv_type,
                "messages": json.dumps(msgs, ensure_ascii=False),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            if conv_id:
                _update("conversations", "id", conv_id, data)
                return conv_id
            else:
                data["id"] = str(uuid.uuid4())
                result = _insert("conversations", data)
                if result:
                    return result.get("id", data["id"])
        return _memory_store.save_conversation(employee_id, employee_name, conv_type, msgs, conv_id)

    @staticmethod
    def get_conversation(conv_id):
        if is_db_available():
            results = _select("conversations", {"id": f"eq.{conv_id}"}, limit=1)
            if results:
                item = results[0]
                if isinstance(item.get("messages"), str):
                    item["messages"] = json.loads(item["messages"])
                return item
        return _memory_store.get_conversation(conv_id)

    @staticmethod
    def get_conversations_by_employee(employee_id, limit=10):
        if is_db_available():
            results = _select("conversations", {
                "employee_id": f"eq.{employee_id}",
                "order": "updated_at.desc",
            }, limit=limit)
            for item in results:
                if isinstance(item.get("messages"), str):
                    item["messages"] = json.loads(item["messages"])
            return results
        return _memory_store.get_conversations_by_employee(employee_id, limit)

    @staticmethod
    def save_work_log(employee_id, employee_name, department,
                      action, log_type="report", icon="📋", metadata=None):
        log_entry = {
            "employee_id": employee_id,
            "employee_name": employee_name,
            "department": department,
            "action": action,
            "type": log_type,
            "icon": icon,
        }
        if is_db_available():
            result = _insert("work_logs", log_entry)
            if result:
                return result.get("id", str(uuid.uuid4())[:8])
        return _memory_store.save_work_log(log_entry)

    @staticmethod
    def get_work_logs(limit=20, employee_id=None, department=None):
        if is_db_available():
            params = {"order": "created_at.desc"}
            if employee_id:
                params["employee_id"] = f"eq.{employee_id}"
            if department:
                params["department"] = f"eq.{department}"
            return _select("work_logs", params, limit=limit)
        return _memory_store.get_work_logs(limit, employee_id, department)

    @staticmethod
    def save_document(title, content, doc_type="briefing", author_id=None,
                      author_name=None, project=None, tags=None, metadata=None):
        if is_db_available():
            data = {
                "title": title,
                "content": content[:10000],
                "doc_type": doc_type,
                "author_id": author_id,
                "author_name": author_name,
                "project": project,
            }
            result = _insert("documents", data)
            if result:
                return result.get("id", str(uuid.uuid4()))
        return _memory_store.save_document(title, content, doc_type, author_id,
                                           author_name, project, tags, metadata)

    @staticmethod
    def get_documents(doc_type=None, project=None, limit=10):
        if is_db_available():
            params = {"order": "created_at.desc"}
            if doc_type:
                params["doc_type"] = f"eq.{doc_type}"
            if project:
                params["project"] = f"eq.{project}"
            return _select("documents", params, limit=limit)
        return _memory_store.get_documents(doc_type, project, limit)

    @staticmethod
    def search_documents(query, limit=5):
        if is_db_available():
            params = {
                "or": f"(title.ilike.%{query}%,content.ilike.%{query}%)",
                "order": "created_at.desc",
                "limit": limit,
            }
            return _select("documents", params, limit=limit)
        return _memory_store.search_documents(query, limit)

    @staticmethod
    def get_stats():
        if is_db_available():
            try:
                h = _headers()
                h["Prefer"] = "count=exact"
                h["Range-Unit"] = "items"
                h["Range"] = "0-0"
                stats = {}
                for table in ["conversations", "work_logs", "documents"]:
                    resp = requests.get(_rest_url(table), headers=h,
                                        params={"select": "id"}, timeout=5)
                    cr = resp.headers.get("content-range", "")
                    # content-range: 0-0/5  →  5
                    total = int(cr.split("/")[-1]) if "/" in cr else 0
                    stats[table] = total
                return {"backend": "supabase", **stats}
            except Exception:
                pass
        return {
            "backend": "in-memory",
            "conversations": len(_memory_store.conversations),
            "work_logs": len(_memory_store.work_logs),
            "documents": len(_memory_store.documents),
        }


# 싱글톤
db = DeepRedDB()
