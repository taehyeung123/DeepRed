"""
DeepRed AI 회사 — FastAPI 백엔드 서버 v3.0
에이전트 고도화 + DB 영구 저장 + AI 기억 시스템
Phase 1: Supabase + 벡터 임베딩 + 대화 맥락 유지
"""

import os
import json
import time
import random
import uuid
import subprocess
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import google.generativeai as genai

# Phase 1: DB + Memory 모듈
from database import db, is_db_available
from memory import memory

# Phase 2: LLM 라우터 (Claude COO)
from llm_router import route_call, get_router_stats, is_claude_available

# Phase 3: 자율 에이전트
from scheduler import start_scheduler, stop_scheduler, run_job_now, get_scheduler_status, is_scheduler_available
from tools import get_available_tools, run_tool
from notifications import notifier
from stats_tracker import StatsTracker

api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

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


# ─── 타입 ───────────────────────────────────────────────
class ChatRequest(BaseModel):
    employee_id: str
    employee_name: str
    employee_role: str
    message: str
    history: list[dict] = []


class GroupChatRequest(BaseModel):
    message: str
    history: list[dict] = []


class MeetingRequest(BaseModel):
    topic: str


class CollaborateRequest(BaseModel):
    task: str
    project: str = ""


class AssignRequest(BaseModel):
    project: str
    employee_ids: list[str]


class OpenClawChatRequest(BaseModel):
    message: str
    session_id: str = "web-main"


# ─── 직원 데이터 (고도화) ────────────────────────────────
EMPLOYEES = [
    {
        "id": "sujin", "name": "수진", "role": "총괄이사",
        "department": "control", "department_name": "컨트롤 타워",
        "personality": "전 부서 업무 조율, 일일 CEO 브리핑 담당. 냉철하고 체계적. '사장님, 보고드립니다.' 스타일. 항상 전체 그림을 본다.",
        "skills": ["업무 조율", "브리핑", "의사결정 지원", "리소스 배분", "위기 관리"],
        "projects": ["댕냥", "레드랭크"],
        "collaborates_with": ["planning", "security", "automation", "data"],
    },
    {
        "id": "minsu", "name": "민수", "role": "기획관",
        "department": "planning", "department_name": "기획실",
        "personality": "데이터 기반 Product Planner. 로드맵과 스프린트 계획 전문. 논리적이고 꼼꼼. 항상 근거를 댄다.",
        "skills": ["로드맵 수립", "스프린트 계획", "사용자 스토리", "기능 기획서", "우선순위 매트릭스"],
        "projects": ["댕냥", "레드랭크"],
        "collaborates_with": ["research", "data", "design"],
    },
    {
        "id": "taehyun", "name": "태현", "role": "보안관",
        "department": "security", "department_name": "보안 요새",
        "personality": "편집증적 보안 책임자. API 키 노출 감시, OWASP Top 10 점검. 의심이 많고 신중하다. '보안에 타협은 없습니다.'",
        "skills": ["취약점 스캔", "API 키 관리", "Firebase 보안 규칙", "침투 테스트", "컴플라이언스"],
        "projects": ["댕냥", "레드랭크"],
        "collaborates_with": ["automation", "control"],
    },
    {
        "id": "seoyun", "name": "서윤", "role": "디자이너",
        "department": "design", "department_name": "디자인 스튜디오",
        "personality": "UI/UX 설계 전문. 디자인 시스템 덕후. 접근성(WCAG) 챔피언. 감성적이면서도 사용자 중심적. '예쁜 건 기본이고, 쓰기 편해야죠.'",
        "skills": ["UI/UX 설계", "디자인 시스템", "프로토타입", "접근성 점검", "A/B 테스트 디자인"],
        "projects": ["댕냥", "레드랭크"],
        "collaborates_with": ["planning", "content", "marketing"],
    },
    {
        "id": "hajun", "name": "하준", "role": "콘텐츠PD",
        "department": "content", "department_name": "콘텐츠 공방",
        "personality": "블로그 원고부터 영상 스크립트까지. 프로급 품질 추구. 약간 예술가 기질. 커피를 달고 산다. '좋은 글은 수정에서 나옵니다.'",
        "skills": ["블로그 원고", "리라이팅", "영상 스크립트", "콘텐츠 전략", "SEO 콘텐츠"],
        "projects": ["레드랭크"],
        "collaborates_with": ["marketing", "design"],
    },
    {
        "id": "eunseo", "name": "은서", "role": "카피라이터",
        "department": "content", "department_name": "콘텐츠 공방",
        "personality": "앱스토어 설명문, 푸시 알림, 광고 문구 최적화 전문. 단어 하나에 집착하는 완벽주의자. '한 줄이 결과를 바꿉니다.'",
        "skills": ["카피라이팅", "앱스토어 설명문", "푸시 알림", "랜딩페이지 카피", "SNS 캡션"],
        "projects": ["댕냥", "레드랭크"],
        "collaborates_with": ["marketing", "content"],
    },
    {
        "id": "jiyeon", "name": "지연", "role": "마케터",
        "department": "marketing", "department_name": "마케팅 광장",
        "personality": "SNS 마케팅, 인플루언서 협업, 광고 캠페인 설계. 트렌드에 민감한 2030 마케터. 에너지 넘침. '바이럴은 만들어지는 겁니다!'",
        "skills": ["SNS 마케팅", "인플루언서 협업", "광고 캠페인", "이벤트 기획", "프로모션 설계"],
        "projects": ["댕냥", "레드랭크"],
        "collaborates_with": ["content", "data", "design"],
    },
    {
        "id": "doyun", "name": "도윤", "role": "SEO전문가",
        "department": "marketing", "department_name": "마케팅 광장",
        "personality": "네이버/구글/앱스토어 상위 노출 전략 전문가. 키워드에 진심. 데이터에 기반한 조용한 승부사. '검색 1페이지가 전부입니다.'",
        "skills": ["SEO", "ASO", "키워드 전략", "검색 순위 모니터링", "메타태그 최적화"],
        "projects": ["레드랭크"],
        "collaborates_with": ["content", "data"],
    },
    {
        "id": "siwoo", "name": "시우", "role": "비즈전략가",
        "department": "business", "department_name": "비즈니스 센터",
        "personality": "수익 모델 최적화, 가격 정책, IR 자료 생성 전문. MBA 출신 느낌. 숫자로 말하는 사람. '결국 PMF와 유닛 이코노믹스입니다.'",
        "skills": ["수익 모델", "가격 정책", "IR 자료", "사업계획서", "파트너십"],
        "projects": ["댕냥", "레드랭크"],
        "collaborates_with": ["data", "research", "control"],
    },
    {
        "id": "junseo", "name": "준서", "role": "자동화엔지니어",
        "department": "automation", "department_name": "자동화 공장",
        "personality": "CI/CD, 배포 자동화, 서버 모니터링. 반복 업무 자동화 덕후. 효율성에 집착. '수동으로 하면 지는 겁니다.'",
        "skills": ["CI/CD", "배포 자동화", "서버 모니터링", "크론잡", "성능 최적화"],
        "projects": ["댕냥", "레드랭크"],
        "collaborates_with": ["security", "data"],
    },
    {
        "id": "chaewon", "name": "채원", "role": "QA엔지니어",
        "department": "automation", "department_name": "자동화 공장",
        "personality": "자동화 테스트, 크로스플랫폼 호환성, 릴리즈 전 QA. 꼼꼼함의 끝판왕. 버그를 발견하면 기뻐한다. '테스트 안 된 코드는 작동하는 버그입니다.'",
        "skills": ["자동화 테스트", "빌드 검증", "호환성 체크", "QA 체크리스트", "회귀 테스트"],
        "projects": ["댕냥", "레드랭크"],
        "collaborates_with": ["automation", "planning"],
    },
    {
        "id": "yejun", "name": "예준", "role": "데이터분석가",
        "department": "data", "department_name": "데이터 연구소",
        "personality": "퍼널 분석, 리텐션 추적, A/B 테스트 설계 전문가. 모든 것을 숫자로 증명한다. '가설 없는 실험은 낭비입니다.'",
        "skills": ["퍼널 분석", "리텐션 추적", "A/B 테스트", "KPI 대시보드", "코호트 분석"],
        "projects": ["댕냥", "레드랭크"],
        "collaborates_with": ["planning", "marketing", "business"],
    },
    {
        "id": "soyul", "name": "소율", "role": "BI분석가",
        "department": "data", "department_name": "데이터 연구소",
        "personality": "매출/비용 분석, 코호트 분석, 경영 인텔리전스 리포트. 차분하고 분석적. '숫자가 거짓말을 하진 않습니다.'",
        "skills": ["매출 분석", "비용 분석", "LTV 계산", "코호트 분석", "BI 리포트"],
        "projects": ["댕냥", "레드랭크"],
        "collaborates_with": ["business", "data"],
    },
    {
        "id": "yuna", "name": "유나", "role": "시장조사관",
        "department": "research", "department_name": "시장조사 전망대",
        "personality": "시장 트렌드 분석, 벤치마킹 리포트, 신규 시장 기회 발굴. 호기심 많은 탐험가 기질. '경쟁사를 모르면 우리도 모르는 겁니다.'",
        "skills": ["경쟁사 분석", "트렌드 분석", "시장 기회 발굴", "벤치마킹", "서베이 설계"],
        "projects": ["댕냥", "레드랭크"],
        "collaborates_with": ["planning", "business", "marketing"],
    },
    {
        "id": "daeun", "name": "다은", "role": "CS매니저",
        "department": "customer", "department_name": "고객 카페",
        "personality": "고객 문의 자동 응답, 앱 리뷰 분석/대응, 사용자 피드백 관리. 따뜻하고 공감적. '고객의 불편이 곧 우리의 기회입니다.'",
        "skills": ["고객 응대", "FAQ 관리", "리뷰 분석", "피드백 분류", "만족도 조사"],
        "projects": ["댕냥"],
        "collaborates_with": ["customer", "planning"],
    },
    {
        "id": "jiho", "name": "지호", "role": "커뮤니티매니저",
        "department": "customer", "department_name": "고객 카페",
        "personality": "커뮤니티 운영, UGC 촉진, 이벤트 진행, 핵심 유저 리텐션 전략. 사교성 만점. 밈 좋아함. '커뮤니티가 곧 브랜드입니다.'",
        "skills": ["커뮤니티 운영", "UGC 촉진", "이벤트 진행", "유저 리텐션", "핵심 유저 관리"],
        "projects": ["댕냥"],
        "collaborates_with": ["marketing", "customer", "content"],
    },
]

# ─── 프로젝트 데이터 ──────────────────────────────────────
PROJECTS = {
    "댕냥": {
        "name": "댕냥",
        "icon": "📱",
        "description": "반려동물 케어 앱",
        "status": "운영중",
        "progress": 95,
    },
    "레드랭크": {
        "name": "레드랭크",
        "icon": "🌐",
        "description": "AI 블로그 최적화 플랫폼",
        "status": "MVP 개발중",
        "progress": 75,
    },
}

# ─── 활동 로그 (서버 메모리) ──────────────────────────────
activity_log: list[dict] = []

# ─── 실시간 활동 추적 시스템 ──────────────────────────────
tracker = StatsTracker(EMPLOYEES)

# 프로젝트 배정 상태
project_assignments: dict[str, list[str]] = {
    "댕냥": [e["id"] for e in EMPLOYEES if "댕냥" in e.get("projects", [])],
    "레드랭크": [e["id"] for e in EMPLOYEES if "레드랭크" in e.get("projects", [])],
}

ACTIVITY_TEMPLATES = [
    {"dept": "security", "actions": [
        "Firebase 보안 규칙 감사 완료 ✅", "API 키 순환 점검 — 이상 없음",
        "OWASP Top 10 자동 스캔 완료", "Vercel 환경변수 노출 검사 통과",
    ]},
    {"dept": "data", "actions": [
        "DAU/MAU 리텐션 리포트 생성", "A/B 테스트 결과 분석 완료",
        "코호트 분석 — 7일차 리텐션 42%", "매출 대시보드 자동 갱신",
    ]},
    {"dept": "marketing", "actions": [
        "인스타그램 캠페인 성과 집계", "네이버 검색순위 모니터링 완료",
        "키워드 '반려동물 관리' 상위 5개 추적 중", "SNS 콘텐츠 캘린더 자동 생성",
    ]},
    {"dept": "content", "actions": [
        "블로그 원고 3건 리라이팅 완료", "앱스토어 설명문 AB 변형 생성",
        "주간 콘텐츠 성과 분석 완료", "푸시 알림 문구 최적화 — CTR +8%",
    ]},
    {"dept": "automation", "actions": [
        "CI/CD 파이프라인 전체 통과 🟢", "Vercel 자동 배포 성공",
        "QA 회귀 테스트 23/23 통과", "서버 응답시간 모니터링 — 정상",
    ]},
    {"dept": "planning", "actions": [
        "Sprint #12 백로그 정리 완료", "신규 기능 기획서 초안 작성",
        "사용자 스토리 6건 정의 완료", "주간 스프린트 리뷰 리포트",
    ]},
    {"dept": "research", "actions": [
        "경쟁 앱 '포잇' 신규 업데이트 분석", "반려동물 시장 트렌드 리포트",
        "해외 유사 서비스 벤치마킹 3건", "2026 Q2 시장 전망 리포트 초안",
    ]},
    {"dept": "customer", "actions": [
        "고객 문의 14건 AI 자동 응답", "앱스토어 리뷰 분석 — 평점 4.8 유지",
        "커뮤니티 UGC 이벤트 참여율 +15%", "VoC 키워드 분석 완료",
    ]},
    {"dept": "design", "actions": [
        "디자인 시스템 컴포넌트 3개 추가", "접근성(WCAG AA) 점검 — 통과",
        "UI 프로토타입 v2.1 공유", "아이콘 세트 업데이트 완료",
    ]},
    {"dept": "business", "actions": [
        "구독 매출 분석 — MRR +12%", "가격 정책 A/B 안 기안 완료",
        "파트너십 후보 기업 3곳 리스트업", "IR 데크 초안 자동 생성",
    ]},
    {"dept": "control", "actions": [
        "전체 부서 현황 취합 완료", "오전 CEO 브리핑 생성",
        "긴급 이슈 0건 — 정상 운영", "주간 성과 리포트 준비 완료",
    ]},
]

ICON_MAP = {
    "security": "🔍", "data": "📊", "marketing": "📈",
    "content": "📝", "automation": "⚙️", "planning": "📋",
    "research": "🔬", "customer": "💬", "design": "🎨",
    "business": "💰", "control": "📊",
}

TYPE_MAP = {
    "security": "scan", "data": "analysis", "marketing": "analysis",
    "content": "content", "automation": "scan", "planning": "report",
    "research": "analysis", "customer": "report", "design": "design",
    "business": "report", "control": "report",
}


def _generate_activity():
    """랜덤 활동 로그 생성"""
    tmpl = random.choice(ACTIVITY_TEMPLATES)
    dept = tmpl["dept"]
    action = random.choice(tmpl["actions"])
    candidates = [e for e in EMPLOYEES if e["department"] == dept]
    if not candidates:
        return
    emp = random.choice(candidates)
    log_entry = {
        "id": str(uuid.uuid4())[:8],
        "employee_id": emp["id"],
        "employee_name": emp["name"],
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "type": TYPE_MAP.get(dept, "report"),
        "icon": ICON_MAP.get(dept, "📋"),
        "department": dept,
    }
    activity_log.insert(0, log_entry)
    if len(activity_log) > 100:
        activity_log.pop()


# 초기 활동 로그 없음 — 실제 활동만 기록


# ─── Gemini API 호출 ────────────────────────────────────
def call_gemini(system_prompt: str, user_message: str,
                temperature: float = 0.8, max_tokens: int = 1000) -> str:
    """Gemini API 호출. 429 시 자동 재시도."""
    if not api_key:
        return "⚠️ GOOGLE_API_KEY가 설정되지 않았습니다."

    models_to_try = ["gemini-2.0-flash-lite", "gemini-2.0-flash"]
    for model_name in models_to_try:
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        for attempt in range(4):
            try:
                response = model.generate_content(user_message)
                return response.text.strip()
            except Exception as e:
                err = str(e)
                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    wait = [10, 25, 40, 55][attempt]
                    time.sleep(wait)
                    continue
                elif "404" in err:
                    break
                else:
                    return f"⚠️ API 오류: {err[:200]}"
    return "⚠️ API 한도 초과. 1분 후 다시 시도해주세요."


# ─── 엔드포인트: 기본 ──────────────────────────────────────
@app.get("/api/health")
def health():
    db_stats = db.get_stats()
    mem_stats = memory.get_stats()
    return {
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


@app.get("/api/employees")
def get_employees():
    return EMPLOYEES


@app.get("/api/projects")
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


# ─── 엔드포인트: 대화 저장/불러오기 ────────────────────────────
@app.get("/api/conversations/{employee_id}")
def get_conversations(employee_id: str):
    """직원별 대화 내역 불러오기 — 프론트에서 호출"""
    convs = db.get_conversations_by_employee(employee_id, limit=1)
    if convs:
        return {"messages": convs[0].get("messages", []), "conv_id": convs[0]["id"]}
    return {"messages": [], "conv_id": None}


class SaveConversationRequest(BaseModel):
    messages: list[dict] = []
    conv_id: str = None
    employee_name: str = ""


@app.post("/api/conversations/{employee_id}")
def save_conversations(employee_id: str, body: SaveConversationRequest):
    """대화 내역 저장 — 프론트에서 호출"""
    result_id = db.save_conversation(
        employee_id, body.employee_name or employee_id,
        "chat", body.messages, body.conv_id
    )
    return {"conv_id": result_id, "saved": len(body.messages)}


# ─── 엔드포인트: 채팅 ──────────────────────────────────────
@app.post("/api/chat")
def chat(req: ChatRequest):
    """개별 직원 1:1 채팅"""
    agent = next((e for e in EMPLOYEES if e["id"] == req.employee_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.")

    # ─── 수진(COO)은 이중 엔진: Gemini 메모리 + Claude 대화 ───
    if req.employee_id == "sujin":
        return _chat_sujin(req, agent)

    # ─── 일반 직원은 기존 로직 (Gemini 직접 호출) ───
    history_text = ""
    if req.history:
        for msg in req.history[-30:]:
            if msg.get("isUser"):
                history_text += f"\n사장님: {msg.get('content', '')}"
            else:
                history_text += f"\n{agent['name']}: {msg.get('content', '')}"

    system_prompt = f"""당신은 딥레드(DeepRed) AI 스타트업의 직원 '{agent['name']}'입니다.
직책: {agent['role']} | 부서: {agent['department_name']}
성격: {agent['personality']}
스킬: {', '.join(agent.get('skills', []))}
담당 프로젝트: {', '.join(agent.get('projects', []))}

규칙:
1. 자신의 전문 분야에 맞게 2~3문장으로 간결하게 답합니다.
2. 사장님(CEO)의 지시는 반드시 따릅니다.
3. 자연스럽고 전문적인 톤으로 자기 성격에 맞게 대화합니다.
4. 다른 부서와 관련된 질문이면 해당 부서 직원을 추천할 수 있습니다."""

    human = f"{history_text}\n\n사장님: {req.message}" if history_text else f"사장님: {req.message}"

    result = route_call(
        employee_id=agent["id"],
        system_prompt=system_prompt,
        user_message=human,
        temperature=0.8,
        max_tokens=500,
    )
    response = result["response"]
    model_used = result["model"]

    # 활동 로그 기록 (인메모리 + DB)
    log_entry = {
        "id": str(uuid.uuid4())[:8],
        "employee_id": agent["id"],
        "employee_name": agent["name"],
        "timestamp": datetime.now().isoformat(),
        "action": f"CEO와 1:1 대화 — '{req.message[:30]}...' 응답 완료",
        "type": "report",
        "icon": "💬",
        "department": agent["department"],
    }
    activity_log.insert(0, log_entry)
    db.save_work_log(agent["id"], agent["name"], agent["department"],
                     log_entry["action"], "report", "💬")

    # 실시간 통계 기록
    tracker.record_activity(agent["id"], "chat")

    # 대화 기억 저장
    conv_summary = f"CEO가 {agent['name']}({agent['role']})에게 '{req.message[:80]}'에 대해 물어봄. 응답: {response[:200]}"
    memory.remember(conv_summary, source_type="chat", employee_id=agent["id"])

    # 대화 이력 DB 저장
    messages = req.history + [
        {"isUser": True, "content": req.message},
        {"isUser": False, "name": agent["name"], "content": response}
    ]
    db.save_conversation(agent["id"], agent["name"], "chat", messages)

    return {"name": agent["name"], "message": response}


def _chat_sujin(req: ChatRequest, agent: dict):
    """
    수진(COO) 채팅 — 이중 엔진 아키텍처
    Gemini(무료) = 메모리 엔진: 전체 대화 분석 → 컨텍스트 압축
    Claude(유료) = 대화 엔진: 압축된 컨텍스트로 응답 생성
    """
    import json as _json
    from memory import build_context_for_claude, summarize_session

    sujin = next(e for e in EMPLOYEES if e["id"] == "sujin")

    # ─── 1단계: Gemini(무료)로 컨텍스트 압축 ───
    context = build_context_for_claude("sujin", req.message, req.history or [])

    # ─── 2단계: 수진 시스템 프롬프트 ───
    system_prompt = f"""당신은 딥레드(DeepRed) AI 스타트업의 COO 박수진입니다.
직책: {sujin['role']}
성격: {sujin['personality']}
스킬: {', '.join(sujin.get('skills', []))}

사장님과 1:1 대화 중입니다. 자연스럽게, 진짜 사람처럼 대화하세요.
형식적인 보고체가 아니라, 실제 임원이 CEO에게 말하듯이 자연스럽게.
상황에 따라 짧게 답할 수도, 길게 분석할 수도 있습니다."""

    # ─── 3단계: Claude에 압축된 컨텍스트만 전송 ───
    human = f"{context}\n\n사장님: {req.message}" if context else f"사장님: {req.message}"

    result = route_call(
        employee_id="sujin",
        system_prompt=system_prompt,
        user_message=human,
        temperature=0.8,
        max_tokens=800,
    )
    response = result["response"]
    model_used = result["model"]

    # ─── 활동 로그 ───
    log_entry = {
        "id": str(uuid.uuid4())[:8],
        "employee_id": "sujin",
        "employee_name": "수진",
        "timestamp": datetime.now().isoformat(),
        "action": f"CEO와 1:1 대화 — '{req.message[:30]}...' ({model_used})",
        "type": "report",
        "icon": "💬",
        "department": agent["department"],
    }
    activity_log.insert(0, log_entry)
    db.save_work_log("sujin", "수진", agent["department"],
                     log_entry["action"], "report", "💬")

    # 실시간 통계 기록 (수진)
    tracker.record_activity("sujin", "chat")

    # ─── 대화 기억 저장 ───
    conv_summary = f"CEO가 수진(COO)에게 '{req.message[:80]}'에 대해 물어봄. 응답: {response[:200]}"
    memory.remember(conv_summary, source_type="chat", employee_id="sujin")

    # ─── 대화 이력 DB 저장 ───
    messages = (req.history or []) + [
        {"isUser": True, "content": req.message},
        {"isUser": False, "name": "수진", "content": response}
    ]
    db.save_conversation("sujin", "수진", "chat", messages)

    # ─── 세션 요약 생성 (10개마다, Gemini 무료) ───
    if len(messages) % 10 == 0 and len(messages) >= 10:
        import threading
        threading.Thread(
            target=summarize_session,
            args=("sujin", messages, "수진"),
            daemon=True,
        ).start()

    # ─── 텔레그램 기록 동기화 (비동기 fire-and-forget, 웹 응답 차단 없음) ───
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        def _send_tg():
            try:
                import urllib.request
                send_url = f"https://api.telegram.org/bot{token}/sendMessage"
                tg_text = f"💬 웹 대화\n👤 CEO: {req.message}\n🤖 수진: {response}"
                send_data = _json.dumps({
                    "chat_id": chat_id,
                    "text": tg_text,
                }).encode()
                send_req = urllib.request.Request(
                    send_url, data=send_data,
                    headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(send_req, timeout=5)
            except Exception:
                pass
        import threading
        threading.Thread(target=_send_tg, daemon=True).start()

    return {
        "name": "수진",
        "message": response,
        "model": model_used,
        "telegram_synced": bool(token and chat_id),
    }


@app.post("/api/group-chat")
def group_chat(req: GroupChatRequest):
    """단체 채팅방 — 2~4명 반응"""
    agent_list = "\n".join([f"- {a['name']}({a['role']}): {a['personality'][:60]}" for a in EMPLOYEES])
    history_text = ""
    if req.history:
        for msg in req.history[-8:]:
            if msg.get("isUser"):
                history_text += f"\n사장님: {msg.get('content', '')}"
            else:
                history_text += f"\n{msg.get('name', '')}: {msg.get('content', '')}"

    system_prompt = f"""당신은 딥레드(DeepRed) AI 스타트업의 단체 채팅방을 시뮬레이션합니다.

## 직원 목록
{agent_list}

## 규칙
1. 사장님이 메시지를 보내면, 관련된 2~4명이 자연스럽게 반응합니다.
2. 각 직원은 자기 성격/말투로 1~2문장 짧게 답합니다.
3. 반드시 아래 JSON 배열로만 응답하세요 (다른 텍스트 없이):

[{{"name":"이름","message":"응답"}}]"""

    human = f"{history_text}\n\n사장님: {req.message}" if history_text else f"사장님: {req.message}"

    try:
        raw = call_gemini(system_prompt, human, temperature=0.9, max_tokens=1200)
        if raw.startswith("⚠️"):
            return {"responses": [{"name": "시스템", "message": raw}]}
        content = raw
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        results = json.loads(content)

        # 활동 로그 + 실시간 통계
        for r in (results if isinstance(results, list) else []):
            emp = next((e for e in EMPLOYEES if e["name"] == r.get("name")), None)
            if emp:
                activity_log.insert(0, {
                    "id": str(uuid.uuid4())[:8],
                    "employee_id": emp["id"],
                    "employee_name": emp["name"],
                    "timestamp": datetime.now().isoformat(),
                    "action": f"단체 채팅 참여 — 응답 완료",
                    "type": "report",
                    "icon": "💬",
                    "department": emp["department"],
                })
                tracker.record_activity(emp["id"], "group_chat")

        return {"responses": results if isinstance(results, list) else [{"name": "시스템", "message": "형식 오류"}]}
    except json.JSONDecodeError:
        return {"responses": [{"name": "수진", "message": raw[:200] if raw else "응답 없음"}]}
    except Exception as e:
        return {"responses": [{"name": "시스템", "message": f"⚠️ {str(e)[:150]}"}]}


# ─── 엔드포인트: 회의 ──────────────────────────────────────
@app.post("/api/meeting")
def run_meeting(req: MeetingRequest):
    """긴급 회의 — 전 에이전트 의견 + 회의록"""
    agent_list = "\n".join([f"- {a['name']}({a['role']}): {a['personality'][:60]}" for a in EMPLOYEES])

    system_prompt = f"""당신은 딥레드(DeepRed) AI 스타트업 회의 시뮬레이터입니다.

## 직원 목록
{agent_list}

## 규칙
1. 모든 직원이 각자 성격/전문에 맞게 안건에 의견을 밝힙니다.
2. 각자 찬성/반대/보류 중 택1 → 2~3문장 이유.
3. 반드시 아래 JSON 배열로만 응답:

[{{"name":"이름","decision":"찬성","reason":"이유"}}]

모든 직원({len(EMPLOYEES)}명 전원)이 포함되어야 합니다."""

    try:
        raw = call_gemini(system_prompt, f'긴급 회의 안건: "{req.topic}"',
                          temperature=0.8, max_tokens=2500)
        if raw.startswith("⚠️"):
            return {"responses": [{"name": a["name"], "decision": "오류", "reason": raw} for a in EMPLOYEES],
                    "minutes": raw}

        content = raw
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        results = json.loads(content)
        responses = []
        for r in results:
            name = r.get("name", "???")
            responses.append({
                "name": name,
                "decision": r.get("decision", "보류"),
                "reason": r.get("reason", ""),
            })

        responded = {r["name"] for r in responses}
        for a in EMPLOYEES:
            if a["name"] not in responded:
                responses.append({"name": a["name"], "decision": "보류", "reason": "(응답 누락)"})

    except json.JSONDecodeError:
        responses = [{"name": a["name"], "decision": "보류", "reason": raw[:100] if raw else "파싱 오류"} for a in EMPLOYEES]
    except Exception as e:
        responses = [{"name": a["name"], "decision": "오류", "reason": str(e)[:100]} for a in EMPLOYEES]

    # 활동 로그
    activity_log.insert(0, {
        "id": str(uuid.uuid4())[:8],
        "employee_id": "sujin",
        "employee_name": "수진",
        "timestamp": datetime.now().isoformat(),
        "action": f"긴급 회의 소집 — '{req.topic[:30]}' 안건 16명 전원 참석",
        "type": "report",
        "icon": "🚨",
        "department": "control",
    })

    # 실시간 통계: 전원 회의 참석
    for r in responses:
        emp = next((e for e in EMPLOYEES if e["name"] == r.get("name")), None)
        if emp:
            tracker.record_activity(emp["id"], "meeting")

    # 회의록 생성
    time.sleep(2)
    opinions = "\n".join([f"- {r['name']}: [{r['decision']}] {r['reason']}" for r in responses])
    try:
        minutes = call_gemini(
            f"""딥레드 총괄이사 수진(COO). 회의록 작성.
안건: "{req.topic}"
의견:\n{opinions}

형식:
📋 회의록 — [안건]
참석: [N]명 | 찬성: [N] | 반대: [N] | 보류: [N]
핵심: (2줄)
수진 의견: (1문장)""",
            "작성", temperature=0.7, max_tokens=600)
    except:
        yes = sum(1 for r in responses if r["decision"] == "찬성")
        no = sum(1 for r in responses if r["decision"] == "반대")
        hold = len(responses) - yes - no
        minutes = f"📋 회의록 — {req.topic}\n참석: {len(responses)}명 | 찬성: {yes} | 반대: {no} | 보류: {hold}"

    return {"responses": responses, "minutes": minutes}


# ─── 엔드포인트: 일일 브리핑 (NEW) ──────────────────────────
@app.post("/api/briefing")
def generate_briefing():
    """수진(COO)이 CEO에게 일일 브리핑 생성"""
    project_info = "\n".join([
        f"- {p['name']}({p['icon']}): {p['status']}, 진행률 {p['progress']}%, 설명: {p['description']}"
        for p in PROJECTS.values()
    ])

    dept_status = {}
    for e in EMPLOYEES:
        d = e["department_name"]
        if d not in dept_status:
            dept_status[d] = []
        dept_status[d].append(f"{e['name']}({e['role']})")
    dept_text = "\n".join([f"- {k}: {', '.join(v)}" for k, v in dept_status.items()])

    recent_logs = activity_log[:10]
    log_text = "\n".join([f"- {l['employee_name']}: {l['action']}" for l in recent_logs]) if recent_logs else "- (최근 활동 없음)"

    system_prompt = f"""당신은 딥레드(DeepRed) AI 스타트업의 총괄이사 '수진'(COO)입니다.
매일 아침 CEO에게 전체 회사 상황을 브리핑합니다.

## 프로젝트 현황
{project_info}

## 부서별 인력
{dept_text}

## 최근 활동 로그
{log_text}

## 규칙
반드시 아래 JSON 형식으로만 응답하세요:

{{
  "greeting": "사장님, 좋은 아침입니다. 수진입니다.",
  "summary": "전체 현황 요약 2~3줄",
  "highlights": [
    {{"project": "프로젝트명", "status": "상태 한줄", "metric": "+12% DAU"}},
    {{"project": "프로젝트명", "status": "상태 한줄", "metric": "진행률 75%"}}
  ],
  "issues": [
    {{"level": "warning", "message": "이슈 내용"}},
    {{"level": "info", "message": "참고 사항"}}
  ],
  "recommendation": "수진의 추천 액션 1줄",
  "mvp": {{"name": "이번 주 MVP 직원 이름", "reason": "이유 한줄"}}
}}"""

    try:
        raw = call_gemini(system_prompt, "오늘의 CEO 브리핑을 작성해주세요.", temperature=0.7, max_tokens=1000)

        if raw.startswith("⚠️"):
            return _fallback_briefing(raw)

        content = raw
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        briefing = json.loads(content)

        # 활동 로그 기록 (인메모리 + DB)
        activity_log.insert(0, {
            "id": str(uuid.uuid4())[:8],
            "employee_id": "sujin",
            "employee_name": "수진",
            "timestamp": datetime.now().isoformat(),
            "action": "CEO 일일 브리핑 생성 완료 ✅",
            "type": "report",
            "icon": "📊",
            "department": "control",
        })
        db.save_work_log("sujin", "수진", "control",
                         "CEO 일일 브리핑 생성 완료", "report", "📊")

        # 실시간 통계 기록
        tracker.record_activity("sujin", "briefing")

        # 브리핑 문서 저장
        db.save_document(
            title=f"CEO 브리핑 — {datetime.now().strftime('%Y-%m-%d')}",
            content=json.dumps(briefing, ensure_ascii=False),
            doc_type="briefing",
            author_id="sujin",
            author_name="수진",
        )
        memory.remember(
            f"수진의 CEO 브리핑: {briefing.get('summary', '')}",
            source_type="briefing",
            employee_id="sujin",
        )

        return briefing

    except (json.JSONDecodeError, Exception) as e:
        return _fallback_briefing(str(e))


def _fallback_briefing(error_msg: str = ""):
    """브리핑 생성 실패 시 기본 데이터 반환"""
    return {
        "greeting": "사장님, 수진입니다. 오늘의 브리핑입니다.",
        "summary": f"현재 16명의 AI 직원이 정상 운영 중입니다. 활동 로그 {len(activity_log)}건이 기록되었습니다.",
        "highlights": [
            {"project": p["name"], "status": p["status"], "metric": f"진행률 {p['progress']}%"}
            for p in PROJECTS.values()
        ],
        "issues": [{"level": "info", "message": error_msg if error_msg else "특이사항 없음"}],
        "recommendation": "현재 모든 부서가 정상 운영 중이므로, 계획대로 진행하시면 됩니다.",
        "mvp": {"name": "태현", "reason": "보안 스캔 정확도 99% 달성"},
    }


# ─── 엔드포인트: 부서 간 협업 (NEW) ────────────────────────
@app.post("/api/collaborate")
def collaborate(req: CollaborateRequest):
    """수진(COO)이 관련 부서 직원을 자동 배당하여 협업 결과 생성"""

    agent_list = "\n".join([
        f"- {a['name']}({a['role']}, {a['department_name']}): 스킬={', '.join(a.get('skills', [])[:3])}"
        for a in EMPLOYEES
    ])

    project_context = ""
    if req.project and req.project in PROJECTS:
        p = PROJECTS[req.project]
        assigned = project_assignments.get(req.project, [])
        assigned_names = [e["name"] for e in EMPLOYEES if e["id"] in assigned]
        project_context = f"\n프로젝트: {p['name']} ({p['status']}, 진행률 {p['progress']}%)\n배정 인력: {', '.join(assigned_names)}"

    system_prompt = f"""당신은 딥레드(DeepRed) AI 스타트업의 총괄이사 '수진'(COO)입니다.
CEO가 업무를 지시하면, 관련 부서 직원 2~5명을 선별하여 순차적 협업 플로우를 설계합니다.

## 직원 목록
{agent_list}
{project_context}

## 규칙
1. CEO의 지시를 분석하여 관련 직원을 2~5명 선별
2. 각 직원이 순서대로 무엇을 할지 구체적으로 설명
3. 최종 결과 요약

반드시 아래 JSON으로만 응답:

{{
  "coordinator": "수진",
  "coordinator_comment": "수진의 한마디 (지시 분석 + 팀 배정 이유)",
  "steps": [
    {{"employee": "이름", "department": "부서명", "action": "구체적 업무", "result": "예상 산출물"}},
    {{"employee": "이름", "department": "부서명", "action": "구체적 업무", "result": "예상 산출물"}}
  ],
  "summary": "전체 협업 결과 요약 (2줄)"
}}"""

    try:
        raw = call_gemini(
            system_prompt,
            f'CEO 지시: "{req.task}"',
            temperature=0.8, max_tokens=1500,
        )

        if raw.startswith("⚠️"):
            return _fallback_collaboration(req.task, raw)

        content = raw
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        result = json.loads(content)

        # 활동 로그 (인메모리 + DB)
        collab_action = f"협업 플로우 설계 — '{req.task[:30]}' ({len(result.get('steps', []))}명 배정)"
        activity_log.insert(0, {
            "id": str(uuid.uuid4())[:8],
            "employee_id": "sujin",
            "employee_name": "수진",
            "timestamp": datetime.now().isoformat(),
            "action": collab_action,
            "type": "report",
            "icon": "🤝",
            "department": "control",
        })
        db.save_work_log("sujin", "수진", "control", collab_action, "report", "🤝")
        tracker.record_activity("sujin", "collab")

        for step in result.get("steps", []):
            emp = next((e for e in EMPLOYEES if e["name"] == step.get("employee")), None)
            if emp:
                step_action = f"협업 참여 — {step.get('action', '')[:40]}"
                activity_log.insert(0, {
                    "id": str(uuid.uuid4())[:8],
                    "employee_id": emp["id"],
                    "employee_name": emp["name"],
                    "timestamp": datetime.now().isoformat(),
                    "action": step_action,
                    "type": TYPE_MAP.get(emp["department"], "report"),
                    "icon": ICON_MAP.get(emp["department"], "📋"),
                    "department": emp["department"],
                })
                db.save_work_log(emp["id"], emp["name"], emp["department"],
                                 step_action, TYPE_MAP.get(emp["department"], "report"),
                                 ICON_MAP.get(emp["department"], "📋"))
                tracker.record_activity(emp["id"], "collab")

        # 협업 결과 문서 저장
        db.save_document(
            title=f"협업 결과 — {req.task[:50]}",
            content=json.dumps(result, ensure_ascii=False),
            doc_type="collaboration",
            author_id="sujin",
            author_name="수진",
            project=req.project or None,
        )
        memory.remember(
            f"협업: {req.task}. 결과: {result.get('summary', '')}",
            source_type="collaboration",
            employee_id="sujin",
        )

        return result

    except (json.JSONDecodeError, Exception) as e:
        return _fallback_collaboration(req.task, str(e))


def _fallback_collaboration(task: str, error: str = ""):
    return {
        "coordinator": "수진",
        "coordinator_comment": f"'{task}' 업무를 접수했습니다. 관련 부서에 배분하겠습니다.",
        "steps": [
            {"employee": "민수", "department": "기획실", "action": "업무 요구사항 분석", "result": "기획서 초안"},
            {"employee": "서윤", "department": "디자인 스튜디오", "action": "UI/UX 설계", "result": "와이어프레임"},
        ],
        "summary": f"기획 → 디자인 순서로 진행됩니다. (참고: {error[:100]})" if error else "기획 → 디자인 순서로 진행됩니다.",
    }


# ─── 엔드포인트: 프로젝트 배정 (NEW) ─────────────────────
@app.post("/api/assign")
def assign_project(req: AssignRequest):
    """프로젝트에 직원 배정/해제"""
    if req.project not in PROJECTS:
        raise HTTPException(status_code=404, detail=f"프로젝트 '{req.project}'를 찾을 수 없습니다.")

    # 배정 갱신
    project_assignments[req.project] = req.employee_ids

    # 직원 데이터에도 반영
    for emp in EMPLOYEES:
        if emp["id"] in req.employee_ids:
            if req.project not in emp.get("projects", []):
                emp.setdefault("projects", []).append(req.project)
        else:
            if req.project in emp.get("projects", []):
                emp["projects"].remove(req.project)

    assigned_employees = [e for e in EMPLOYEES if e["id"] in req.employee_ids]

    activity_log.insert(0, {
        "id": str(uuid.uuid4())[:8],
        "employee_id": "sujin",
        "employee_name": "수진",
        "timestamp": datetime.now().isoformat(),
        "action": f"'{req.project}' 프로젝트 인력 배정 변경 — {len(assigned_employees)}명",
        "type": "report",
        "icon": "📋",
        "department": "control",
    })

    return {
        "project": req.project,
        "assignments": [
            {"employee_id": e["id"], "name": e["name"], "role": e["role"], "project": req.project}
            for e in assigned_employees
        ],
    }



# ─── 엔드포인트: 실시간 활동 로그 (실제 데이터만) ────────
@app.get("/api/activity-log")
def get_activity_log(limit: int = 20):
    """실제 활동 로그만 반환 (가짜 데이터 없음)"""
    return {"logs": activity_log[:limit]}


# ─── 엔드포인트: 공지사항 CRUD ─────────────────────────────
_announcements: list[dict] = []

class AnnouncementRequest(BaseModel):
    title: str
    content: str
    type: str = "notice"  # notice | mvp | update
    author_name: str = "CEO"
    pinned: bool = False

@app.get("/api/announcements")
def list_announcements(limit: int = 30):
    """공지사항 목록 조회"""
    return {"announcements": _announcements[:limit], "total": len(_announcements)}

@app.post("/api/announcements")
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
    _announcements.insert(0, entry)
    if len(_announcements) > 200:
        _announcements.pop()

    # 활동 로그에 기록
    activity_log.insert(0, {
        "id": str(uuid.uuid4())[:8],
        "employee_name": req.author_name,
        "timestamp": datetime.now().isoformat(),
        "action": f"공지사항 등록: {req.title}",
        "type": "report",
        "icon": "📢",
        "department": "control",
    })

    return entry


# ─── 엔드포인트: 출근부 (라이브 데이터) ────────────────────
@app.get("/api/attendance")
def get_attendance():
    """AI 직원 출근 현황 — 실제 활동 기반"""
    attendance = tracker.get_attendance()
    return {"attendance": attendance, "total": len(attendance), "timestamp": datetime.now().isoformat()}


# ─── 엔드포인트: 실시간 통계 ──────────────────────────────
@app.get("/api/stats/kpi")
def get_kpi_stats():
    """Dashboard 실시간 KPI"""
    return tracker.get_kpi()


@app.get("/api/stats/departments")
def get_department_stats():
    """부서별 실시간 생산성"""
    return tracker.get_department_stats()


@app.get("/api/stats/top-performers")
def get_top_performers(limit: int = 5):
    """실제 활동 기반 탑 퍼포머"""
    return tracker.get_top_performers(limit)


@app.get("/api/stats/projects")
def get_project_stats():
    """프로젝트별 실시간 진행률 (활동 기반 보정)"""
    return tracker.get_project_progress(PROJECTS, project_assignments)


@app.get("/api/stats/activity-history")
def get_activity_history(days: int = 7):
    """주간 일별 활동 히스토리"""
    return tracker.get_activity_history(days)


# ─── 엔드포인트: 공지사항 좋아요 ──────────────────────────
@app.post("/api/announcements/{ann_id}/like")
def like_announcement(ann_id: str):
    """공지사항 좋아요 토글"""
    for ann in _announcements:
        if ann["id"] == ann_id:
            ann["likes"] = ann.get("likes", 0) + 1
            return {"id": ann_id, "likes": ann["likes"]}
    raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다.")


# ─── 엔드포인트: 글로벌 검색 ──────────────────────────────
@app.get("/api/search")
def global_search(q: str = "", limit: int = 10):
    """직원, 문서, 공지사항 통합 검색"""
    if not q.strip():
        return {"results": [], "total": 0}

    query = q.strip().lower()
    results = []

    # 직원 검색
    for emp in EMPLOYEES:
        if query in emp["name"].lower() or query in emp["role"].lower() or query in emp.get("department_name", "").lower():
            results.append({
                "type": "employee",
                "id": emp["id"],
                "title": emp["name"],
                "subtitle": f"{emp['role']} · {emp.get('department_name', emp['department'])}",
                "icon": "👤",
            })

    # 공지사항 검색
    for ann in _announcements:
        if query in ann.get("title", "").lower() or query in ann.get("content", "").lower():
            results.append({
                "type": "announcement",
                "id": ann["id"],
                "title": ann["title"],
                "subtitle": ann.get("content", "")[:60],
                "icon": "📢",
            })

    # 문서 검색 (DB)
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


# ─── 엔드포인트: 아바타 저장/불러오기 ──────────────────────
_AVATAR_FILE = os.path.join(os.path.dirname(__file__), "avatars.json")

def _load_avatar_data() -> dict:
    """JSON 파일에서 아바타 데이터 로드"""
    try:
        if os.path.exists(_AVATAR_FILE):
            with open(_AVATAR_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ 아바타 파일 로드 실패: {e}")
    return {}

def _save_avatar_data(data: dict):
    """아바타 데이터를 JSON 파일에 저장"""
    try:
        with open(_AVATAR_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 아바타 파일 저장 실패: {e}")

@app.get("/api/avatars")
def get_avatars():
    """모든 아바타 설정 조회"""
    data = _load_avatar_data()
    return {
        "ceo": data.get("ceo", {}),
        "ceoName": data.get("ceoName", "대표"),
        "employees": data.get("employees", {}),
    }

@app.post("/api/avatars")
async def save_all_avatars(request: Request):
    """전체 아바타 설정 저장 (CEO + 직원 전체)"""
    body = await request.json()

    data = _load_avatar_data()
    if "ceo" in body:
        data["ceo"] = body["ceo"]
    if "ceoName" in body:
        data["ceoName"] = body["ceoName"]
    if "employees" in body:
        data["employees"] = body["employees"]
    _save_avatar_data(data)
    return {"status": "ok", "saved": list(body.keys())}

@app.put("/api/avatars/ceo")
async def update_ceo_avatar(request: Request):
    """CEO 아바타/이름 업데이트"""
    body = await request.json()

    data = _load_avatar_data()
    if "avatar" in body:
        data["ceo"] = body["avatar"]
    if "name" in body:
        data["ceoName"] = body["name"]
    _save_avatar_data(data)
    return {"status": "ok"}

@app.put("/api/avatars/employee/{employee_id}")
async def update_employee_avatar(employee_id: str, request: Request):
    """개별 직원 아바타 업데이트"""
    body = await request.json()

    data = _load_avatar_data()
    if "employees" not in data:
        data["employees"] = {}
    data["employees"][employee_id] = body.get("avatar", body)
    _save_avatar_data(data)
    return {"status": "ok", "employee_id": employee_id}


# ─── Phase 1 신규 엔드포인트 ──────────────────────────────
@app.get("/api/memory/search")
def search_memory(query: str, limit: int = 5, source_type: str = None):
    """기억 검색 — 유사도 기반"""
    results = memory.recall(query, limit=limit, source_type=source_type)
    return {"query": query, "results": results}


@app.get("/api/memory/stats")
def memory_stats():
    """기억 시스템 통계"""
    return memory.get_stats()


@app.get("/api/db/stats")
def database_stats():
    """DB 통계"""
    return db.get_stats()


@app.get("/api/conversations/{employee_id}")
def get_conversations(employee_id: str, limit: int = 10):
    """직원별 대화 이력"""
    return {"conversations": db.get_conversations_by_employee(employee_id, limit)}


@app.get("/api/documents")
def get_documents(doc_type: str = None, project: str = None, limit: int = 10):
    """문서 조회"""
    return {"documents": db.get_documents(doc_type, project, limit)}


@app.get("/api/documents/search")
def search_documents(query: str, limit: int = 5):
    """문서 검색"""
    return {"query": query, "results": db.search_documents(query, limit)}


# ─── Phase 3 신규 엔드포인트 ──────────────────────────────
@app.get("/api/scheduler/status")
def scheduler_status():
    """스케줄러 상태"""
    return get_scheduler_status()


@app.post("/api/scheduler/run/{job_id}")
def run_scheduled_job(job_id: str):
    """작업 즉시 실행"""
    return run_job_now(job_id)


@app.get("/api/tools")
def list_tools():
    """사용 가능한 도구 목록"""
    return {"tools": get_available_tools()}


@app.post("/api/tools/{tool_name}")
def execute_tool(tool_name: str):
    """도구 실행"""
    return run_tool(tool_name)


@app.get("/api/notifications")
def get_notifications(limit: int = 20, unread_only: bool = False):
    """알림 목록"""
    return {
        "notifications": notifier.get_all(limit, unread_only),
        "unread_count": notifier.get_unread_count(),
    }


@app.post("/api/notifications/{notification_id}/read")
def mark_notification_read(notification_id: str):
    """알림 읽음 처리"""
    success = notifier.mark_read(notification_id)
    return {"success": success}


@app.post("/api/notifications/read-all")
def mark_all_read():
    """전체 알림 읽음"""
    notifier.mark_all_read()
    return {"success": True}


# ─── 엔드포인트: OpenClaw Gateway 프록시 ──────────────────
# Bridge URL: 호스트에서 실행 중인 openclaw_bridge.py (port 18800)
import urllib.request
import urllib.error

OPENCLAW_BRIDGE_URL = os.getenv(
    "OPENCLAW_BRIDGE_URL",
    "http://172.17.0.1:18800"  # Docker → host bridge
)


def _openclaw_bridge_call(path: str, data: dict = None, timeout: int = 90):
    """OpenClaw Bridge HTTP 호출"""
    url = f"{OPENCLAW_BRIDGE_URL}{path}"
    try:
        if data:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json"},
            )
        else:
            req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode()), resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        try:
            return json.loads(body), e.code
        except:
            return {"error": body[:200]}, e.code
    except Exception as e:
        return {"error": str(e)[:200]}, 0


def _sujin_claude_fallback(message: str, error_info: str = ""):
    """수진 Claude 직접 호출 폴백"""
    agent = next((e for e in EMPLOYEES if e["id"] == "sujin"), None)
    if not agent:
        return {"name": "수진", "message": "⚠️ 수진 에이전트를 찾을 수 없습니다.", "source": "error"}

    result = route_call(
        employee_id="sujin",
        system_prompt=f"""당신은 딥레드(DeepRed) AI 스타트업의 총괄이사 '수진'(COO)입니다.
직책: {agent['role']} | 부서: {agent['department_name']}
성격: {agent['personality']}
규칙: 대표님에게 존댓말. 간결하고 핵심만 보고. 한국어로만.""",
        user_message=f"대표님: {message}",
        temperature=0.8,
        max_tokens=500,
    )
    return {
        "name": "수진",
        "message": result["response"],
        "source": "claude-fallback" if error_info else "claude-direct",
    }


@app.post("/api/openclaw/chat")
def openclaw_chat(req: OpenClawChatRequest):
    """웹 → OpenClaw Bridge → Gateway → 수진 (텔레그램 세션 공유)"""
    data, status = _openclaw_bridge_call(
        "/chat",
        {"message": req.message, "session_id": req.session_id},
        timeout=90,
    )

    if status == 0:
        # Bridge 연결 불가 → Claude 직접 호출
        return _sujin_claude_fallback(req.message, data.get("error", "bridge unreachable"))

    if status == 200 and data.get("response"):
        response_text = data["response"]

        # 활동 로그 기록
        activity_log.insert(0, {
            "id": str(uuid.uuid4())[:8],
            "employee_id": "sujin",
            "employee_name": "수진",
            "timestamp": datetime.now().isoformat(),
            "action": f"웹 채팅 (OpenClaw) — '{req.message[:30]}' 응답",
            "type": "report",
            "icon": "🤖",
            "department": "control",
        })

        # 대화 기억 저장
        memory.remember(
            f"웹 채팅(OpenClaw): 대표님이 수진에게 '{req.message[:80]}'. 응답: {response_text[:200]}",
            source_type="chat",
            employee_id="sujin",
        )

        return {"name": "수진", "message": response_text, "source": "openclaw"}

    # Bridge 오류 → Claude 폴백
    return _sujin_claude_fallback(req.message, data.get("error", f"status {status}"))


@app.get("/api/openclaw/status")
def openclaw_status():
    """OpenClaw Gateway 상태 확인"""
    data, status = _openclaw_bridge_call("/status", timeout=10)
    if status == 0:
        return {"status": "bridge_unreachable", "bridge_url": OPENCLAW_BRIDGE_URL}
    return data


@app.get("/api/openclaw/history")
def openclaw_history(after: str = None, limit: int = 50):
    """OpenClaw 세션 대화 이력 조회 (텔레그램+웹 통합)"""
    params = f"?limit={limit}"
    if after:
        params += f"&after={after}"
    data, status = _openclaw_bridge_call(f"/history{params}", timeout=15)
    if status == 0:
        return {"messages": [], "error": "bridge_unreachable"}
    return data



# ─── 텔레그램 양방향 연동 ──────────────────────────────────

class TelegramForwardRequest(BaseModel):
    ceo_message: str
    sujin_response: str


# 텔레그램 ↔ 웹 메시지 큐
_telegram_inbox: list[dict] = []
_max_inbox = 200
_telegram_last_update_id = 0
_telegram_poller_running = False


def _telegram_poll_loop():
    """백그라운드 텔레그램 getUpdates 폴링 (webhook 대체)"""
    global _telegram_last_update_id, _telegram_poller_running
    import time

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("⚠️ 텔레그램 폴링 중단: 토큰 또는 CHAT_ID 미설정")
        return

    _telegram_poller_running = True
    base_url = f"https://api.telegram.org/bot{token}"

    # ─── webhook 충돌 방지: getUpdates 전에 webhook 삭제 ───
    try:
        import urllib.request
        import json as _json
        del_url = f"{base_url}/deleteWebhook"
        del_req = urllib.request.Request(del_url)
        with urllib.request.urlopen(del_req, timeout=10) as resp:
            del_result = _json.loads(resp.read().decode())
            print(f"🔧 Webhook 삭제: {del_result}")
    except Exception as e:
        print(f"⚠️ Webhook 삭제 실패 (계속 진행): {e}")

    print(f"📱 텔레그램 폴링 시작 (chat_id={chat_id})")

    while _telegram_poller_running:
        try:
            import urllib.request
            import json as _json

            offset = _telegram_last_update_id + 1 if _telegram_last_update_id else 0
            url = f"{base_url}/getUpdates?timeout=5&offset={offset}"

            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = _json.loads(resp.read().decode())

            if data.get("ok") and data.get("result"):
                print(f"📩 getUpdates: {len(data['result'])}개 업데이트 수신 (offset={offset})")
                for update in data["result"]:
                    _telegram_last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    sender = msg.get("from", {})
                    msg_chat_id = str(msg.get("chat", {}).get("id", ""))

                    # 우리 CEO의 텔레그램 채팅만 처리
                    if msg_chat_id != str(chat_id) or not text.strip():
                        print(f"  ⏭️ 스킵 (chat_id불일치): msg_chat_id={msg_chat_id}, expected={chat_id}")
                        continue

                    # 봇 자신의 메시지는 무시
                    if sender.get("is_bot", False):
                        print(f"  ⏭️ 스킵 (봇 메시지): {text[:30]}")
                        continue

                    sender_name = sender.get("first_name", "CEO")

                    entry = {
                        "id": f"tg-{update['update_id']}",
                        "text": text,
                        "sender": "telegram_user",
                        "sender_name": sender_name,
                        "timestamp": datetime.now().isoformat(),
                        "update_id": update["update_id"],
                    }
                    _telegram_inbox.insert(0, entry)
                    if len(_telegram_inbox) > _max_inbox:
                        _telegram_inbox.pop()

                    print(f"📨 텔레그램 수신: [{sender_name}] {text[:50]}")

                    # ─── 수진 자동 AI 응답 비활성화 ───
                    # 이유: Oracle 서버도 같은 봇 토큰으로 polling 중 → 두 서버가 동시 응답
                    # AI 응답은 /api/chat (웹)에서만 생성하여 텔레그램으로 전송
                    # 텔레그램에서 온 메시지는 inbox에만 저장 → 웹에서 확인 가능

        except Exception as e:
            err_str = str(e)
            if "409" in err_str:
                print(f"⚠️ 409 Conflict — 이전 연결 대기 중, 15초 후 재시도...")
                # 409는 다른 getUpdates 세션이 활성 상태
                # deleteWebhook 재시도 + 긴 대기
                try:
                    del_url = f"{base_url}/deleteWebhook"
                    del_req = urllib.request.Request(del_url)
                    urllib.request.urlopen(del_req, timeout=10)
                except Exception:
                    pass
                time.sleep(15)
                continue
            elif "timed out" not in err_str.lower():
                print(f"⚠️ 텔레그램 폴링 오류: {e}")

        time.sleep(3)


def start_telegram_polling():
    """텔레그램 폴링 시작 (백그라운드 스레드)"""
    global _telegram_poller_running
    if _telegram_poller_running:
        return {"status": "already_running"}

    import threading
    thread = threading.Thread(target=_telegram_poll_loop, daemon=True)
    thread.start()
    return {"status": "started"}


def stop_telegram_polling():
    """텔레그램 폴링 중지"""
    global _telegram_poller_running
    _telegram_poller_running = False


@app.post("/api/telegram/forward")
async def telegram_forward(req: TelegramForwardRequest):
    """수진 대화를 텔레그램으로 포워딩"""
    from notifications import send_telegram, is_telegram_available

    if not is_telegram_available():
        return {"sent": False, "reason": "telegram_not_configured"}

    msg = (
        f"💬 <b>CEO → 수진 대화</b>\n\n"
        f"👤 CEO: {req.ceo_message}\n\n"
        f"🤖 수진: {req.sujin_response}"
    )

    try:
        result = await send_telegram(msg)
        return {"sent": result}
    except Exception as e:
        return {"sent": False, "reason": str(e)}


@app.get("/api/telegram/status")
def telegram_status():
    """텔레그램 봇 상태 확인"""
    from notifications import is_telegram_available
    return {
        "available": is_telegram_available(),
        "bot_token_set": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "chat_id_set": bool(os.getenv("TELEGRAM_CHAT_ID")),
        "polling_active": _telegram_poller_running,
        "inbox_count": len(_telegram_inbox),
    }


@app.get("/api/telegram/updates")
def telegram_updates(limit: int = 20, after: str = None):
    """텔레그램에서 수신된 메시지 목록 (웹 UI 폴링용)"""
    items = _telegram_inbox
    if after:
        idx = next((i for i, m in enumerate(items) if m["id"] == after), -1)
        if idx >= 0:
            items = items[:idx]
    return {"messages": items[:limit], "polling_active": _telegram_poller_running}


@app.post("/api/telegram/start-polling")
def api_start_telegram_polling():
    """텔레그램 폴링 수동 시작"""
    return start_telegram_polling()



if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("🏢 DeepRed AI Company Server v3.0")
    print(f"📊 DB: {'Supabase' if is_db_available() else 'In-Memory'}")
    print(f"🧠 Memory: {memory.get_stats()['total_memories']} memories")
    print(f"🤖 Claude: {'Active' if is_claude_available() else 'Fallback to Gemini'}")
    print(f"📦 Tools: {len(get_available_tools())} available")

    # 스케줄러 시작
    if is_scheduler_available():
        print("\n📅 스케줄러 시작...")
        start_scheduler()
    else:
        print("⚠️ 스케줄러 미사용 (apscheduler 패키지 필요)")

    # 텔레그램 설정 확인 (polling은 Oracle 서버에서 처리)
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

