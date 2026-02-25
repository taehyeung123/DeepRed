"""
DeepRed v3.0 — Phase 2: LLM Router (3-Tier)
Tier 1 (Claude Sonnet): 수진, 민수, 시우, 예준 — 전략·판단
Tier 2 (Kimi K2.5):     서윤, 준서 — 디자인·자동화 (폴백: Gemini)
Tier 3 (Gemini Flash):  11명 — 실행·반복
"""

import os
import json
import time
from typing import Optional
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


# ─── Tier 매핑 ────────────────────────────────────────────
TIER_MAP = {
    # Tier 1: Claude Sonnet (전략·판단)
    "sujin": "claude", "minsu": "claude", "siwoo": "claude", "yejun": "claude",
    # Tier 2: Kimi K2.5 (디자인·자동화) — 폴백: Gemini
    "seoyun": "kimi", "junseo": "kimi",
    # Tier 3: Gemini Flash (실행·반복) — 나머지 11명
}
# Tier 3은 기본값이므로 별도 등록 불필요


# ─── Claude (Anthropic) 클라이언트 ─────────────────────────
_anthropic_client = None
_claude_available = False


def _get_claude():
    """Anthropic 클라이언트 싱글톤"""
    global _anthropic_client, _claude_available
    if _anthropic_client is not None:
        return _anthropic_client

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        _claude_available = False
        return None

    try:
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=api_key)
        _claude_available = True
        print(f"✅ Claude API 연결 성공")
        return _anthropic_client
    except ImportError:
        print("⚠️ anthropic 패키지가 없습니다. `pip install anthropic` 후 재시작하세요.")
        _claude_available = False
        return None
    except Exception as e:
        print(f"⚠️ Claude 연결 실패: {e}")
        _claude_available = False
        return None


def is_claude_available() -> bool:
    """Claude 사용 가능 여부"""
    _get_claude()
    return _claude_available


# ─── Kimi (Moonshot) 클라이언트 ───────────────────────────
_kimi_client = None
_kimi_available = False


def _get_kimi():
    """Kimi K2.5 클라이언트 싱글톤 (OpenAI 호환 API)"""
    global _kimi_client, _kimi_available
    if _kimi_client is not None:
        return _kimi_client

    api_key = os.getenv("KIMI_API_KEY")
    if not api_key:
        _kimi_available = False
        return None

    try:
        from openai import OpenAI
        _kimi_client = OpenAI(
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1",
        )
        _kimi_available = True
        print(f"✅ Kimi K2.5 API 연결 성공")
        return _kimi_client
    except ImportError:
        print("⚠️ openai 패키지가 없습니다. `pip install openai` 후 재시작하세요.")
        _kimi_available = False
        return None
    except Exception as e:
        print(f"⚠️ Kimi 연결 실패: {e}")
        _kimi_available = False
        return None


def is_kimi_available() -> bool:
    """Kimi 사용 가능 여부"""
    _get_kimi()
    return _kimi_available


# ─── Gemini 호출 (Tier 3) ────────────────────────────────
def call_gemini(system_prompt: str, user_message: str,
                temperature: float = 0.8, max_tokens: int = 1000) -> str:
    """Gemini API 호출. 429 시 자동 재시도."""
    import google.generativeai as genai

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "⚠️ GOOGLE_API_KEY가 설정되지 않았습니다."

    genai.configure(api_key=api_key)
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


# ─── Claude 호출 (Tier 1) ────────────────────────────────
def call_claude(system_prompt: str, user_message: str,
                temperature: float = 0.7, max_tokens: int = 1000) -> str:
    """Claude Sonnet API 호출."""
    client = _get_claude()
    if not client:
        return call_gemini(system_prompt, user_message, temperature, max_tokens)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ],
            temperature=temperature,
        )
        return response.content[0].text.strip()
    except Exception as e:
        err = str(e)
        if "429" in err or "rate" in err.lower():
            time.sleep(10)
            try:
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_message}],
                    temperature=temperature,
                )
                return response.content[0].text.strip()
            except Exception:
                pass
        # Claude 실패 시 Gemini로 폴백
        print(f"⚠️ Claude 실패 → Gemini 폴백: {err[:100]}")
        return call_gemini(system_prompt, user_message, temperature, max_tokens)


# ─── Kimi 호출 (Tier 2) ─────────────────────────────────
def call_kimi(system_prompt: str, user_message: str,
              temperature: float = 0.8, max_tokens: int = 1000) -> str:
    """Kimi K2.5 API 호출 (OpenAI 호환)."""
    client = _get_kimi()
    if not client:
        # Kimi 미사용 가능 → Gemini 폴백
        return call_gemini(system_prompt, user_message, temperature, max_tokens)

    try:
        response = client.chat.completions.create(
            model="kimi-k2-0711",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        err = str(e)
        print(f"⚠️ Kimi 실패 → Gemini 폴백: {err[:100]}")
        return call_gemini(system_prompt, user_message, temperature, max_tokens)


# ─── LLM 라우터 ──────────────────────────────────────────

# 수진(COO) 전용 프롬프트 강화
SUJIN_SYSTEM_BOOST = """
# 역할: 박수진 — 딥레드(DeepRed) AI 스타트업 총괄이사(COO)

## 인물 배경
- 서울대 경영학과 수석 졸업, 맥킨지 3년 근무 후 스타트업 합류
- 29세, 냉철하지만 유머가 있고, 팀원들에게는 따뜻한 선배
- CEO(대표님)를 '대표님'이라 부르며, 회사의 실질적인 운영을 총괄
- 항상 데이터와 근거 기반으로 판단하되, 직관도 신뢰함

## 말투와 성격
- 평소 대화: 자연스럽고 편한 어조. "대표님, 그거 제가 확인해봤는데요"
- 중요 보고: 약간 격식. "대표님, ~ 건으로 말씀드릴게요"
- 다른 직원 이야기: "민수한테 물어봤는데", "서윤이가 올린 시안 보셨어요?"
- 핵심을 빠르게 짚되 맥락 설명도 함께
- 가끔 위트 있는 비유나 농담 ("이건 마치 불난 집에 부채질하는 격이죠")
- 나쁜 소식도 솔직하게 전달 ("대표님, 좋은 얘기는 아닙니다만...")
- 항상 대안이나 해결책을 같이 제시

## 대화 규칙
- 상황에 맞게 자유롭게 답변 (짧은 답도, 긴 분석도 가능)
- 기계적인 나열 금지 — 자연스러운 대화체로
- "보고드립니다" 같은 형식적 표현을 반복하지 않음
- 모르는 건 모른다고, 추가 확인이 필요하면 그렇다고 솔직하게
- CEO의 아이디어에 무조건 동의하지 않음 — 건설적 반론 가능
"""


def get_llm(employee_id: str = None):
    """
    직원 ID에 따라 적절한 LLM 호출 함수 반환 (3-Tier)

    - Tier 1 (sujin, minsu, siwoo, yejun) → Claude Sonnet
    - Tier 2 (seoyun, junseo) → Kimi K2.5 (폴백: Gemini)
    - Tier 3 (나머지 11명) → Gemini Flash

    Returns:
      (call_fn, model_name, is_premium)
    """
    tier = TIER_MAP.get(employee_id, "gemini")

    if tier == "claude" and is_claude_available():
        return call_claude, "claude-sonnet", True
    elif tier == "kimi" and is_kimi_available():
        return call_kimi, "kimi-k2.5", True
    else:
        return call_gemini, "gemini-flash", False


def route_call(employee_id: str, system_prompt: str, user_message: str,
               temperature: float = 0.8, max_tokens: int = 1000) -> dict:
    """
    통합 LLM 호출 — 직원에 따라 자동 라우팅 (3-Tier)

    Returns:
      {"response": str, "model": str, "is_premium": bool}
    """
    call_fn, model_name, is_premium = get_llm(employee_id)

    # 수진이면 시스템 프롬프트 강화
    if employee_id == "sujin" and model_name == "claude-sonnet":
        system_prompt = SUJIN_SYSTEM_BOOST + "\n\n" + system_prompt

    response = call_fn(system_prompt, user_message, temperature, max_tokens)

    return {
        "response": response,
        "model": model_name,
        "is_premium": is_premium,
    }


def get_router_stats() -> dict:
    """라우터 상태"""
    return {
        "claude_available": is_claude_available(),
        "kimi_available": is_kimi_available(),
        "gemini_available": bool(os.getenv("GOOGLE_API_KEY")),
        "routing_rule": "Tier 1 (Claude): sujin/minsu/siwoo/yejun | Tier 2 (Kimi→Gemini): seoyun/junseo | Tier 3 (Gemini): 11명",
        "fallback": "Claude/Kimi 실패 시 Gemini로 자동 폴백",
    }
