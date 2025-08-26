import os
import sys
from pathlib import Path

# プロジェクトルートを import パスに追加
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# テスト中は重いモデルロードをスキップ
os.environ.setdefault("WHISPER_SKIP_LOAD", "1")
