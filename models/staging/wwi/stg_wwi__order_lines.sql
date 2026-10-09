with source as (

    select * from {{ source('wwi', 'sales__order_lines') }}

),

renamed as (

    select
        OrderLineID                              as order_line_id,
        OrderID                                  as order_id,
        StockItemID                              as stock_item_id,
        Description                              as description,
        PackageTypeID                            as package_type_id,
        Quantity                                 as quantity,
        UnitPrice                                as unit_price,
        TaxRate                                  as tax_rate,
        PickedQuantity                           as picked_quantity,
        PickingCompletedWhen                     as picking_completed_at,
        LastEditedWhen                           as last_edited_at,
        _loaded_at                               as _loaded_at
    from source

)

select * from renamed
