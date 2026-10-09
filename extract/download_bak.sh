#!/usr/bin/env bash
# Microsoft sql-server-samples 릴리스에서 WWI 백업을 내려받습니다.
#   ./extract/download_bak.sh            # Full (기본)
#   ./extract/download_bak.sh Standard   # Full 복원이 실패할 때
set -euo pipefail

EDITION="${1:-Full}"
BASE="https://github.com/Microsoft/sql-server-samples/releases/download/wide-world-importers-v1.0"
DEST="$(cd "$(dirname "$0")" && pwd)/backup"

mkdir -p "$DEST"
curl -fL --progress-bar -o "$DEST/WideWorldImporters-$EDITION.bak" "$BASE/WideWorldImporters-$EDITION.bak"
ls -lh "$DEST"
