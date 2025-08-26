## Cloud Run Whisper (GPU) 概要

`faster-whisper` を `FastAPI` で提供し、Cloud Run GPU（例: NVIDIA L4）で動かすためのプロジェクトです。

---

## Artifact Registry へのイメージ発行（publish_image.sh）

### 前提

- `gcloud` がインストール・認証済み（`gcloud auth login` / `gcloud config set project <PROJECT_ID>`）。
- API: `artifactregistry.googleapis.com` と `cloudbuild.googleapis.com` が有効（スクリプト内で有効化を試行します）。

### 使い方（Bash）

```bash
chmod +x scripts/publish_image.sh

# フラグ指定例
./scripts/publish_image.sh \
  --project <PROJECT_ID> \
  --region asia-northeast1 \
  --repo whisper-repo \
  --image cloud-run-whisper \
  --tag 1.0.0

# 環境変数指定例（latest も付与）
PROJECT_ID=<PROJECT_ID> TAG=1.0.0 TAG_LATEST=1 ./scripts/publish_image.sh
```

### 出力

- `IMAGE_URI.txt`: タグ付き URI（例: `asia-northeast1-docker.pkg.dev/PROJECT/whisper-repo/cloud-run-whisper:1.0.0`）
- `IMAGE_URI_DIGEST.txt`: ダイジェスト URI（例: `asia-northeast1-docker.pkg.dev/PROJECT/whisper-repo/cloud-run-whisper@sha256:...`）

ダイジェスト（後者）の利用を推奨します。再現性が高く、Terraform との相性が良いです。

---

## Terraform から参照（推奨: ダイジェスト）

```bash
IMG_DIGEST="$(cat IMAGE_URI_DIGEST.txt)"
terraform apply -var "region=asia-northeast1" -var "image_uri=$IMG_DIGEST"
```

例（`google_cloud_run_v2_service` の一部）:

```hcl
containers {
  image = var.image_uri  # ここにダイジェスト URI を渡す
  ports { container_port = 8080 }
  env { name = "XDG_CACHE_HOME" value = "/root/.cache" }
  env { name = "WHISPER_MODEL" value = "large-v3" }
  env { name = "WHISPER_DEVICE" value = "cuda" }
  env { name = "WHISPER_COMPUTE_TYPE" value = "float16" }
}
```

---

## Cloud Run へ直接デプロイ（参考）

```bash
gcloud run deploy cloud-run-whisper \
  --image "$(cat IMAGE_URI.txt)" \
  --region=asia-northeast1 \
  --platform=managed \
  --accelerator=type=nvidia-l4,count=1 \
  --memory=16Gi --cpu=4 \
  --concurrency=1 \
  --timeout=3600 \
  --min-instances=1 --max-instances=2 \
  --port=8080 \
  --set-env-vars=XDG_CACHE_HOME=/root/.cache,WHISPER_MODEL=large-v3,WHISPER_DEVICE=cuda,WHISPER_COMPUTE_TYPE=float16 \
  --allow-unauthenticated
```

---

## API の使い方（ローカル/本番共通）

```bash
curl -X POST \
  --form "upload_file=@data/sample_audio.mp3" \
  http://localhost:8080/transcribe | jq .
```

本番（Cloud Run の URL）:

```bash
curl -X POST \
  --form "upload_file=@sample.mp3" \
  https://<YOUR_CLOUD_RUN_URL>/transcribe | jq .
```

---

## ローカル開発

- Uvicorn:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
```

- Docker Compose（GPU 環境）:

```bash
docker compose --profile gpu up --build
```

---

## 注意事項

- Cloud Run GPU ランタイムの更新に合わせ、`Dockerfile` の CUDA/cuDNN の版は調整してください。
- GPU 前提で `WHISPER_DEVICE=cuda`、`WHISPER_COMPUTE_TYPE=float16` を推奨します。
- 同時実行は `--concurrency=1` を推奨（GPU の計算資源競合を避けるため）。

---

## Cloud Build（cloudbuild.yaml）で自動ビルド/発行

このリポジトリには Artifact Registry へ push するための `cloudbuild.yaml` が同梱されています。

### 手動実行（Cloud Shell 等）

```bash
gcloud builds submit \
  --config cloudbuild.yaml \
  --substitutions _REGION=asia-northeast1,_REPO=whisper-repo,_IMAGE=cloud-run-whisper,_TAG=v1.0.0,_TAG_LATEST=true,_ARTIFACTS_BUCKET=
```

- `_REGION`/`_REPO`/`_IMAGE`/`_TAG` を適宜変更してください。
- `_TAG_LATEST=true` で `:latest` も付与。
- `_ARTIFACTS_BUCKET` を指定すると、`IMAGE_URI.txt` と `IMAGE_URI_DIGEST.txt` が `gs://<BUCKET>/cloud-run-whisper/<TAG>/` にアップロードされます（空ならスキップ）。

実行後、ログに push 先と digest が表示されます。Terraform ではダイジェスト（`IMAGE_URI_DIGEST.txt`）の利用を推奨します。

### 推奨トリガー運用（例）

- Git タグ `v*` でトリガー → `_TAG=$TAG_NAME` にしてビルド → Artifact Registry に発行
- 成果物の URI は GCS に保存し、Terraform パイプラインへ受け渡し
