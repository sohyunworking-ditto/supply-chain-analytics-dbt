"""DuckDB marts → BigQuery 샌드박스 게시.

    python publish/publish.py                                   # warehouse/wwi.duckdb의 marts 스키마 전체
    python publish/publish.py --files data/raw/sales__buying_groups.parquet   # 파일 직접 (연결 확인용)

- 샌드박스는 DML이 막혀 있으므로 적재 작업(load job)만 씁니다.
- 테이블마다 삭제 → 재생성합니다. 60일 만료일을 새로 잡기 위해서입니다.
- 적재 후 BigQuery 행 수를 원본 행 수와 대조하고, 하나라도 다르면 종료 코드 1을 냅니다.

환경변수: GCP_PROJECT (기본 dev-sohyun), BQ_DATASET (기본 wwi_marts),
          GOOGLE_APPLICATION_CREDENTIALS (기본 ~/.gcp/dbt-publisher.json)
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

import pyarrow.parquet as pq
from google.cloud import bigquery

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KEY = Path.home() / ".gcp" / "dbt-publisher.json"


def export_marts(db_path: Path, schema: str, out_dir: Path) -> list[Path]:
    import duckdb

    con = duckdb.connect(str(db_path), read_only=True)
    tables = [
        r[0]
        for r in con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = ? AND table_type = 'BASE TABLE' ORDER BY 1",
            [schema],
        ).fetchall()
    ]
    paths = []
    for t in tables:
        path = out_dir / f"{t}.parquet"
        con.execute(f'COPY "{schema}"."{t}" TO \'{path}\' (FORMAT parquet)')
        paths.append(path)
    con.close()
    return paths


def publish_file(client: bigquery.Client, dataset: str, path: Path) -> bool:
    table_id = f"{client.project}.{dataset}.{path.stem}"
    local_rows = pq.read_metadata(path).num_rows

    client.delete_table(table_id, not_found_ok=True)
    config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_EMPTY,
    )
    with path.open("rb") as f:
        client.load_table_from_file(f, table_id, job_config=config).result()

    table = client.get_table(table_id)
    ok = table.num_rows == local_rows
    expires = table.expires.date().isoformat() if table.expires else "없음"
    print(f"  {path.stem:<40} {table.num_rows:>9,} / {local_rows:>9,} rows  만료 {expires}  {'ok' if ok else 'MISMATCH'}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", nargs="+", type=Path, help="DuckDB 대신 Parquet 파일을 직접 게시")
    parser.add_argument("--duckdb", type=Path, default=ROOT / "warehouse" / "wwi.duckdb")
    parser.add_argument("--schema", default="marts")
    args = parser.parse_args()

    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(DEFAULT_KEY))
    project = os.environ.get("GCP_PROJECT", "dev-sohyun")
    dataset = os.environ.get("BQ_DATASET", "wwi_marts")
    client = bigquery.Client(project=project)

    with tempfile.TemporaryDirectory() as tmp:
        files = args.files or export_marts(args.duckdb, args.schema, Path(tmp))
        if not files:
            print(f"게시할 테이블이 없습니다: {args.duckdb} / {args.schema}", file=sys.stderr)
            return 1
        print(f"{project}.{dataset} ← {len(files)}개 테이블")
        results = [publish_file(client, dataset, p) for p in files]

    failed = results.count(False)
    print(f"\n완료: {len(results) - failed}개 성공, {failed}개 불일치")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
