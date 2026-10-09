with source as (

    select * from {{ source('wwi', 'warehouse__stock_item_transactions') }}

),

renamed as (

    select
        StockItemTransactionID                   as stock_item_transaction_id,
        StockItemID                              as stock_item_id,
        TransactionTypeID                        as transaction_type_id,
        cast(CustomerID as bigint)               as customer_id,
        cast(InvoiceID as bigint)                as invoice_id,
        cast(SupplierID as bigint)               as supplier_id,
        cast(PurchaseOrderID as bigint)          as purchase_order_id,
        TransactionOccurredWhen                  as transaction_occurred_at,
        Quantity                                 as quantity,
        LastEditedWhen                           as last_edited_at,
        _loaded_at                               as _loaded_at
    from source

)

select * from renamed
