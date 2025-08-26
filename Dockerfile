FROM python:3.12-slim-bookworm

# uv (高速 pip 互換) を使用
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# 依存定義（pyproject.toml のみ。uv.lock は任意）
COPY pyproject.toml ./
RUN uv venv --python=python3.12 \
  && uv sync --no-dev

# CUDA 追加ライブラリ（cuBLAS / cuDNN）を導入
RUN apt-get update \
  && apt-get install -y --no-install-recommends wget ca-certificates \
  \
  # cuBLAS (CUDA 12.9 例。Cloud Run 環境に合わせて URL/Version を更新)
  && wget -q https://developer.download.nvidia.com/compute/cuda/12.9.0/local_installers/cuda-repo-debian12-12-9-local_12.9.0-575.51.03-1_amd64.deb \
  && dpkg -i cuda-repo-debian12-12-9-local_12.9.0-575.51.03-1_amd64.deb \
  && cp /var/cuda-repo-debian12-12-9-local/cuda-*-keyring.gpg /usr/share/keyrings/ \
  && apt-get update \
  && apt-get install -y --no-install-recommends libcublas-12-9 \
  \
  # cuDNN (9.10.1 例。Cloud Run 環境に合わせて URL/Version を更新)
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

# アプリ配置
COPY app /app
COPY scripts /app/scripts

# モデル事前ダウンロード（ビルド時）
ENV WHISPER_MODEL=large-v3-turbo
ENV XDG_CACHE_HOME=/root/.cache
RUN uv run python /app/scripts/download_model.py --device cpu

EXPOSE 8080
CMD ["uv", "run", "hypercorn", "main:app", "--bind", "0.0.0.0:8080", "--access-logfile", "-", "--error-logfile", "-", "--alpn", "h2"]


