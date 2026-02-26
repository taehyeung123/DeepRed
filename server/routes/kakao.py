"""
DeepRed v3.1 — 카카오 나에게 보내기 라우트
OAuth 콜백 + 상태조회 + 테스트 전송
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from kakao import (
    get_auth_url, exchange_code, send_to_me,
    get_kakao_status, is_kakao_available,
)

router = APIRouter(prefix="/api/kakao", tags=["kakao"])


@router.get("/auth")
def kakao_auth():
    """카카오 로그인 URL 반환 — 대표님이 이 URL로 접속"""
    url = get_auth_url()
    return {"auth_url": url, "instruction": "이 URL을 브라우저에서 열고 카카오 로그인하세요."}


@router.get("/callback")
def kakao_callback(code: str = None, error: str = None):
    """카카오 OAuth 콜백 — 인증 코드 수신 후 토큰 교환"""
    if error:
        return HTMLResponse(f"""
        <html><body style="font-family:sans-serif;text-align:center;padding:50px">
        <h2>❌ 카카오 인증 실패</h2>
        <p>{error}</p>
        </body></html>
        """)

    if not code:
        return HTMLResponse("""
        <html><body style="font-family:sans-serif;text-align:center;padding:50px">
        <h2>❌ 인증 코드가 없습니다</h2>
        </body></html>
        """)

    result = exchange_code(code)
    
    if result.get("success"):
        return HTMLResponse(f"""
        <html><body style="font-family:sans-serif;text-align:center;padding:50px">
        <h1>✅ 카카오 연동 완료!</h1>
        <p>토큰이 발급되었습니다. 이제 수진이가 카카오톡으로 보고를 보낼 수 있습니다.</p>
        <p>유효 시간: {result.get('expires_in', 0) // 3600}시간 (자동 갱신됨)</p>
        <p style="color:gray;margin-top:30px">이 창을 닫으셔도 됩니다.</p>
        </body></html>
        """)
    else:
        return HTMLResponse(f"""
        <html><body style="font-family:sans-serif;text-align:center;padding:50px">
        <h2>❌ 토큰 발급 실패</h2>
        <p>{result.get('error', '알 수 없는 오류')}</p>
        </body></html>
        """)


@router.get("/status")
def kakao_status():
    """카카오 연동 상태"""
    return get_kakao_status()


class KakaoTestRequest(BaseModel):
    message: str = "🔔 DeepRed 카카오 알림 테스트입니다!"


@router.post("/test")
def kakao_test(req: KakaoTestRequest):
    """카카오 나에게 보내기 테스트"""
    if not is_kakao_available():
        return {"error": "카카오 미연동 — /api/kakao/auth 에서 인증하세요."}
    result = send_to_me(req.message)
    return result
