"""
DeepRed v3.0 — 공유 의존성 모듈 (deps.py)
모든 라우터가 공유하는 데이터, 상태, 유틸리티
"""

import os
import uuid
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import google.generativeai as genai

from database import db, is_db_available
from memory import memory
from llm_router import route_call, get_router_stats, is_claude_available
from stats_tracker import StatsTracker
from notifications import notifier
from scheduler import start_scheduler, stop_scheduler, run_job_now, get_scheduler_status, is_scheduler_available
from tools import get_available_tools, run_tool


# ─── Gemini 설정 ─────────────────────────────────────────
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)


# ─── 직원 데이터 ────────────────────────────────────────
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
    },
    "레드랭크": {
        "name": "레드랭크",
        "icon": "🌐",
        "description": "AI 블로그 최적화 플랫폼",
        "status": "MVP 개발중",
    },
}


# ─── 공유 상태 ────────────────────────────────────────────
activity_log: list[dict] = []

# 실시간 활동 추적
tracker = StatsTracker(EMPLOYEES)

# 프로젝트 배정
project_assignments: dict[str, list[str]] = {
    "댕냥": [e["id"] for e in EMPLOYEES if "댕냥" in e.get("projects", [])],
    "레드랭크": [e["id"] for e in EMPLOYEES if "레드랭크" in e.get("projects", [])],
}

# 공지사항 (인메모리)
announcements: list[dict] = []

# 아이콘/타입 매핑
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


# ─── 유틸리티 ────────────────────────────────────────────
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


def load_activity_log_from_db():
    """서버 시작 시 Supabase에서 최근 활동 로그 복원"""
    global activity_log
    try:
        logs = db.get_work_logs(limit=100)
        if logs:
            activity_log = [
                {
                    "id": log.get("id", str(uuid.uuid4())[:8]),
                    "employee_id": log.get("employee_id", ""),
                    "employee_name": log.get("employee_name", ""),
                    "timestamp": log.get("created_at", datetime.now().isoformat()),
                    "action": log.get("action", ""),
                    "type": log.get("type", "report"),
                    "icon": log.get("icon", "📋"),
                    "department": log.get("department", ""),
                }
                for log in logs
            ]
            print(f"✅ 활동 로그 {len(activity_log)}건 DB에서 복원")
    except Exception as e:
        print(f"⚠️ 활동 로그 DB 복원 실패: {e}")


def add_activity_log(employee_id: str, employee_name: str, department: str,
                     action: str, log_type: str = "report", icon: str = "📋"):
    """활동 로그 추가 (인메모리 + DB)"""
    entry = {
        "id": str(uuid.uuid4())[:8],
        "employee_id": employee_id,
        "employee_name": employee_name,
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "type": log_type,
        "icon": icon,
        "department": department,
    }
    activity_log.insert(0, entry)
    db.save_work_log(employee_id, employee_name, department, action, log_type, icon)
    return entry


def parse_json_response(raw: str) -> dict | list:
    """LLM 응답에서 JSON 파싱. 코드블록 제거."""
    content = raw
    if "```" in content:
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    return json.loads(content)
