#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Build and publish Docker image to Docker Hub from local machine.

Requirements:
  - docker CLI logged in (or provide DOCKERHUB_USERNAME/DOCKERHUB_PASSWORD)
  - git (for default TAG) or pass --tag

Env/flags:
  DOCKERHUB_USERNAME            (or --username/-u)
  DOCKERHUB_PASSWORD            (optional if docker login already done)
  REPO         (or --repo/-r)   Docker Hub repo (e.g., yourname/cloud-run-whisper)
  TAG          (or --tag/-t)    Tag (default: git describe or timestamp)
  LATEST=1                      Also tag :latest (default: 0)

Usage:
  ./scripts/publish_dockerhub.sh --repo yourname/cloud-run-whisper --tag 1.0.0
EOF
}

REPO="${REPO:-}"
TAG="${TAG:-$(git describe --tags --always 2>/dev/null || date +%Y%m%d%H%M%S)}"
LATEST="${LATEST:-0}"
DOCKERHUB_USERNAME="${DOCKERHUB_USERNAME:-}"
DOCKERHUB_PASSWORD="${DOCKERHUB_PASSWORD:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -r|--repo) REPO="$2"; shift 2 ;;
    -t|--tag) TAG="$2"; shift 2 ;;
    -u|--username) DOCKERHUB_USERNAME="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

if [[ -z "${REPO}" ]]; then
  echo "--repo (e.g., yourname/cloud-run-whisper) is required"; exit 1
fi

echo "Repo : docker.io/$REPO"
echo "Tag  : $TAG"

# Optional login (skip if already logged in)
if [[ -n "${DOCKERHUB_USERNAME}" && -n "${DOCKERHUB_PASSWORD}" ]]; then
  echo "$DOCKERHUB_PASSWORD" | docker login --username "$DOCKERHUB_USERNAME" --password-stdin
fi

IMAGE_LOCAL="${REPO//\//_}:build-${TAG}"
IMAGE_REMOTE="docker.io/${REPO}:${TAG}"

# Build locally
docker build -t "$IMAGE_LOCAL" -f Dockerfile .

# Tag & push
docker tag "$IMAGE_LOCAL" "$IMAGE_REMOTE"
docker push "$IMAGE_REMOTE"

if [[ "$LATEST" == "1" ]]; then
  docker tag "$IMAGE_LOCAL" "docker.io/${REPO}:latest"
  docker push "docker.io/${REPO}:latest"
fi

echo "Pushed: $IMAGE_REMOTE"
if [[ "$LATEST" == "1" ]]; then
  echo "Also pushed: docker.io/${REPO}:latest"
fi


