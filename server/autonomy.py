"""
DeepRed v3.0 — AutonomyEngine
AI 직원 자율 행동 시스템

직원들이 역할에 맞는 업무를 자발적으로 수행합니다.
CEO 개입 없이도 회사가 돌아가는 시뮬레이션.
"""

import random
import threading
from datetime import datetime, timedelta
from collections import defaultdict

_engine_lock = threading.Lock()
_action_history: list[dict] = []
_max_history = 200
_engine_running = False

# 각 직원 행동 쿨다운 (마지막 행동 시각)
_cooldowns: dict[str, datetime] = {}
_MIN_COOLDOWN_MINUTES = 30


# ─── 역할별 자율 행동 정의 ──────────────────────────────────
AUTONOMOUS_ACTIONS = {
    "sujin": {
        "role": "총괄이사",
        "actions": [
            {"action": "부서별 업무 현황 점검 및 조율 메모 작성", "type": "report", "icon": "📊", "weight": 3},
            {"action": "이번 주 우선순위 태스크 재정렬", "type": "report", "icon": "📋", "weight": 2},
            {"action": "프로젝트 간 리소스 배분 검토", "type": "report", "icon": "⚖️", "weight": 1},
        ],
    },
    "minsu": {
        "role": "기획관",
        "actions": [
            {"action": "스프린트 백로그 정리 및 우선순위 재조정", "type": "report", "icon": "📋", "weight": 3},
            {"action": "사용자 스토리 초안 작성", "type": "report", "icon": "📝", "weight": 2},
            {"action": "기능별 임팩트-노력 매트릭스 업데이트", "type": "report", "icon": "📊", "weight": 1},
        ],
    },
    "taehyun": {
        "role": "보안관",
        "actions": [
            {"action": "API 키 노출 여부 자동 스캔 완료", "type": "scan", "icon": "🔍", "weight": 3},
            {"action": "Firebase 보안 규칙 감사 수행", "type": "scan", "icon": "🛡️", "weight": 2},
            {"action": "의존성 패키지 CVE 취약점 체크", "type": "scan", "icon": "⚠️", "weight": 1},
        ],
    },
    "seoyun": {
        "role": "디자이너",
        "actions": [
            {"action": "디자인 시스템 컴포넌트 일관성 점검", "type": "design", "icon": "🎨", "weight": 3},
            {"action": "접근성(WCAG) 자가 점검 리포트 생성", "type": "design", "icon": "♿", "weight": 2},
            {"action": "UI 컬러 팔레트 다크모드 대비 검증", "type": "design", "icon": "🌙", "weight": 1},
        ],
    },
    "hajun": {
        "role": "콘텐츠PD",
        "actions": [
            {"action": "이번 주 콘텐츠 캘린더 검토", "type": "content", "icon": "📝", "weight": 3},
            {"action": "미발행 원고 품질 자가 점검", "type": "content", "icon": "✍️", "weight": 2},
            {"action": "트렌드 키워드 기반 콘텐츠 아이디어 메모", "type": "content", "icon": "💡", "weight": 1},
        ],
    },
    "eunseo": {
        "role": "카피라이터",
        "actions": [
            {"action": "앱스토어 설명문 A/B 테스트 아이디어 정리", "type": "content", "icon": "📱", "weight": 2},
            {"action": "푸시 알림 문구 최적화 초안 작성", "type": "content", "icon": "🔔", "weight": 3},
            {"action": "랜딩페이지 CTA 문구 리프레시", "type": "content", "icon": "✨", "weight": 1},
        ],
    },
    "jiyeon": {
        "role": "마케터",
        "actions": [
            {"action": "SNS 채널별 이번 주 성과 분석", "type": "analysis", "icon": "📈", "weight": 3},
            {"action": "인플루언서 협업 리스트 업데이트", "type": "analysis", "icon": "🤝", "weight": 2},
            {"action": "경쟁사 소셜 미디어 동향 모니터링", "type": "analysis", "icon": "👀", "weight": 1},
        ],
    },
    "doyun": {
        "role": "SEO전문가",
        "actions": [
            {"action": "핵심 키워드 검색 순위 변동 체크", "type": "analysis", "icon": "🔍", "weight": 3},
            {"action": "메타태그/OG 태그 최적화 상태 점검", "type": "analysis", "icon": "🏷️", "weight": 2},
            {"action": "사이트맵 갱신 필요 여부 확인", "type": "analysis", "icon": "🗺️", "weight": 1},
        ],
    },
    "siwoo": {
        "role": "비즈전략가",
        "actions": [
            {"action": "월간 유닛 이코노믹스 시뮬레이션", "type": "report", "icon": "💰", "weight": 2},
            {"action": "수익 모델 개선 아이디어 메모", "type": "report", "icon": "💡", "weight": 3},
            {"action": "경쟁사 가격 정책 벤치마킹", "type": "report", "icon": "📊", "weight": 1},
        ],
    },
    "junseo": {
        "role": "자동화엔지니어",
        "actions": [
            {"action": "CI/CD 파이프라인 상태 점검", "type": "scan", "icon": "⚙️", "weight": 3},
            {"action": "서버 리소스 사용량 모니터링 리포트", "type": "scan", "icon": "📡", "weight": 2},
            {"action": "반복 업무 자동화 기회 탐색", "type": "scan", "icon": "🤖", "weight": 1},
        ],
    },
    "chaewon": {
        "role": "QA엔지니어",
        "actions": [
            {"action": "회귀 테스트 체크리스트 업데이트", "type": "scan", "icon": "✅", "weight": 3},
            {"action": "크로스 플랫폼 호환성 자가 점검", "type": "scan", "icon": "📱", "weight": 2},
            {"action": "미해결 버그 티켓 우선순위 재분류", "type": "scan", "icon": "🐛", "weight": 1},
        ],
    },
    "yejun": {
        "role": "데이터분석가",
        "actions": [
            {"action": "주간 DAU/MAU 트렌드 분석 리포트 생성", "type": "analysis", "icon": "📊", "weight": 3},
            {"action": "퍼널 이탈 구간 분석", "type": "analysis", "icon": "🔍", "weight": 2},
            {"action": "코호트 리텐션 변화 추적", "type": "analysis", "icon": "📈", "weight": 1},
        ],
    },
    "soyul": {
        "role": "BI분석가",
        "actions": [
            {"action": "매출/비용 추이 대시보드 스냅샷 생성", "type": "analysis", "icon": "💰", "weight": 3},
            {"action": "LTV/CAC 비율 업데이트", "type": "analysis", "icon": "📉", "weight": 2},
            {"action": "부서별 예산 소진률 점검", "type": "analysis", "icon": "🧮", "weight": 1},
        ],
    },
    "yuna": {
        "role": "시장조사관",
        "actions": [
            {"action": "경쟁사 신규 기능 출시 모니터링", "type": "analysis", "icon": "🔬", "weight": 3},
            {"action": "반려동물/블로그 시장 트렌드 요약", "type": "analysis", "icon": "📰", "weight": 2},
            {"action": "신규 시장 기회 리서치 메모", "type": "analysis", "icon": "🌍", "weight": 1},
        ],
    },
    "daeun": {
        "role": "CS매니저",
        "actions": [
            {"action": "미답변 고객 문의 알림 점검", "type": "report", "icon": "📬", "weight": 3},
            {"action": "앱스토어 최신 리뷰 감정 분석", "type": "report", "icon": "⭐", "weight": 2},
            {"action": "FAQ 업데이트 필요 항목 식별", "type": "report", "icon": "❓", "weight": 1},
        ],
    },
    "jiho": {
        "role": "커뮤니티매니저",
        "actions": [
            {"action": "커뮤니티 활성 유저 동향 점검", "type": "report", "icon": "👥", "weight": 3},
            {"action": "이번 주 UGC 하이라이트 선별", "type": "report", "icon": "🏆", "weight": 2},
            {"action": "핵심 유저 리텐션 프로그램 아이디어 정리", "type": "report", "icon": "💎", "weight": 1},
        ],
    },
}


def _select_action(employee_id: str) -> dict | None:
    """가중치 기반 랜덤 행동 선택"""
    config = AUTONOMOUS_ACTIONS.get(employee_id)
    if not config:
        return None
    actions = config["actions"]
    weights = [a["weight"] for a in actions]
    return random.choices(actions, weights=weights, k=1)[0]


def _is_on_cooldown(employee_id: str) -> bool:
    """쿨다운 중인지 확인"""
    last = _cooldowns.get(employee_id)
    if not last:
        return False
    return datetime.now() - last < timedelta(minutes=_MIN_COOLDOWN_MINUTES)


def run_autonomous_tick(employees: list, tracker, add_log_fn, memory=None):
    """
    자율 행동 틱 — 스케줄러에서 주기적 호출.
    전 직원 중 2~5명이 랜덤으로 자율 행동을 수행합니다.
    """
    with _engine_lock:
        available = [e for e in employees if not _is_on_cooldown(e["id"])]
        if not available:
            return {"triggered": 0, "reason": "all_on_cooldown"}

        count = min(random.randint(2, 5), len(available))
        selected = random.sample(available, count)
        results = []

        for emp in selected:
            action = _select_action(emp["id"])
            if not action:
                continue

            # 활동 로그 기록
            add_log_fn(
                emp["id"], emp["name"], emp["department"],
                action["action"], action["type"], action["icon"]
            )

            # 실시간 통계
            tracker.record_activity(emp["id"], action["type"])

            # 쿨다운 설정
            _cooldowns[emp["id"]] = datetime.now()

            entry = {
                "employee_id": emp["id"],
                "employee_name": emp["name"],
                "role": emp["role"],
                "action": action["action"],
                "icon": action["icon"],
                "timestamp": datetime.now().isoformat(),
            }
            _action_history.insert(0, entry)
            results.append(entry)

        # 기억 저장
        if memory and results:
            names = ", ".join(r["employee_name"] for r in results)
            memory.remember(
                f"자율 행동: {names}이(가) 각자 업무를 자발적으로 수행함",
                source_type="autonomy",
                employee_id="system",
            )

        # 히스토리 관리
        if len(_action_history) > _max_history:
            del _action_history[_max_history:]

        return {"triggered": len(results), "actions": results}


def get_autonomy_status() -> dict:
    """자율 행동 엔진 상태"""
    now = datetime.now()
    cooldown_info = {
        eid: {
            "on_cooldown": _is_on_cooldown(eid),
            "remaining_sec": max(0, int((_MIN_COOLDOWN_MINUTES * 60) - (now - ts).total_seconds()))
        }
        for eid, ts in _cooldowns.items()
    }
    return {
        "total_actions": len(_action_history),
        "cooldown_minutes": _MIN_COOLDOWN_MINUTES,
        "cooldowns": cooldown_info,
        "recent_actions": _action_history[:10],
    }


def get_autonomy_history(limit: int = 20) -> list[dict]:
    """자율 행동 이력"""
    return _action_history[:limit]
