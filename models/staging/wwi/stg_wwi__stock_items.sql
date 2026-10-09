with source as (

    select * from {{ source('wwi', 'warehouse__stock_items') }}

),

renamed as (

    select
        StockItemID                              as stock_item_id,
        StockItemName                            as stock_item_name,
        SupplierID                               as supplier_id,
        cast(ColorID as bigint)                  as color_id,
        UnitPackageID                            as unit_package_id,
        OuterPackageID                           as outer_package_id,
        Brand                                    as brand,
        Size                                     as size,
        LeadTimeDays                             as lead_time_days,
        QuantityPerOuter                         as quantity_per_outer,
        IsChillerStock                           as is_chiller_stock,
        Barcode                                  as barcode,
        TaxRate                                  as tax_rate,
        UnitPrice                                as unit_price,
        RecommendedRetailPrice                   as recommended_retail_price,
        TypicalWeightPerUnit                     as typical_weight_per_unit,
        ValidFrom                                as valid_from,
        _loaded_at                               as _loaded_at
    from source

)

select * from renamed
