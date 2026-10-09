/*
  Day 0 ⑤ 확인 쿼리. 결과는 계획서 진행 현황 비고에 옮겨 적습니다.

  docker exec wwi-mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
    -d WideWorldImporters -i /scripts/checks.sql -W -s '|'
*/
SET NOCOUNT ON;

-- 1. 데이터 기간
SELECT 'orders'          AS src, MIN(OrderDate) AS min_date, MAX(OrderDate) AS max_date FROM Sales.Orders
UNION ALL
SELECT 'purchase_orders', MIN(OrderDate), MAX(OrderDate) FROM Purchasing.PurchaseOrders
UNION ALL
SELECT 'stock_txn', MIN(CAST(TransactionOccurredWhen AS date)), MAX(CAST(TransactionOccurredWhen AS date))
FROM Warehouse.StockItemTransactions;

-- 2. snapshot 시연 가능 여부: 이력 테이블 버전 수와 기간
SELECT 'stock_items' AS src, COUNT(*) AS versions, COUNT(DISTINCT StockItemID) AS ids,
       MIN(ValidFrom) AS first_change, MAX(ValidTo) AS last_change
FROM Warehouse.StockItems_Archive
UNION ALL
SELECT 'suppliers', COUNT(*), COUNT(DISTINCT SupplierID), MIN(ValidFrom), MAX(ValidTo)
FROM Purchasing.Suppliers_Archive
UNION ALL
SELECT 'customers', COUNT(*), COUNT(DISTINCT CustomerID), MIN(ValidFrom), MAX(ValidTo)
FROM Sales.Customers_Archive;

-- 3. 단가 변경 이력: 버전 간 UnitPrice가 실제로 바뀐 품목 수
WITH versions AS (
    SELECT StockItemID, ValidFrom, UnitPrice FROM Warehouse.StockItems_Archive
    UNION ALL
    SELECT StockItemID, ValidFrom, UnitPrice FROM Warehouse.StockItems
), diffs AS (
    SELECT StockItemID,
           UnitPrice,
           LAG(UnitPrice) OVER (PARTITION BY StockItemID ORDER BY ValidFrom) AS prev_price
    FROM versions
)
SELECT COUNT(*)                    AS price_changes,
       COUNT(DISTINCT StockItemID) AS items_with_price_change
FROM diffs
WHERE prev_price IS NOT NULL AND prev_price <> UnitPrice;

-- 4. 발주 라인 ↔ 입고 트랜잭션 연결 키
SELECT COUNT(*)                                             AS receipt_txns,
       SUM(CASE WHEN pol.PurchaseOrderLineID IS NULL THEN 1 ELSE 0 END) AS unmatched_to_po_line
FROM Warehouse.StockItemTransactions AS sit
LEFT JOIN Purchasing.PurchaseOrderLines AS pol
       ON pol.PurchaseOrderID = sit.PurchaseOrderID
      AND pol.StockItemID     = sit.StockItemID
WHERE sit.PurchaseOrderID IS NOT NULL;

-- 5. 발주 라인 하나에 입고가 여러 번(부분 입고) 있는지
SELECT TOP 1 WITH TIES receipts_per_line, COUNT(*) AS lines
FROM (
    SELECT PurchaseOrderID, StockItemID, COUNT(*) AS receipts_per_line
    FROM Warehouse.StockItemTransactions
    WHERE PurchaseOrderID IS NOT NULL
    GROUP BY PurchaseOrderID, StockItemID
) AS t
GROUP BY receipts_per_line
ORDER BY COUNT(*) DESC;
