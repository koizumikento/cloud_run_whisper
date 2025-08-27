FROM python:3.12-slim-bookworm

# uv (高速 pip 互換) を使用
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# 依存定義（pyproject.toml のみ。uv.lock は任意）
COPY pyproject.toml ./
RUN uv venv --python=python3.12 \
  && uv sync --no-dev

# CUDA 追加ライブラリ（cuBLAS / cuDNN）を導入（スクリプト化）
COPY scripts/setup_cuda.sh /app/scripts/setup_cuda.sh
RUN bash /app/scripts/setup_cuda.sh

# アプリ配置
COPY app /app
COPY scripts /app/scripts

# モデル事前ダウンロード（ビルド時）
ENV WHISPER_MODEL=large-v3
ENV XDG_CACHE_HOME=/root/.cache
RUN uv run python /app/scripts/download_model.py --device cpu

EXPOSE 8080
CMD ["uv", "run", "hypercorn", "main:app", "--bind", "0.0.0.0:8080", "--access-logfile", "-", "--error-logfile","-"]

