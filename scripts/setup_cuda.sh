#!/usr/bin/env bash
set -euo pipefail

# このスクリプトは Debian 12 (bookworm) ベースで CUDA ランタイムが事前搭載された
# Cloud Run GPU ランタイムを想定し、追加で cuBLAS / cuDNN を導入します。
# バージョンは Dockerfile のコメントに合わせています。必要に応じて更新してください。

export DEBIAN_FRONTEND=noninteractive

apt-get update \
  && apt-get install -y --no-install-recommends wget ca-certificates \
  \
  # cuBLAS (CUDA 12.9 の例)
  && wget -q https://developer.download.nvidia.com/compute/cuda/12.9.0/local_installers/cuda-repo-debian12-12-9-local_12.9.0-575.51.03-1_amd64.deb \
  && dpkg -i cuda-repo-debian12-12-9-local_12.9.0-575.51.03-1_amd64.deb \
  && cp /var/cuda-repo-debian12-12-9-local/cuda-*-keyring.gpg /usr/share/keyrings/ \
  && apt-get update \
  && apt-get install -y --no-install-recommends libcublas-12-9 \
  \
  # cuDNN (9.10.1 の例)
  && wget -q https://developer.download.nvidia.com/compute/cudnn/9.10.1/local_installers/cudnn-local-repo-debian12-9.10.1_1.0-1_amd64.deb \
  && dpkg -i cudnn-local-repo-debian12-9.10.1_1.0-1_amd64.deb \
  && cp /var/cudnn-local-repo-debian12-9.10.1/cudnn-*-keyring.gpg /usr/share/keyrings/ \
  && apt-get update \
  && apt-get install -y --no-install-recommends cudnn-cuda-12 \
  \
  # クリーンアップでサイズ削減
  && rm -f /usr/share/keyrings/*.gpg \
  && rm -f /var/cuda-repo-debian12-12-9-local/cuda-*-keyring.gpg \
  && rm -f /var/cudnn-local-repo-debian12-9.10.1/cudnn-*-keyring.gpg \
  && rm -f cuda-repo-debian12-12-9-local_12.9.0-575.51.03-1_amd64.deb \
  && rm -f cudnn-local-repo-debian12-9.10.1_1.0-1_amd64.deb \
  && apt-get purge -y --auto-remove \
       cuda-repo-debian12-12-9-local \
       cudnn-local-repo-debian12-9.10.1 \
       wget \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

echo "[setup_cuda] cuBLAS/cuDNN setup completed"


