"""
DeepRed v3.0 — RedRank 운영 데이터 커넥터
RedRank Supabase에서 운영 지표를 읽어와 직원별로 필요한 데이터만 제공.
토큰 최적화를 위해 요약 형태로 반환.
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


# ─── RedRank Supabase 설정 ─────────────────────────────────
REDRANK_SUPABASE_URL = os.getenv("REDRANK_SUPABASE_URL", "")
REDRANK_SUPABASE_KEY = os.getenv("REDRANK_SUPABASE_KEY", "")  # service_role key


def _supabase_query(table: str, select: str = "*",
                    filters: dict = None, order: str = None,
                    limit: int = 100) -> list:
    """RedRank Supabase REST API 직접 호출"""
    if not REDRANK_SUPABASE_URL or not REDRANK_SUPABASE_KEY:
        return []

    url = f"{REDRANK_SUPABASE_URL}/rest/v1/{table}?select={select}"

    if filters:
        for key, value in filters.items():
            url += f"&{key}={value}"
    if order:
        url += f"&order={order}"
    if limit:
        url += f"&limit={limit}"

    req = urllib.request.Request(url, headers={
        "apikey": REDRANK_SUPABASE_KEY,
        "Authorization": f"Bearer {REDRANK_SUPABASE_KEY}",
        "Content-Type": "application/json",
    })

    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read().decode())
    except Exception as e:
        print(f"⚠️ RedRank Supabase 조회 오류: {e}")
        return []


# ─── 데이터 수집 함수들 ───────────────────────────────────────

def get_total_users() -> dict:
    """전체 사용자 수 및 플랜별 분포"""
    profiles = _supabase_query("profiles", select="id,plan,created_at")
    if not profiles:
        return {"total": 0, "by_plan": {}, "available": False}

    by_plan = {}
    for p in profiles:
        plan = p.get("plan", "free")
        by_plan[plan] = by_plan.get(plan, 0) + 1

    # 최근 7일 신규 가입
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    new_users = sum(1 for p in profiles
                    if p.get("created_at", "") > week_ago)

    return {
        "total": len(profiles),
        "by_plan": by_plan,
        "new_users_7d": new_users,
        "available": True,
    }


def get_revenue_stats() -> dict:
    """매출 관련 지표 (코인 구매, 구독)"""
    # 코인 트랜잭션에서 구매 내역 조회
    txns = _supabase_query(
        "coin_transactions",
        select="amount,type,created_at",
        filters={"type": "eq.purchase"},
        order="created_at.desc",
        limit=500,
    )

    total_revenue = 0
    monthly_revenue = {}
    for t in txns:
        amount = abs(t.get("amount", 0))
        total_revenue += amount
        month_key = t.get("created_at", "")[:7]  # YYYY-MM
        monthly_revenue[month_key] = monthly_revenue.get(month_key, 0) + amount

    # 구독 현황
    profiles = _supabase_query("profiles", select="plan")
    plan_counts = {}
    for p in profiles:
        plan = p.get("plan", "free")
        plan_counts[plan] = plan_counts.get(plan, 0) + 1

    return {
        "total_coin_purchases": total_revenue,
        "monthly_coin_purchases": monthly_revenue,
        "subscription_distribution": plan_counts,
        "available": bool(txns or profiles),
    }


def get_usage_stats() -> dict:
    """기능별 사용 현황"""
    today = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    # 오늘 사용량
    today_usage = _supabase_query(
        "daily_usage",
        select="usage",
        filters={"date": f"eq.{today}"},
    )

    # 주간 사용량
    week_usage = _supabase_query(
        "daily_usage",
        select="usage,date",
        filters={"date": f"gte.{week_ago}"},
        limit=1000,
    )

    # 기능별 집계
    feature_totals_today = {}
    for row in today_usage:
        usage = row.get("usage", {})
        if isinstance(usage, str):
            try:
                usage = json.loads(usage)
            except:
                continue
        for feat, count in usage.items():
            feature_totals_today[feat] = feature_totals_today.get(feat, 0) + count

    feature_totals_week = {}
    for row in week_usage:
        usage = row.get("usage", {})
        if isinstance(usage, str):
            try:
                usage = json.loads(usage)
            except:
                continue
        for feat, count in usage.items():
            feature_totals_week[feat] = feature_totals_week.get(feat, 0) + count

    return {
        "today": feature_totals_today,
        "weekly": feature_totals_week,
        "dau_today": len(today_usage),
        "wau": len(set(r.get("uid", "") for r in week_usage if r.get("uid"))),
        "available": bool(today_usage or week_usage),
    }


def get_activity_overview() -> dict:
    """최근 활동 요약"""
    activities = _supabase_query(
        "activity_logs",
        select="activity_type,created_at",
        order="created_at.desc",
        limit=500,
    )

    # 활동 타입별 집계
    type_counts = {}
    for a in activities:
        atype = a.get("activity_type", "unknown")
        type_counts[atype] = type_counts.get(atype, 0) + 1

    return {
        "total_activities_recent": len(activities),
        "by_type": type_counts,
        "available": bool(activities),
    }


# ─── 직원별 데이터 접근 권한 ─────────────────────────────────

# 각 직원이 볼 수 있는 데이터 카테고리
EMPLOYEE_DATA_ACCESS = {
    # 컨트롤 타워 — 수진: 전체
    "sujin": ["users", "revenue", "usage", "activity"],

    # 전략 기획실
    "minsu": ["users", "usage"],         # 기능별 사용률, DAU, 신규 가입
    "siwoo": ["revenue", "users"],       # 매출, 구독 전환율, ARPU
    "yejun": ["users", "revenue", "usage", "activity"],  # 전체 KPI

    # 프로덕트 랩
    "seoyun": ["usage"],                 # UX 지표 (기능별 사용률)
    "junseo": [],                        # 코드만 (운영 데이터 불필요)

    # 콘텐츠 & 그로스
    "hajun": ["activity"],               # 콘텐츠 활동
    "eunseo": ["usage"],                 # CTA 클릭률 관련
    "jiyeon": ["users"],                 # 유입 채널
    "doyun": ["activity"],               # SEO 활동

    # 보안 & 품질
    "taehyun": ["users", "activity"],    # 보안 이상 감지
    "chaewon": ["usage", "activity"],    # 품질 검수

    # 분석 & 리서치
    "jieun": ["revenue"],                # 재무 리포트
    "soyul": ["users", "revenue", "usage", "activity"],  # BI 대시보드
    "yuna": ["users"],                   # 시장 점유율

    # 고객 경험
    "daeun": ["activity"],               # 고객 문의/피드백
    "jiho": ["users", "activity"],       # 커뮤니티 활동
}


def get_data_for_employee(employee_id: str) -> str:
    """
    직원의 데이터 접근 권한에 맞는 운영 데이터를 요약 텍스트로 반환.
    채팅 시 시스템 프롬프트에 주입됨.
    """
    access = EMPLOYEE_DATA_ACCESS.get(employee_id, [])
    if not access:
        return ""

    if not REDRANK_SUPABASE_URL:
        return ""

    parts = ["[레드랭크 운영 현황]"]

    if "users" in access:
        users = get_total_users()
        if users.get("available"):
            parts.append(
                f"\n👥 사용자: 총 {users['total']}명"
                f" | 플랜별: {', '.join(f'{k}:{v}명' for k, v in users['by_plan'].items())}"
                f" | 신규(7일): {users.get('new_users_7d', 0)}명"
            )

    if "revenue" in access:
        rev = get_revenue_stats()
        if rev.get("available"):
            parts.append(
                f"\n💰 코인 구매: 총 {rev['total_coin_purchases']}코인"
                f" | 구독 분포: {', '.join(f'{k}:{v}명' for k, v in rev['subscription_distribution'].items())}"
            )

    if "usage" in access:
        usage = get_usage_stats()
        if usage.get("available"):
            top_features = sorted(
                usage.get("weekly", {}).items(),
                key=lambda x: x[1], reverse=True
            )[:5]
            features_str = ", ".join(f"{k}:{v}회" for k, v in top_features)
            parts.append(
                f"\n📊 DAU: {usage['dau_today']}명 | WAU: {usage['wau']}명"
                f"\n   주간 인기 기능: {features_str}"
            )

    if "activity" in access:
        act = get_activity_overview()
        if act.get("available"):
            top_acts = sorted(
                act.get("by_type", {}).items(),
                key=lambda x: x[1], reverse=True
            )[:5]
            acts_str = ", ".join(f"{k}:{v}" for k, v in top_acts)
            parts.append(f"\n🔄 최근 활동: {acts_str}")

    return "\n".join(parts) if len(parts) > 1 else ""


def is_available() -> bool:
    """RedRank 데이터 연결 가능 여부"""
    return bool(REDRANK_SUPABASE_URL and REDRANK_SUPABASE_KEY)
