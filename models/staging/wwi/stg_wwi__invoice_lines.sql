with source as (

    select * from {{ source('wwi', 'sales__invoice_lines') }}

),

renamed as (

    select
        InvoiceLineID                            as invoice_line_id,
        InvoiceID                                as invoice_id,
        StockItemID                              as stock_item_id,
        Description                              as description,
        PackageTypeID                            as package_type_id,
        Quantity                                 as quantity,
        UnitPrice                                as unit_price,
        TaxRate                                  as tax_rate,
        TaxAmount                                as tax_amount,
        LineProfit                               as line_profit,
        ExtendedPrice                            as extended_price,
        LastEditedWhen                           as last_edited_at,
        _loaded_at                               as _loaded_at
    from source

)

select * from renamed
