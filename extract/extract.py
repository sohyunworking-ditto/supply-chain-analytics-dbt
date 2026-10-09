"""WWI(SQL Server) → data/raw/*.parquet 1회 추출.

    python extract/extract.py              # 전체
    python extract/extract.py --only Sales.Orders Warehouse.StockItems

- 대상 테이블과 그 시스템 버전 이력 테이블(*_Archive)을 함께 추출합니다.
- geography 컬럼은 WKT 문자열로 바꾸고, varbinary 컬럼(사진·해시 암호)은 제외합니다.
- 테이블별 원천 행 수와 기록 행 수를 data/raw/_manifest.json에 남깁니다.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pymssql

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "raw"
DATABASE = "WideWorldImporters"

TABLES = [
    # Application
    "Application.Cities",
    "Application.StateProvinces",
    "Application.Countries",
    "Application.DeliveryMethods",
    "Application.PaymentMethods",
    "Application.TransactionTypes",
    "Application.People",
    # Purchasing
    "Purchasing.Suppliers",
    "Purchasing.SupplierCategories",
    "Purchasing.PurchaseOrders",
    "Purchasing.PurchaseOrderLines",
    "Purchasing.SupplierTransactions",
    # Sales
    "Sales.Customers",
    "Sales.CustomerCategories",
    "Sales.BuyingGroups",
    "Sales.Orders",
    "Sales.OrderLines",
    "Sales.Invoices",
    "Sales.InvoiceLines",
    "Sales.CustomerTransactions",
    # Warehouse
    "Warehouse.StockItems",
    "Warehouse.StockItemHoldings",
    "Warehouse.StockItemTransactions",
    "Warehouse.StockGroups",
    "Warehouse.StockItemStockGroups",
    "Warehouse.Colors",
    "Warehouse.PackageTypes",
]

EXCLUDED_TYPES = {"varbinary", "binary", "image"}


def load_env(path: Path) -> None:
    """extract/.env의 KEY=VALUE를 환경변수로 (이미 있으면 유지)."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def to_snake(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", name).lower()


def file_stem(qualified: str) -> str:
    """Purchasing.PurchaseOrderLines → purchasing__purchase_order_lines"""
    schema, table = qualified.split(".")
    return f"{to_snake(schema)}__{to_snake(table)}"


def history_table(cur, qualified: str) -> str | None:
    cur.execute(
        """
        SELECT SCHEMA_NAME(h.schema_id) + '.' + h.name
        FROM sys.tables AS t
        JOIN sys.tables AS h ON h.object_id = t.history_table_id
        WHERE t.object_id = OBJECT_ID(%s) AND t.temporal_type = 2
        """,
        (qualified,),
    )
    row = cur.fetchone()
    return row[0] if row else None


def select_list(cur, qualified: str) -> tuple[str, list[str]]:
    cur.execute(
        """
        SELECT c.name, ty.name
        FROM sys.columns AS c
        JOIN sys.types AS ty ON ty.user_type_id = c.user_type_id
        WHERE c.object_id = OBJECT_ID(%s)
        ORDER BY c.column_id
        """,
        (qualified,),
    )
    exprs, skipped = [], []
    for col, typ in cur.fetchall():
        if typ in EXCLUDED_TYPES:
            skipped.append(col)
        elif typ == "geography":
            exprs.append(f"[{col}].STAsText() AS [{col}]")
        else:
            exprs.append(f"[{col}]")
    return ", ".join(exprs), skipped


def extract_table(cur, qualified: str) -> dict:
    cols, skipped = select_list(cur, qualified)
    cur.execute(f"SELECT COUNT_BIG(*) FROM {qualified}")
    source_rows = cur.fetchone()[0]

    cur.execute(f"SELECT {cols} FROM {qualified}")
    names = [d[0] for d in cur.description]
    df = pd.DataFrame(cur.fetchall(), columns=names)

    path = OUT_DIR / f"{file_stem(qualified)}.parquet"
    df.to_parquet(path, index=False)

    status = "ok" if len(df) == source_rows else "MISMATCH"
    print(f"  {qualified:<45} {len(df):>9,} rows  {status}")
    return {
        "source": qualified,
        "file": path.name,
        "source_rows": source_rows,
        "written_rows": len(df),
        "columns": names,
        "skipped_columns": skipped,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="+", metavar="SCHEMA.TABLE", help="일부 테이블만 추출")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=1433)
    args = parser.parse_args()

    load_env(ROOT / "extract" / ".env")
    password = os.environ.get("MSSQL_SA_PASSWORD")
    if not password:
        print("MSSQL_SA_PASSWORD가 없습니다. extract/.env를 만드세요.", file=sys.stderr)
        return 1

    targets = args.only or TABLES
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = pymssql.connect(
        server=args.host, port=args.port, user="sa", password=password, database=DATABASE
    )
    cur = conn.cursor()
    entries = []
    try:
        for qualified in targets:
            entries.append(extract_table(cur, qualified))
            hist = history_table(cur, qualified)
            if hist:
                entries.append(extract_table(cur, hist))
    finally:
        conn.close()

    manifest = {
        "database": DATABASE,
        "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tables": entries,
    }
    manifest_path = OUT_DIR / "_manifest.json"
    if args.only and manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        kept = [t for t in previous["tables"] if t["source"] not in {e["source"] for e in entries}]
        manifest["tables"] = kept + entries
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=str))

    mismatches = [e["source"] for e in entries if e["source_rows"] != e["written_rows"]]
    print(f"\n{len(entries)}개 테이블 → {OUT_DIR.relative_to(ROOT)}  (행 수 불일치 {len(mismatches)}개)")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
