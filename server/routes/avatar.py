"""
DeepRed v3.0 — Avatar Routes
아바타 전체 조회/저장, CEO/직원 개별 업데이트
"""

import os
import json
from fastapi import APIRouter, Request

router = APIRouter(prefix="/api", tags=["avatar"])

_AVATAR_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "server", "avatars.json")
# Docker: /app/data/avatars.json (영구 볼륨), 로컬: server/avatars.json
_DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), ".."))
_AVATAR_FILE = os.path.join(_DATA_DIR, "avatars.json")
os.makedirs(os.path.dirname(_AVATAR_FILE), exist_ok=True)


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


@router.get("/avatars")
def get_avatars():
    """모든 아바타 설정 조회"""
    data = _load_avatar_data()
    return {
        "ceo": data.get("ceo", {}),
        "ceoName": data.get("ceoName", "대표"),
        "employees": data.get("employees", {}),
    }


@router.post("/avatars")
async def save_all_avatars(request: Request):
    """전체 아바타 설정 저장"""
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


@router.put("/avatars/ceo")
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


@router.put("/avatars/employee/{employee_id}")
async def update_employee_avatar(employee_id: str, request: Request):
    """개별 직원 아바타 업데이트"""
    body = await request.json()

    data = _load_avatar_data()
    if "employees" not in data:
        data["employees"] = {}
    data["employees"][employee_id] = body.get("avatar", body)
    _save_avatar_data(data)
    return {"status": "ok", "employee_id": employee_id}
