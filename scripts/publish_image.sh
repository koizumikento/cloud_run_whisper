#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Build and publish Docker image to Artifact Registry, then output IMAGE_URI(.txt) and IMAGE_URI_DIGEST(.txt).

Env/flags:
  PROJECT_ID        (or --project/-p)   GCP project id (default: gcloud config)
  REGION            (or --region/-r)    Registry region (default: asia-northeast1)
  REPO              (or --repo)         Artifact Registry repo name (default: whisper-repo)
  IMAGE             (or --image)        Image name (default: cloud-run-whisper)
  TAG               (or --tag)          Image tag (default: git describe or timestamp)
  TAG_LATEST=1                         Also tag :latest (default: 0)

Usage:
  ./scripts/publish_image.sh [--project <id>] [--region <r>] [--repo <name>] [--image <name>] [--tag <tag>]
EOF
}

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || true)}"
REGION="${REGION:-asia-northeast1}"
REPO="${REPO:-whisper-repo}"
IMAGE="${IMAGE:-cloud-run-whisper}"
TAG="${TAG:-$(git describe --tags --always 2>/dev/null || date +%Y%m%d%H%M%S)}"
TAG_LATEST="${TAG_LATEST:-0}"

# parse flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project) PROJECT_ID="$2"; shift 2 ;;
    -r|--region)  REGION="$2"; shift 2 ;;
    --repo)       REPO="$2"; shift 2 ;;
    --image)      IMAGE="$2"; shift 2 ;;
    --tag)        TAG="$2"; shift 2 ;;
    -h|--help)    usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

if [[ -z "${PROJECT_ID:-}" ]]; then
  echo "PROJECT_ID is required (set gcloud config or pass --project)"; exit 1
fi

echo "Project: $PROJECT_ID"
echo "Region : $REGION"
echo "Repo   : $REPO"
echo "Image  : $IMAGE"
echo "Tag    : $TAG"

# Ensure required APIs (no-op if already enabled)
gcloud services enable artifactregistry.googleapis.com cloudbuild.googleapis.com >/dev/null

# Ensure repository
if ! gcloud artifacts repositories describe "$REPO" --location="$REGION" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$REPO" --repository-format=docker --location="$REGION"
fi

IMAGE_URI="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE:$TAG"

# Build & push via Cloud Build
gcloud builds submit --tag "$IMAGE_URI" .

# Optional latest tag
if [[ "$TAG_LATEST" == "1" ]]; then
  gcloud artifacts docker tags add "$IMAGE_URI" "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE:latest"
fi

# Resolve digest and export files
DIGEST="$(gcloud artifacts docker images describe "$IMAGE_URI" --format='value(image_summary.digest)')"
IMAGE_URI_DIGEST="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE@$DIGEST"

printf "%s" "$IMAGE_URI" > IMAGE_URI.txt
printf "%s" "$IMAGE_URI_DIGEST" > IMAGE_URI_DIGEST.txt

echo "Pushed: $IMAGE_URI"
echo "Digest: $IMAGE_URI_DIGEST"
echo "Wrote:  IMAGE_URI.txt / IMAGE_URI_DIGEST.txt"


