with source as (

    select * from {{ source('wwi', 'warehouse__stock_item_holdings') }}

),

renamed as (

    select
        StockItemID                              as stock_item_id,
        QuantityOnHand                           as quantity_on_hand,
        BinLocation                              as bin_location,
        LastStocktakeQuantity                    as last_stocktake_quantity,
        LastCostPrice                            as last_cost_price,
        ReorderLevel                             as reorder_level,
        TargetStockLevel                         as target_stock_level,
        LastEditedWhen                           as last_edited_at,
        _loaded_at                               as _loaded_at
    from source

)

select * from renamed
