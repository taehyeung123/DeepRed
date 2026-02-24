"""
DeepRed v3.0 — Phase 2: Dual-Engine Memory System
Gemini(무료) = 메모리 엔진 (컨텍스트 압축 + 세션 요약 + 기억 검색)
Claude(유료) = 대화 엔진 (압축된 컨텍스트만 수신)
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


# ─── 임베딩 생성 ──────────────────────────────────────────
def _get_embedding(text: str) -> Optional[list[float]]:
    """Gemini 임베딩 API로 벡터 생성 (실패 시 None)"""
    try:
        import google.generativeai as genai
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None
        genai.configure(api_key=api_key)
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return result["embedding"]
    except Exception as e:
        print(f"⚠️ 임베딩 생성 실패: {e}")
        return None


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """코사인 유사도 계산"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x ** 2 for x in a) ** 0.5
    norm_b = sum(x ** 2 for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ─── 메모리 스토어 ─────────────────────────────────────────
class MemoryStore:
    """
    AI 에이전트 기억 관리
    - 대화 요약 저장
    - 업무 결과물 색인
    - 유사도 기반 기억 검색
    """

    def __init__(self):
        self._memories: list[dict] = []
        self._max_memories = 500

    def remember(self, content: str, source_type: str = "chat",
                 employee_id: str = None, metadata: dict = None) -> str:
        """
        기억 저장
        - content: 기억할 내용
        - source_type: chat, meeting, briefing, collaboration, document
        - employee_id: 관련 직원 ID
        - metadata: 추가 컨텍스트
        """
        memory_id = hashlib.md5(f"{content[:100]}{datetime.now().isoformat()}".encode()).hexdigest()[:12]

        embedding = _get_embedding(content[:2000])

        memory = {
            "id": memory_id,
            "content": content,
            "source_type": source_type,
            "employee_id": employee_id,
            "embedding": embedding,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self._memories.insert(0, memory)

        if len(self._memories) > self._max_memories:
            self._memories = self._memories[:self._max_memories]

        # Supabase에도 저장 시도
        self._persist_to_db(memory)

        return memory_id

    def recall(self, query: str, limit: int = 5, source_type: str = None,
               employee_id: str = None) -> list[dict]:
        """
        관련 기억 검색
        1. 임베딩 유사도 (사용 가능 시)
        2. 키워드 매칭 (폴백)
        """
        results = self._search_db(query, limit, source_type, employee_id)
        if results:
            return results

        query_embedding = _get_embedding(query[:500])

        candidates = self._memories
        if source_type:
            candidates = [m for m in candidates if m.get("source_type") == source_type]
        if employee_id:
            candidates = [m for m in candidates if m.get("employee_id") == employee_id]

        if query_embedding:
            scored = []
            for mem in candidates:
                if mem.get("embedding"):
                    score = _cosine_similarity(query_embedding, mem["embedding"])
                    scored.append((score, mem))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [
                {
                    "id": m["id"],
                    "content": m["content"],
                    "source_type": m["source_type"],
                    "employee_id": m.get("employee_id"),
                    "score": round(s, 4),
                    "created_at": m["created_at"],
                }
                for s, m in scored[:limit]
            ]

        # 임베딩 불가능 시 키워드 폴백
        query_lower = query.lower()
        keyword_results = []
        for mem in candidates:
            content_lower = mem["content"].lower()
            if query_lower in content_lower:
                keyword_results.append({
                    "id": mem["id"],
                    "content": mem["content"],
                    "source_type": mem["source_type"],
                    "employee_id": mem.get("employee_id"),
                    "score": 0.5,
                    "created_at": mem["created_at"],
                })
        return keyword_results[:limit]

    def get_agent_context(self, employee_id: str, limit: int = 5) -> str:
        """
        특정 직원의 최근 기억을 요약 텍스트로 반환
        → AI 프롬프트에 주입하여 대화 연속성 확보
        """
        memories = self.recall("", limit=limit, employee_id=employee_id)
        if not memories:
            return ""

        context_lines = []
        for mem in memories:
            date_str = mem.get("created_at", "")[:10]
            context_lines.append(f"[{date_str}] {mem['content'][:200]}")

        return "\n".join(context_lines)

    def summarize_conversation(self, messages: list[dict], employee_name: str = "") -> str:
        """
        대화 내용을 요약하여 기억으로 저장할 텍스트 생성
        (Gemini 없이 로컬에서 처리)
        """
        if not messages:
            return ""

        parts = []
        for msg in messages[-10:]:
            sender = "CEO" if msg.get("isUser") or msg.get("isMe") else msg.get("name", employee_name)
            content = msg.get("content", "")[:100]
            parts.append(f"{sender}: {content}")

        summary = f"[대화 요약 - {employee_name}]\n" + "\n".join(parts)
        return summary

    def _persist_to_db(self, memory: dict):
        """Supabase에 기억 저장 시도 (실패 시 무시)"""
        try:
            from database import db
            db.save_document(
                title=f"Memory: {memory['source_type']}",
                content=memory["content"][:5000],
                doc_type="memory",
                author_id=memory.get("employee_id"),
                metadata={
                    "memory_id": memory["id"],
                    "source_type": memory["source_type"],
                }
            )
        except Exception:
            pass

    def _search_db(self, query: str, limit: int, source_type: str = None,
                   employee_id: str = None) -> list[dict]:
        """Supabase에서 검색 시도"""
        try:
            from database import db, is_db_available
            if not is_db_available():
                return []
            results = db.search_documents(query, limit=limit)
            return [
                {
                    "id": r.get("id", ""),
                    "content": r.get("content", ""),
                    "source_type": r.get("doc_type", ""),
                    "employee_id": r.get("author_id"),
                    "score": 0.7,
                    "created_at": r.get("created_at", ""),
                }
                for r in results
            ]
        except Exception:
            return []

    def get_stats(self) -> dict:
        """기억 시스템 통계"""
        total = len(self._memories)
        with_embedding = sum(1 for m in self._memories if m.get("embedding"))
        by_type = {}
        for m in self._memories:
            t = m.get("source_type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1

        return {
            "total_memories": total,
            "with_embedding": with_embedding,
            "without_embedding": total - with_embedding,
            "by_source_type": by_type,
        }


# ─── Gemini 메모리 엔진 (이중 엔진 핵심) ────────────────────

def build_context_for_claude(employee_id: str, current_message: str,
                              full_history: list = None) -> str:
    """
    Gemini(무료)가 전체 대화를 분석 → Claude에 보낼 압축 컨텍스트 생성
    
    프로세스:
    1. 과거 세션 요약 로드 (DB/메모리)
    2. 관련 기억 검색 (임베딩 유사도)
    3. 전체 히스토리를 Gemini에 전달 → 핵심 맥락 추출
    → ~500토큰 컨텍스트 반환
    """
    parts = []
    
    # 1. 과거 세션 요약 로드
    session_summaries = memory.recall(
        current_message, limit=5, source_type="session_summary", employee_id=employee_id
    )
    if session_summaries:
        parts.append("[과거 대화 요약]")
        for s in session_summaries:
            parts.append(f"- {s['content'][:200]}")
    
    # 2. 관련 기억 검색 (임베딩)
    related_memories = memory.recall(
        current_message, limit=3, source_type="chat", employee_id=employee_id
    )
    if related_memories:
        parts.append("\n[관련 기억]")
        for m in related_memories:
            parts.append(f"- {m['content'][:150]}")
    
    # 2.5. 코드 컨텍스트 (GitHub 리포 참조)
    try:
        from github_reader import get_code_context
        code_ctx = get_code_context(current_message)
        if code_ctx:
            parts.append(f"\n{code_ctx}")
    except Exception as e:
        print(f"⚠️ 코드 컨텍스트 로드 실패: {e}")
    
    # 3. 히스토리가 짧으면 (15개 이하) 압축 없이 직접 전달
    history = full_history or []
    if len(history) <= 15:
        if history:
            parts.append("\n[최근 대화]")
            for msg in history:
                sender = "사장님" if msg.get("isUser") else msg.get("name", "직원")
                parts.append(f"{sender}: {msg.get('content', '')[:200]}")
        return "\n".join(parts) if parts else ""
    
    # 4. 히스토리가 긴 경우: Gemini로 압축
    history_text = ""
    for msg in history:
        sender = "사장님" if msg.get("isUser") else msg.get("name", "직원")
        history_text += f"\n{sender}: {msg.get('content', '')[:200]}"
    
    compress_prompt = """다음은 CEO(사장님)와 직원의 대화 내역입니다.
이 대화의 핵심 맥락을 500자 이내로 정리해주세요.

정리 규칙:
1. 주요 논의 주제와 결론
2. CEO가 지시한 사항
3. 아직 해결 안 된 이슈
4. 약속이나 일정

간결하게, 핵심만 추출하세요."""
    
    try:
        from llm_router import call_gemini
        compressed = call_gemini(compress_prompt, history_text[:8000], temperature=0.3, max_tokens=500)
        if compressed and not compressed.startswith("⚠️"):
            parts.append(f"\n[대화 맥락 요약]\n{compressed}")
        else:
            # Gemini 실패 시: 최근 20개만 직접 전달
            parts.append("\n[최근 대화]")
            for msg in history[-20:]:
                sender = "사장님" if msg.get("isUser") else msg.get("name", "직원")
                parts.append(f"{sender}: {msg.get('content', '')[:150]}")
    except Exception as e:
        print(f"⚠️ 컨텍스트 압축 실패: {e}")
        # 폴백: 최근 20개만
        parts.append("\n[최근 대화]")
        for msg in history[-20:]:
            sender = "사장님" if msg.get("isUser") else msg.get("name", "직원")
            parts.append(f"{sender}: {msg.get('content', '')[:150]}")
    
    return "\n".join(parts) if parts else ""


def summarize_session(employee_id: str, messages: list,
                      employee_name: str = "") -> str:
    """
    대화 세션 종료 시 Gemini(무료)로 요약 생성 → 메모리에 저장
    다음 대화에서 build_context_for_claude()가 이 요약을 활용
    """
    if not messages or len(messages) < 3:
        return ""
    
    conversation_text = ""
    for msg in messages[-30:]:
        sender = "CEO" if msg.get("isUser") else msg.get("name", employee_name)
        conversation_text += f"\n{sender}: {msg.get('content', '')[:200]}"
    
    summary_prompt = f"""다음은 CEO와 {employee_name}의 대화입니다.
이 대화의 핵심을 2~3문장으로 요약해주세요.
주요 결정사항, 지시사항, 논의 주제를 포함하세요."""
    
    try:
        from llm_router import call_gemini
        summary = call_gemini(summary_prompt, conversation_text[:5000],
                              temperature=0.3, max_tokens=200)
        if summary and not summary.startswith("⚠️"):
            # 세션 요약으로 저장
            memory.remember(
                content=f"[세션 요약] {summary}",
                source_type="session_summary",
                employee_id=employee_id,
                metadata={"message_count": len(messages)}
            )
            return summary
    except Exception as e:
        print(f"⚠️ 세션 요약 실패: {e}")
    
    # Gemini 실패 시 로컬 요약 폴백
    fallback = memory.summarize_conversation(messages, employee_name)
    memory.remember(
        content=fallback,
        source_type="session_summary",
        employee_id=employee_id,
    )
    return fallback


# 싱글톤 인스턴스
memory = MemoryStore()
