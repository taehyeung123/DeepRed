"""
DeepRed v3.0 — Phase 4: GitHub Code Reader
수진(COO)이 GitHub 리포 코드를 읽을 수 있게 하는 모듈.
Claude 직접 방식 + 인메모리 TTL 캐시로 비용 최적화.
"""

import os
import json
import time
import base64
import urllib.request
import urllib.error
from typing import Optional
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ─── 설정 ─────────────────────────────────────────────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
REPOS = {
    "딥레드": "taehyeung123/DeepRed",
    "deepred": "taehyeung123/DeepRed",
}
API_BASE = "https://api.github.com"

# 코드 관련 키워드 — 이 키워드가 메시지에 있으면 코드 참조 트리거
CODE_KEYWORDS = [
    # 한글
    "코드", "구현", "파일", "버그", "에러", "오류", "함수", "클래스",
    "컴포넌트", "모듈", "서버", "프론트", "백엔드", "엔드포인트",
    "타입", "인터페이스", "훅",
    "딥레드", "레드랭크",
    "소스", "배포", "빌드", "라우터", "라우팅", "페이지", "스타일",
    "데이터베이스", "스키마", "마이그레이션",
    # 영문
    "code", "file", "bug", "error", "function", "class", "component",
    "module", "server", "frontend", "backend", "endpoint", "API",
    "hook", "import", "export", "deploy", "build", "router", "route",
    "database", "DB", "schema", "deepred", "redrank",
    "chat", "messenger", "dashboard", "meeting", "attendance",
    "main.py", "index", "config", "setup",
]

# 코드 파일 확장자 (이 확장자만 읽음)
CODE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".css", ".html",
    ".md", ".yaml", ".yml", ".toml", ".cfg", ".env.example",
    ".sh", ".sql",
}

# 무시할 경로 패턴
IGNORE_PATTERNS = [
    "node_modules/", ".git/", "dist/", "build/", ".next/",
    "__pycache__/", ".vercel/", "package-lock.json",
    ".env", "avatars.json",
]


# ─── TTL 캐시 ──────────────────────────────────────────────
class TTLCache:
    """간단한 인메모리 TTL 캐시"""

    def __init__(self):
        self._cache: dict[str, tuple[float, any]] = {}

    def get(self, key: str, ttl_seconds: int = 1800) -> Optional[any]:
        if key in self._cache:
            ts, value = self._cache[key]
            if time.time() - ts < ttl_seconds:
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value: any):
        self._cache[key] = (time.time(), value)

    def clear(self):
        self._cache.clear()

    def stats(self) -> dict:
        valid = sum(1 for ts, _ in self._cache.values() if time.time() - ts < 3600)
        return {"total_cached": len(self._cache), "valid_entries": valid}


_cache = TTLCache()


# ─── GitHub API 호출 ────────────────────────────────────────
def _github_api(endpoint: str) -> Optional[dict | list]:
    """GitHub API 호출 (인증 헤더 포함)"""
    if not GITHUB_TOKEN:
        print("⚠️ GITHUB_TOKEN이 설정되지 않았습니다.")
        return None

    url = f"{API_BASE}{endpoint}" if endpoint.startswith("/") else endpoint
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DeepRed-Sujin-Bot",
    })

    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"⚠️ GitHub API 오류 {e.code}: {e.read().decode()[:200]}")
        return None
    except Exception as e:
        print(f"⚠️ GitHub 연결 오류: {e}")
        return None


# ─── 코어 함수 ──────────────────────────────────────────────
def fetch_repo_tree(repo: str) -> list[dict]:
    """
    리포 전체 파일 트리 가져오기 (캐시 1시간).
    반환: [{"path": "server/main.py", "size": 69180}, ...]
    """
    cache_key = f"tree:{repo}"
    cached = _cache.get(cache_key, ttl_seconds=3600)
    if cached is not None:
        return cached

    data = _github_api(f"/repos/{repo}/git/trees/main?recursive=1")
    if not data or "tree" not in data:
        # main 대신 master 시도
        data = _github_api(f"/repos/{repo}/git/trees/master?recursive=1")

    if not data or "tree" not in data:
        return []

    files = []
    for item in data["tree"]:
        if item["type"] != "blob":
            continue
        path = item["path"]
        # 무시 패턴 체크
        if any(p in path for p in IGNORE_PATTERNS):
            continue
        # 코드 파일만
        ext = os.path.splitext(path)[1].lower()
        if ext in CODE_EXTENSIONS or path in ("Dockerfile", "Makefile", "vercel.json"):
            files.append({
                "path": path,
                "size": item.get("size", 0),
            })

    _cache.set(cache_key, files)
    return files


def fetch_file_content(repo: str, file_path: str, max_size: int = 50000) -> Optional[str]:
    """
    특정 파일 내용 읽기 (캐시 30분).
    max_size 초과 파일은 잘라서 반환.
    """
    cache_key = f"file:{repo}:{file_path}"
    cached = _cache.get(cache_key, ttl_seconds=1800)
    if cached is not None:
        return cached

    data = _github_api(f"/repos/{repo}/contents/{file_path}")
    if not data or "content" not in data:
        return None

    try:
        content = base64.b64decode(data["content"]).decode("utf-8")
        if len(content) > max_size:
            content = content[:max_size] + f"\n\n... (파일이 너무 커서 {max_size}자까지만 표시)"
        _cache.set(cache_key, content)
        return content
    except Exception as e:
        print(f"⚠️ 파일 디코딩 오류: {e}")
        return None


def search_relevant_files(repo: str, query: str, max_files: int = 3) -> list[dict]:
    """
    질문과 관련된 파일 자동 선별.
    파일명/경로 기반 키워드 매칭으로 선별 후 내용 로드.
    
    반환: [{"path": "server/main.py", "content": "...", "relevance": "높음"}, ...]
    """
    tree = fetch_repo_tree(repo)
    if not tree:
        return []

    query_lower = query.lower()

    # 쿼리에서 키워드 추출
    keywords = []
    keyword_map = {
        # 파일/디렉토리 관련
        "채팅": ["chat", "messenger", "message"],
        "대화": ["chat", "messenger", "message", "conversation"],
        "수진": ["sujin", "chat_sujin", "memory"],
        "메신저": ["messenger", "chat", "message"],
        "대시보드": ["dashboard", "Dashboard"],
        "회의": ["meeting", "Meeting"],
        "브리핑": ["briefing"],
        "협업": ["collaborate", "collaboration"],
        "출근": ["attendance", "Attendance", "stats"],
        "근태": ["attendance", "stats", "tracker"],
        "프로필": ["avatar", "profile", "Avatar"],
        "아바타": ["avatar", "Avatar", "avatarParts"],
        "사이드바": ["sidebar", "Sidebar"],
        "헤더": ["header", "Header"],
        "조직도": ["organization", "OrganizationChart"],
        "업무": ["task", "Tasks", "deliverable"],
        "산출물": ["deliverable", "Deliverables"],
        "공지": ["announcement", "Announcements"],
        "설정": ["system", "System", "config"],
        "라우터": ["router", "llm_router", "route"],
        "메모리": ["memory", "Memory"],
        "데이터베이스": ["database", "db", "supabase"],
        "DB": ["database", "db"],
        "스케줄": ["scheduler", "schedule"],
        "도구": ["tools", "tool"],
        "통계": ["stats", "tracker", "statistics"],
        "서버": ["server", "main.py", "api"],
        "백엔드": ["server", "main.py", "api"],
        "프론트": ["src/app", "components", "pages"],
        "컴포넌트": ["components"],
        "페이지": ["pages"],
        "훅": ["hooks", "use"],
        "스타일": ["css", "style", "index.css"],
        "구조": ["main", "app", "index"],
        "배포": ["vercel", "deploy", "docker"],
        "환경": ["env", "config"],
        "API": ["api", "endpoint"],
        "엔드포인트": ["api", "endpoint", "route"],
    }

    for kr_key, en_vals in keyword_map.items():
        if kr_key in query_lower or kr_key.lower() in query_lower:
            keywords.extend(en_vals)

    # 영문 키워드 직접 매칭
    for word in query.split():
        w = word.strip("?!.,").lower()
        if len(w) >= 2 and w.isascii():
            keywords.append(w)

    if not keywords:
        # 폴백: 주요 파일들 반환
        keywords = ["main", "app", "index"]

    # 파일 스코어링
    scored_files = []
    for f in tree:
        path_lower = f["path"].lower()
        score = 0
        for kw in keywords:
            if kw.lower() in path_lower:
                score += 1
                # 파일명에 직접 매칭되면 보너스
                basename = os.path.basename(f["path"]).lower()
                if kw.lower() in basename:
                    score += 2
        if score > 0:
            scored_files.append((score, f))

    scored_files.sort(key=lambda x: x[0], reverse=True)

    # 상위 N개 파일의 내용 로드
    results = []
    for score, f in scored_files[:max_files]:
        content = fetch_file_content(repo, f["path"], max_size=8000)
        if content:
            results.append({
                "path": f["path"],
                "content": content,
                "size": f["size"],
                "relevance": "높음" if score >= 3 else "보통",
            })

    return results


def should_search_code(message: str) -> bool:
    """메시지가 코드 참조가 필요한지 판단"""
    msg_lower = message.lower()
    return any(kw.lower() in msg_lower for kw in CODE_KEYWORDS)


def get_code_context(message: str, max_tokens_approx: int = 3000) -> str:
    """
    메시지 기반으로 코드 컨텍스트 생성.
    build_context_for_claude()에서 호출.
    
    반환: Claude에 전달할 [코드 참조] 텍스트
    """
    if not should_search_code(message):
        return ""

    if not GITHUB_TOKEN:
        return ""

    parts = ["[코드 참조]"]
    total_chars = 0

    for repo_name, repo_path in REPOS.items():
        files = search_relevant_files(repo_path, message, max_files=3)
        if not files:
            continue

        parts.append(f"\n📂 {repo_name} ({repo_path})")
        for f in files:
            content = f["content"]
            # 토큰 제한 관리 (대략 1토큰 = 3~4자)
            remaining = (max_tokens_approx * 3) - total_chars
            if remaining <= 200:
                parts.append("... (토큰 제한으로 추가 파일 생략)")
                break
            if len(content) > remaining:
                content = content[:remaining] + "\n... (잘림)"

            parts.append(f"\n--- {f['path']} (관련도: {f['relevance']}) ---")
            parts.append(content)
            total_chars += len(content)

    return "\n".join(parts) if len(parts) > 1 else ""


def get_repo_overview(repo_key: str = "딥레드") -> str:
    """리포 전체 파일 구조 요약 (질문: '구조 알려줘' 같은 경우)"""
    repo = REPOS.get(repo_key, REPOS.get("딥레드"))
    if not repo:
        return ""

    tree = fetch_repo_tree(repo)
    if not tree:
        return "⚠️ GitHub 리포 접근 실패"

    # 디렉토리별 그룹핑
    dirs: dict[str, list[str]] = {}
    for f in tree:
        parts = f["path"].split("/")
        dir_name = parts[0] if len(parts) > 1 else "(root)"
        filename = parts[-1]
        if dir_name not in dirs:
            dirs[dir_name] = []
        dirs[dir_name].append(filename)

    lines = [f"📂 {repo} — 파일 구조 ({len(tree)}개 파일)"]
    for dir_name, files in sorted(dirs.items()):
        lines.append(f"\n  📁 {dir_name}/ ({len(files)}개)")
        for f in files[:8]:
            lines.append(f"    - {f}")
        if len(files) > 8:
            lines.append(f"    ... (+{len(files) - 8}개)")

    return "\n".join(lines)


def get_cache_stats() -> dict:
    """캐시 통계"""
    return {
        "repos_configured": list(REPOS.keys()),
        "token_set": bool(GITHUB_TOKEN),
        **_cache.stats(),
    }
