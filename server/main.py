"""
DeepRed AI 회사 — FastAPI 백엔드 서버 v3.0
에이전트 고도화 + DB 영구 저장 + AI 기억 시스템
Phase 1: Supabase + 벡터 임베딩 + 대화 맥락 유지

리팩토링: 모든 엔드포인트가 routes/ 패키지로 분리됨
"""

import os
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


# ─── FastAPI 앱 ──────────────────────────────────────────
app = FastAPI(title="DeepRed AI Backend", version="3.0.0")

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


# ─── 서버 시작 시 초기화 ─────────────────────────────────
load_activity_log_from_db()


# ─── 엔트리포인트 ────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 50)
    print("🏢 DeepRed AI Company Server v3.0")
    print(f"📊 DB: {'Supabase' if is_db_available() else 'In-Memory'}")
    print(f"🧠 Memory: {memory.get_stats()['total_memories']} memories")
    print(f"🤖 Claude: {'Active' if is_claude_available() else 'Fallback to Gemini'}")
    print(f"📦 Tools: {len(get_available_tools())} available")

    # 스케줄러 시작 (자율 행동 포함)
    if is_scheduler_available():
        print("\n📅 스케줄러 시작...")
        start_scheduler()
        print("🤖 자율 행동 엔진 활성화 (30분 간격)")
    else:
        print("⚠️ 스케줄러 미사용 (apscheduler 패키지 필요)")

    # 텔레그램 설정 확인
    from notifications import is_telegram_available
    if is_telegram_available():
        print("\n📱 텔레그램 연결 확인됨 (polling은 Oracle 서버에서 처리)")
        print("   웹 채팅 → 텔레그램 동기화 활성")
    else:
        print("⚠️ 텔레그램 미설정 (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID 필요)")

    print("=" * 50 + "\n")
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        stop_scheduler()
        stop_telegram_polling()
