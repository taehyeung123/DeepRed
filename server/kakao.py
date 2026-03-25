"""
DeepRed v3.1 — 카카오 나에게 보내기 연동
OAuth2 토큰 관리 + 메시지 전송
"""

import os
import json
import time
import threading
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# ─── 카카오 설정 ──────────────────────────────────────────
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY", "")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET", "")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:8000/api/kakao/callback")

# 토큰 저장 (파일 기반 — Docker volume으로 영구 보존)
_DATA_DIR = os.getenv("DATA_DIR", ".")
_TOKEN_FILE = os.path.join(_DATA_DIR, "kakao_tokens.json")
_lock = threading.Lock()

_tokens: dict = {
    "access_token": "",
    "refresh_token": "",
    "expires_at": 0,
    "refresh_expires_at": 0,
}


# ─── 토큰 파일 관리 ──────────────────────────────────────

def _load_tokens():
    """파일에서 토큰 로드"""
    global _tokens
    try:
        if os.path.exists(_TOKEN_FILE):
            with open(_TOKEN_FILE, "r") as f:
                _tokens = json.load(f)
                print(f"📱 카카오 토큰 로드됨 (만료: {datetime.fromtimestamp(_tokens.get('expires_at', 0)).strftime('%H:%M')})")
    except Exception as e:
        print(f"⚠️ 카카오 토큰 로드 실패: {e}")


def _save_tokens():
    """토큰을 파일에 저장"""
    try:
        os.makedirs(os.path.dirname(_TOKEN_FILE) or ".", exist_ok=True)
        with open(_TOKEN_FILE, "w") as f:
            json.dump(_tokens, f)
    except Exception as e:
        print(f"⚠️ 카카오 토큰 저장 실패: {e}")


# 시작 시 토큰 로드
_load_tokens()


# ─── 카카오 OAuth ────────────────────────────────────────

def get_auth_url() -> str:
    """카카오 로그인 URL 생성 — 대표님이 브라우저에서 접속"""
    return (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={KAKAO_REST_API_KEY}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=talk_message"
    )


def exchange_code(auth_code: str) -> dict:
    """인증 코드 → access_token + refresh_token 교환"""
    import urllib.request
    import urllib.parse
    import urllib.error

    params = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_REST_API_KEY,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": auth_code,
    }
    if KAKAO_CLIENT_SECRET:
        params["client_secret"] = KAKAO_CLIENT_SECRET

    data = urllib.parse.urlencode(params).encode()

    req = urllib.request.Request(
        "https://kauth.kakao.com/oauth/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())

        with _lock:
            _tokens["access_token"] = result["access_token"]
            _tokens["refresh_token"] = result.get("refresh_token", "")
            _tokens["expires_at"] = time.time() + result.get("expires_in", 21600)
            _tokens["refresh_expires_at"] = time.time() + result.get("refresh_token_expires_in", 5184000)
            _save_tokens()

        print(f"✅ 카카오 토큰 발급 완료 (유효: {result.get('expires_in', 0) // 3600}시간)")
        return {"success": True, "expires_in": result.get("expires_in", 0)}

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")
        print(f"❌ 카카오 토큰 발급 실패: HTTP {e.code} — {error_body}")
        return {"success": False, "error": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        print(f"❌ 카카오 토큰 발급 실패: {e}")
        return {"success": False, "error": str(e)}


def _refresh_token() -> bool:
    """만료된 access_token을 refresh_token으로 갱신"""
    import urllib.request
    import urllib.parse

    if not _tokens.get("refresh_token"):
        print("⚠️ 카카오 refresh_token 없음 — 재인증 필요")
        return False

    params = {
        "grant_type": "refresh_token",
        "client_id": KAKAO_REST_API_KEY,
        "refresh_token": _tokens["refresh_token"],
    }
    if KAKAO_CLIENT_SECRET:
        params["client_secret"] = KAKAO_CLIENT_SECRET

    data = urllib.parse.urlencode(params).encode()

    req = urllib.request.Request(
        "https://kauth.kakao.com/oauth/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())

        with _lock:
            _tokens["access_token"] = result["access_token"]
            _tokens["expires_at"] = time.time() + result.get("expires_in", 21600)
            # refresh_token도 갱신된 경우
            if "refresh_token" in result:
                _tokens["refresh_token"] = result["refresh_token"]
                _tokens["refresh_expires_at"] = time.time() + result.get("refresh_token_expires_in", 5184000)
            _save_tokens()

        print(f"🔄 카카오 토큰 갱신 완료")
        return True

    except Exception as e:
        print(f"❌ 카카오 토큰 갱신 실패: {e}")
        return False


def _get_valid_token() -> Optional[str]:
    """유효한 access_token 반환 (만료 시 자동 갱신)"""
    with _lock:
        token = _tokens.get("access_token", "")
        expires_at = _tokens.get("expires_at", 0)

    if not token:
        return None

    # 만료 5분 전이면 갱신
    if time.time() > expires_at - 300:
        if not _refresh_token():
            return None
        with _lock:
            token = _tokens.get("access_token", "")

    return token


# ─── 메시지 전송 ──────────────────────────────────────────

def is_kakao_available() -> bool:
    """카카오 나에게 보내기 — 비활성화됨 (2026-03-20)"""
    return False  # 카카오 알림 완전 비활성화


def send_to_me(text: str, web_url: str = "https://deepred.vercel.app") -> dict:
    """
    카카오 나에게 보내기 — 텍스트 메시지 전송
    알림은 안 뜨지만 '나와의 채팅'에 메시지가 기록됨
    """
    # ⛔ 카카오 알림 비활성화 — 어디서 호출하든 차단
    if not is_kakao_available():
        print("⛔ 카카오 알림 비활성화 상태 — 메시지 전송 차단됨")
        return {"success": False, "error": "카카오 알림이 비활성화되어 있습니다."}

    import urllib.request
    import urllib.parse

    token = _get_valid_token()
    if not token:
        return {"success": False, "error": "카카오 토큰 없음 — /api/kakao/auth 에서 인증 필요"}

    # 텍스트 500자 제한
    text = text[:500] if len(text) > 500 else text

    template = json.dumps({
        "object_type": "text",
        "text": text,
        "link": {
            "web_url": web_url,
            "mobile_web_url": web_url,
        },
    }, ensure_ascii=False)

    data = urllib.parse.urlencode({
        "template_object": template,
    }).encode()

    req = urllib.request.Request(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())

        if result.get("result_code") == 0:
            print(f"📨 카카오 전송 성공")
            return {"success": True}
        else:
            print(f"⚠️ 카카오 전송 실패: {result}")
            return {"success": False, "error": str(result)}

    except Exception as e:
        error_msg = str(e)
        print(f"❌ 카카오 전송 에러: {error_msg}")
        # 401 = 토큰 만료
        if "401" in error_msg:
            _refresh_token()
        return {"success": False, "error": error_msg}


def get_kakao_status() -> dict:
    """카카오 연동 상태"""
    return {
        "available": is_kakao_available(),
        "api_key_set": bool(KAKAO_REST_API_KEY),
        "token_exists": bool(_tokens.get("access_token")),
        "token_expires": datetime.fromtimestamp(_tokens.get("expires_at", 0)).isoformat() if _tokens.get("expires_at") else None,
        "refresh_expires": datetime.fromtimestamp(_tokens.get("refresh_expires_at", 0)).isoformat() if _tokens.get("refresh_expires_at") else None,
    }
