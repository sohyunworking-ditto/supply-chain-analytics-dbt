with source as (

    select * from {{ source('wwi', 'sales__customer_transactions') }}

),

renamed as (

    select
        CustomerTransactionID                    as customer_transaction_id,
        CustomerID                               as customer_id,
        TransactionTypeID                        as transaction_type_id,
        cast(InvoiceID as bigint)                as invoice_id,
        cast(PaymentMethodID as bigint)          as payment_method_id,
        TransactionDate                          as transaction_date,
        AmountExcludingTax                       as amount_excluding_tax,
        TaxAmount                                as tax_amount,
        TransactionAmount                        as transaction_amount,
        OutstandingBalance                       as outstanding_balance,
        FinalizationDate                         as finalization_date,
        IsFinalized                              as is_finalized,
        LastEditedWhen                           as last_edited_at,
        _loaded_at                               as _loaded_at
    from source

)

select * from renamed
