with source as (

    select * from {{ source('wwi', 'sales__orders') }}

),

renamed as (

    select
        OrderID                                  as order_id,
        CustomerID                               as customer_id,
        SalespersonPersonID                      as salesperson_person_id,
        cast(PickedByPersonID as bigint)         as picked_by_person_id,
        ContactPersonID                          as contact_person_id,
        cast(BackorderOrderID as bigint)         as backorder_order_id,
        OrderDate                                as order_date,
        ExpectedDeliveryDate                     as expected_delivery_date,
        CustomerPurchaseOrderNumber              as customer_purchase_order_number,
        IsUndersupplyBackordered                 as is_undersupply_backordered,
        PickingCompletedWhen                     as picking_completed_at,
        LastEditedWhen                           as last_edited_at,
        _loaded_at                               as _loaded_at
    from source

)

select * from renamed
