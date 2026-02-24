#!/bin/bash
# ============================================
# DeepRed v3.0 — Oracle Cloud VM 배포 스크립트
# ============================================
# 사용법: ssh ubuntu@<VM_IP> 'bash -s' < deploy.sh

set -e

echo "🔴 DeepRed v3.0 — Oracle Cloud 배포 시작"
echo "========================================="

# ─── 1. 시스템 업데이트 ───
echo "📦 시스템 업데이트..."
sudo apt-get update -y
sudo apt-get upgrade -y

# ─── 2. Docker 설치 ───
if ! command -v docker &> /dev/null; then
    echo "🐳 Docker 설치..."
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker $USER
    echo "✅ Docker 설치 완료"
else
    echo "✅ Docker 이미 설치됨"
fi

# Docker Compose 플러그인 확인
if ! docker compose version &> /dev/null; then
    echo "🐳 Docker Compose 플러그인 설치..."
    sudo apt-get install -y docker-compose-plugin
fi

# ─── 3. 방화벽 설정 ───
echo "🔒 방화벽 규칙 설정..."
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
sudo netfilter-persistent save 2>/dev/null || true

# ─── 4. 프로젝트 디렉토리 ───
echo "📁 프로젝트 디렉토리 설정..."
DEPLOY_DIR="$HOME/deepred"
mkdir -p $DEPLOY_DIR
cd $DEPLOY_DIR

# ─── 5. 환경변수 확인 ───
if [ ! -f ".env.production" ]; then
    echo ""
    echo "⚠️  .env.production 파일이 없습니다!"
    echo "    아래 파일을 먼저 서버에 업로드해주세요:"
    echo "    scp .env.production ubuntu@<VM_IP>:~/deepred/"
    echo ""
    exit 1
fi

# ─── 6. Docker 빌드 & 실행 ───
echo "🏗️  Docker 빌드 중..."
docker compose build --no-cache

echo "🚀 컨테이너 시작..."
docker compose up -d

# ─── 7. 헬스체크 ───
echo ""
echo "⏳ 서버 시작 대기 (10초)..."
sleep 10

if curl -sf http://localhost:8000/api/health > /dev/null; then
    echo "✅ DeepRed API 정상 동작!"
    curl -s http://localhost:8000/api/health | python3 -m json.tool
else
    echo "❌ API 응답 없음. 로그 확인:"
    docker compose logs api --tail 20
fi

echo ""
echo "========================================="
echo "🔴 DeepRed v3.0 배포 완료!"
echo ""
echo "📋 유용한 명령어:"
echo "  docker compose logs -f api    # API 로그"
echo "  docker compose restart api    # API 재시작"
echo "  docker compose down           # 전체 중지"
echo "  docker compose up -d          # 전체 시작"
echo "========================================="
