#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${ENV_FILE:-${PROJECT_ROOT}/.env}"

# Load .env variables if present. Existing exported env vars still take priority.
if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

IMAGE_REPO="${IMAGE_REPO:-}"
IMAGE_TAG="${IMAGE_TAG:-}"
PUSH_LATEST="${PUSH_LATEST:-true}"
DOCKERFILE="${DOCKERFILE:-Dockerfile}"
CONTEXT="${CONTEXT:-.}"

if [[ -z "${IMAGE_REPO}" ]]; then
  echo "ERROR: IMAGE_REPO is required, e.g. registry.example.com/namespace/ai-rss-reader" >&2
  exit 1
fi

if [[ -z "${IMAGE_TAG}" ]]; then
  TS="$(date +%Y%m%d-%H%M%S)"
  if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    GIT_SHA="$(git rev-parse --short HEAD)"
  else
    GIT_SHA="nogit"
  fi
  IMAGE_TAG="${TS}-${GIT_SHA}"
fi

FULL_TAG="${IMAGE_REPO}:${IMAGE_TAG}"
LATEST_TAG="${IMAGE_REPO}:latest"

echo "[1/4] Building image: ${FULL_TAG}"
docker build -f "${DOCKERFILE}" -t "${FULL_TAG}" "${CONTEXT}"

echo "[2/4] Tagging image"
if [[ "${PUSH_LATEST}" == "true" ]]; then
  docker tag "${FULL_TAG}" "${LATEST_TAG}"
fi

echo "[3/4] Pushing image tag: ${FULL_TAG}"
docker push "${FULL_TAG}"

if [[ "${PUSH_LATEST}" == "true" ]]; then
  echo "[4/4] Pushing image tag: ${LATEST_TAG}"
  docker push "${LATEST_TAG}"
else
  echo "[4/4] Skipped pushing latest tag"
fi

echo
echo "IMAGE_REF=${FULL_TAG}"
if [[ "${PUSH_LATEST}" == "true" ]]; then
  echo "IMAGE_REF_LATEST=${LATEST_TAG}"
fi
