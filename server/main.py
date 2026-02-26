"""
DeepRed AI 회사 — FastAPI 백엔드 서버 v3.1
에이전트 고도화 + DB 영구 저장 + AI 기억 시스템
Phase 1: Supabase + 벡터 임베딩 + 대화 맥락 유지
Phase 2: 수진 자율 봇 — Docker lifespan 스케줄러

리팩토링: 모든 엔드포인트가 routes/ 패키지로 분리됨
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ─── 공유 의존성 초기화 ──────────────────────────────────
from deps import (
    load_activity_log_from_db,
    is_db_available, is_claude_available, is_scheduler_available,
    memory, get_available_tools,
    start_scheduler, stop_scheduler,
)

# ─── 라우터 임포트 ──────────────────────────────────────
from routes.core import router as core_router
from routes.chat import router as chat_router
from routes.meeting import router as meeting_router
from routes.collab import router as collab_router
from routes.stats import router as stats_router
from routes.content import router as content_router
from routes.avatar import router as avatar_router
from routes.telegram import router as telegram_router, stop_telegram_polling
from routes.openclaw import router as openclaw_router
from routes.system import router as system_router
from routes.autonomy import router as autonomy_router
from routes.security import router as security_router
from routes.kakao import router as kakao_router


# ─── FastAPI Lifespan (Docker 호환 스케줄러) ──────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작/종료 시 스케줄러 + 텔레그램 관리"""
    print("\n" + "=" * 50)
    print("🏢 DeepRed AI Company Server v3.1")
    print(f"📊 DB: {'Supabase' if is_db_available() else 'In-Memory'}")
    print(f"🧠 Memory: {memory.get_stats()['total_memories']} memories")
    print(f"🤖 Claude: {'Active' if is_claude_available() else 'Fallback to Gemini'}")
    print(f"📦 Tools: {len(get_available_tools())} available")

    # 스케줄러 시작
    if is_scheduler_available():
        print("\n📅 스케줄러 시작...")
        start_scheduler()
        print("🤖 자율 행동 엔진 활성화")
    else:
        print("⚠️ 스케줄러 미사용 (apscheduler 패키지 필요)")

    # 텔레그램 확인
    from notifications import is_telegram_available
    if is_telegram_available():
        print("\n📱 텔레그램 연결 확인됨")
    else:
        print("⚠️ 텔레그램 미설정 (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID 필요)")

    print("=" * 50 + "\n")

    yield  # 서버 가동 중

    # 종료 정리
    stop_scheduler()
    stop_telegram_polling()
    print("⏹ 서버 종료 — 스케줄러 + 텔레그램 정리 완료")


# ─── FastAPI 앱 ──────────────────────────────────────────
app = FastAPI(title="DeepRed AI Backend", version="3.1.0", lifespan=lifespan)

# CORS: 환경변수 기반 동적 설정
_env = os.getenv("ENVIRONMENT", "development")
_default_origins = ["http://localhost:5173", "http://localhost:3000"]
_prod_origins = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []
_all_origins = list(set(_default_origins + [o.strip() for o in _prod_origins if o.strip()]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_all_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── 라우터 등록 ─────────────────────────────────────────
app.include_router(core_router)
app.include_router(chat_router)
app.include_router(meeting_router)
app.include_router(collab_router)
app.include_router(stats_router)
app.include_router(content_router)
app.include_router(avatar_router)
app.include_router(telegram_router)
app.include_router(openclaw_router)
app.include_router(system_router)
app.include_router(autonomy_router)
app.include_router(security_router)
app.include_router(kakao_router)


# ─── 서버 시작 시 초기화 ─────────────────────────────────
load_activity_log_from_db()


# ─── 엔트리포인트 (직접 실행 시) ─────────────────────────
# Docker에서는 lifespan이 자동 처리하므로 여기서 수동 초기화 불필요
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

