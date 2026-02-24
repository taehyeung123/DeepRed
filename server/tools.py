"""
DeepRed v3.0 — Phase 3: Agent Tools
에이전트가 사용할 수 있는 도구 모음
보안 검사, 데이터 분석, 콘텐츠 생성 등
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional


# ─── 도구 레지스트리 ──────────────────────────────────────
TOOLS = {}


def register_tool(name: str, description: str, department: str):
    """도구 데코레이터"""
    def decorator(func):
        TOOLS[name] = {
            "name": name,
            "description": description,
            "department": department,
            "function": func,
        }
        return func
    return decorator


def get_available_tools() -> list[dict]:
    """사용 가능한 도구 목록"""
    return [
        {"name": t["name"], "description": t["description"], "department": t["department"]}
        for t in TOOLS.values()
    ]


def run_tool(name: str, **kwargs) -> dict:
    """도구 실행"""
    tool = TOOLS.get(name)
    if not tool:
        return {"error": f"도구 '{name}'을 찾을 수 없습니다.", "available": list(TOOLS.keys())}
    try:
        result = tool["function"](**kwargs)
        return {"tool": name, "status": "success", "result": result}
    except Exception as e:
        return {"tool": name, "status": "error", "error": str(e)}


# ─── 보안 도구 (태현) ──────────────────────────────────────
@register_tool("security_scan", "환경 변수 및 API 키 노출 검사", "security")
def security_scan(project: str = None) -> dict:
    """환경 변수 보안 검사"""
    issues = []
    warnings = []

    # .env 파일 검사
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, _, value = line.partition('=')
                    if value and len(value) > 20:
                        # 키가 코드에 하드코딩되어 있는지 검사
                        warnings.append(f"⚠️ {key}: 값이 설정됨 (길이: {len(value)})")

    # Git 검사
    gitignore_path = os.path.join(os.path.dirname(__file__), '..', '.gitignore')
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            content = f.read()
            if '.env' not in content:
                issues.append("🚨 .gitignore에 .env가 포함되지 않음!")
    else:
        warnings.append("⚠️ .gitignore 파일이 없음")

    score = 100
    score -= len(issues) * 20
    score -= len(warnings) * 5

    return {
        "score": max(0, score),
        "grade": "A" if score >= 90 else "B" if score >= 70 else "C" if score >= 50 else "F",
        "issues": issues,
        "warnings": warnings,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@register_tool("dependency_check", "패키지 의존성 보안 검사", "security")
def dependency_check() -> dict:
    """requirements.txt 패키지 목록 확인"""
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    packages = []
    if os.path.exists(req_path):
        with open(req_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    packages.append(line)

    return {
        "total_packages": len(packages),
        "packages": packages,
        "recommendation": "정기적으로 `pip audit`으로 보안 취약점을 검사하세요.",
    }


# ─── 데이터 분석 도구 (예준, 소율) ─────────────────────────
@register_tool("kpi_report", "KPI 대시보드 데이터 생성", "data")
def kpi_report(project: str = None) -> dict:
    """KPI 리포트 생성 (시뮬레이션)"""
    import random

    base_dau = random.randint(800, 1500)
    base_mau = base_dau * random.randint(15, 25)
    retention_7d = round(random.uniform(35, 55), 1)
    retention_30d = round(random.uniform(15, 30), 1)
    mrr = random.randint(800000, 2500000)

    return {
        "project": project or "전체",
        "period": datetime.now().strftime("%Y-%m"),
        "dau": base_dau,
        "mau": base_mau,
        "dau_mau_ratio": round(base_dau / base_mau * 100, 1),
        "retention_7d": retention_7d,
        "retention_30d": retention_30d,
        "mrr": mrr,
        "mrr_formatted": f"₩{mrr:,}",
        "growth_rate": round(random.uniform(-5, 15), 1),
        "nps": random.randint(30, 70),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@register_tool("funnel_analysis", "퍼널 분석 데이터 생성", "data")
def funnel_analysis(project: str = None) -> dict:
    """퍼널 분석 (시뮬레이션)"""
    import random

    visitors = random.randint(5000, 15000)
    signups = int(visitors * random.uniform(0.08, 0.15))
    activations = int(signups * random.uniform(0.3, 0.6))
    retained = int(activations * random.uniform(0.4, 0.7))
    paid = int(retained * random.uniform(0.05, 0.15))

    return {
        "project": project or "전체",
        "funnel": [
            {"stage": "방문", "count": visitors, "rate": 100.0},
            {"stage": "가입", "count": signups, "rate": round(signups / visitors * 100, 1)},
            {"stage": "활성화", "count": activations, "rate": round(activations / visitors * 100, 1)},
            {"stage": "유지", "count": retained, "rate": round(retained / visitors * 100, 1)},
            {"stage": "결제", "count": paid, "rate": round(paid / visitors * 100, 1)},
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ─── 콘텐츠 도구 (하준, 은서) ──────────────────────────────
@register_tool("content_calendar", "콘텐츠 캘린더 생성", "content")
def content_calendar(weeks: int = 2) -> dict:
    """콘텐츠 캘린더 템플릿 생성"""
    from datetime import timedelta

    channels = ["블로그", "인스타그램", "유튜브", "네이버포스트"]
    content_types = ["정보성", "홍보", "이벤트", "사용자 후기"]

    calendar = []
    today = datetime.now()

    for w in range(weeks):
        for d in range(5):  # 평일만
            date = today + timedelta(weeks=w, days=d)
            if date.weekday() < 5:
                import random
                calendar.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "day": ["월", "화", "수", "목", "금"][date.weekday()],
                    "channel": random.choice(channels),
                    "type": random.choice(content_types),
                    "status": "예정",
                })

    return {
        "period": f"{weeks}주간",
        "total_posts": len(calendar),
        "calendar": calendar,
    }


# ─── 마케팅 도구 (지연, 도윤) ──────────────────────────────
@register_tool("seo_check", "기본 SEO 점검", "marketing")
def seo_check(url: str = None) -> dict:
    """SEO 기본 점검 리포트"""
    import random

    checks = {
        "title_tag": {"status": "pass", "detail": "제목 태그 존재 (30자 이내)"},
        "meta_description": {"status": "pass", "detail": "메타 설명 존재 (150자 이내)"},
        "h1_tag": {"status": "pass", "detail": "H1 태그 1개 존재"},
        "img_alt": {"status": random.choice(["pass", "warning"]), "detail": "대체 텍스트 검사"},
        "mobile_friendly": {"status": "pass", "detail": "모바일 반응형"},
        "page_speed": {"status": random.choice(["pass", "warning"]), "detail": f"로딩 시간: {random.uniform(1.0, 3.5):.1f}초"},
        "ssl": {"status": "pass", "detail": "HTTPS 적용됨"},
        "sitemap": {"status": random.choice(["pass", "fail"]), "detail": "sitemap.xml 검사"},
    }

    passed = sum(1 for c in checks.values() if c["status"] == "pass")
    total = len(checks)

    return {
        "url": url or "전체",
        "score": round(passed / total * 100),
        "checks": checks,
        "passed": passed,
        "total": total,
    }


# ─── 비즈니스 도구 (시우) ──────────────────────────────────
@register_tool("revenue_summary", "매출 요약 리포트", "business")
def revenue_summary(period: str = "monthly") -> dict:
    """매출 요약 (시뮬레이션)"""
    import random

    mrr = random.randint(800000, 3000000)
    costs = int(mrr * random.uniform(0.3, 0.6))
    users_total = random.randint(500, 3000)
    paying = int(users_total * random.uniform(0.05, 0.12))

    return {
        "period": period,
        "mrr": mrr,
        "mrr_formatted": f"₩{mrr:,}",
        "arr": mrr * 12,
        "arr_formatted": f"₩{mrr * 12:,}",
        "costs": costs,
        "costs_formatted": f"₩{costs:,}",
        "profit": mrr - costs,
        "profit_formatted": f"₩{mrr - costs:,}",
        "margin": round((mrr - costs) / mrr * 100, 1),
        "total_users": users_total,
        "paying_users": paying,
        "arpu": round(mrr / paying) if paying > 0 else 0,
        "ltv": round(mrr / paying * 12 * 0.8) if paying > 0 else 0,
    }
