"""
DeepRed v3.0 — pytest 설정 (conftest.py)
FastAPI TestClient + InMemory DB 폴백으로 외부 의존성 없이 테스트
"""

import sys
import os

# server/ 디렉토리를 path에 추가 (import 해결)
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient — 세션 전체에서 공유"""
    # 환경변수로 테스트 모드 설정 (Supabase 미사용)
    os.environ.pop("SUPABASE_URL", None)
    os.environ.pop("SUPABASE_KEY", None)
    os.environ.pop("GOOGLE_API_KEY", None)

    from main import app
    with TestClient(app) as c:
        yield c
