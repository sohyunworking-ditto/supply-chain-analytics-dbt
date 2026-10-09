"""data/raw/*.parquet → DuckDB raw 스키마 리플레이 적재.

    python loader/replay.py --until 2016-05-31 --reset    # 처음부터 전체 기간
    python loader/replay.py --until 2013-01-31 --reset    # 첫 달만
    python loader/replay.py --until 2013-02-28            # 다음 달 추가

WWI는 전체 기간이 한 번에 들어 있는 고정 데이터라, 시간순으로 다시 흘려보내야
dbt incremental과 snapshot이 실제로 동작합니다. 테이블 종류별 규칙:

- 트랜잭션: 업무 일자가 (직전 --until, 이번 --until] 인 행만 추가합니다. 라인은 상위 문서 일자를 따릅니다.
- 마스터: 현재 + 이력(_archive)을 합쳐 --until 시점에 유효했던 버전으로 통째로 교체합니다.
- 정적: 이력이 없는 테이블은 매번 전체를 교체하되, 그 시점의 품목 마스터에 있는 행만 남깁니다.
- 이력: snapshot 검증용. --until까지 확정된(ValidTo가 지난) 이력만 남깁니다.

모든 raw 테이블에 _loaded_at(적재 시각)과 _batch_until(이번 --until)을 붙입니다.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw"
DEFAULT_DB = ROOT / "warehouse" / "wwi.duckdb"

# 테이블: 업무 일자 식. 라인 테이블은 (상위 테이블, 조인 키, 상위 일자 컬럼)
TRANSACTIONS: dict[str, str | tuple[str, str, str]] = {
    "sales__orders": "OrderDate",
    "sales__order_lines": ("sales__orders", "OrderID", "OrderDate"),
    "sales__invoices": "InvoiceDate",
    "sales__invoice_lines": ("sales__invoices", "InvoiceID", "InvoiceDate"),
    "sales__customer_transactions": "TransactionDate",
    "warehouse__stock_item_transactions": "CAST(TransactionOccurredWhen AS DATE)",
}

MASTERS = [
    "application__cities",
    "application__state_provinces",
    "application__people",
    "sales__customers",
    "sales__customer_categories",
    "sales__buying_groups",
    "warehouse__stock_items",
]

# 이력이 없어 시점 복원이 안 되는 테이블. 그 시점에 존재하는 품목 행만 남깁니다.
STATIC = ["warehouse__stock_item_holdings"]

HISTORY = ["sales__customers_archive"]


def parquet(name: str) -> str:
    return f"read_parquet('{DATA / f'{name}.parquet'}')"


def batch_cols(until: date) -> str:
    return f"current_timestamp AS _loaded_at, DATE '{until}' AS _batch_until"


def replace_table(con, name: str, select_sql: str) -> int:
    con.execute(f"CREATE OR REPLACE TABLE raw.{name} AS {select_sql}")
    return con.execute(f"SELECT count(*) FROM raw.{name}").fetchone()[0]


def load_transaction(con, name: str, rule, since: date | None, until: date) -> int:
    if isinstance(rule, tuple):
        parent, key, parent_date = rule
        source = f"{parquet(name)} AS t JOIN {parquet(parent)} AS p USING ({key})"
        event_date = f"p.{parent_date}"
    else:
        source = f"{parquet(name)} AS t"
        event_date = rule

    where = f"{event_date} <= DATE '{until}'"
    if since:
        where += f" AND {event_date} > DATE '{since}'"
    select_sql = f"SELECT t.*, {batch_cols(until)} FROM {source} WHERE {where}"

    exists = con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'raw' AND table_name = ?",
        [name],
    ).fetchone()[0]
    if not exists:
        con.execute(f"CREATE TABLE raw.{name} AS {select_sql}")
    else:
        con.execute(f"INSERT INTO raw.{name} BY NAME {select_sql}")
    return con.execute(f"SELECT count(*) FROM raw.{name} WHERE _batch_until = DATE '{until}'").fetchone()[0]


def load_master(con, name: str, until: date) -> int:
    # until 당일 자정 직후(= 다음 날 0시)에 유효한 버전
    as_of = f"(DATE '{until}' + INTERVAL 1 DAY)"
    select_sql = f"""
        SELECT *, {batch_cols(until)}
        FROM (
            SELECT * FROM {parquet(name)}
            UNION ALL BY NAME
            SELECT * FROM {parquet(name + '_archive')}
        )
        WHERE ValidFrom < {as_of} AND ValidTo >= {as_of}
    """
    return replace_table(con, name, select_sql)


def load_history(con, name: str, until: date) -> int:
    as_of = f"(DATE '{until}' + INTERVAL 1 DAY)"
    return replace_table(con, name, f"SELECT *, {batch_cols(until)} FROM {parquet(name)} WHERE ValidTo < {as_of}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--until", required=True, type=date.fromisoformat, help="이번 배치의 마지막 업무 일자 (YYYY-MM-DD)")
    parser.add_argument("--reset", action="store_true", help="raw 스키마를 지우고 처음부터 적재")
    parser.add_argument("--db", type=Path, default=Path(os.environ.get("DBT_DUCKDB_PATH", DEFAULT_DB)))
    args = parser.parse_args()

    args.db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(args.db))
    if args.reset:
        con.execute("DROP SCHEMA IF EXISTS raw CASCADE")
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute("CREATE TABLE IF NOT EXISTS raw._replay_state (batch_until DATE, loaded_at TIMESTAMP)")

    since = con.execute("SELECT max(batch_until) FROM raw._replay_state").fetchone()[0]
    if since and args.until <= since:
        print(f"--until {args.until}은 직전 적재({since}) 이후여야 합니다. 처음부터 하려면 --reset", file=sys.stderr)
        return 1

    print(f"{args.db.relative_to(ROOT) if args.db.is_relative_to(ROOT) else args.db}: ({since or '시작'}, {args.until}]")
    con.execute("BEGIN")
    for name, rule in TRANSACTIONS.items():
        print(f"  + {name:<40} {load_transaction(con, name, rule, since, args.until):>9,} rows")
    for name in MASTERS:
        print(f"  = {name:<40} {load_master(con, name, args.until):>9,} rows (as of)")
    for name in STATIC:
        select_sql = (
            f"SELECT *, {batch_cols(args.until)} FROM {parquet(name)} "
            "WHERE StockItemID IN (SELECT StockItemID FROM raw.warehouse__stock_items)"
        )
        print(f"  = {name:<40} {replace_table(con, name, select_sql):>9,} rows")
    for name in HISTORY:
        print(f"  = {name:<40} {load_history(con, name, args.until):>9,} rows (closed)")
    con.execute("INSERT INTO raw._replay_state VALUES (?, current_timestamp)", [args.until])
    con.execute("COMMIT")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
