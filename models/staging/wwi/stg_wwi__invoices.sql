with source as (

    select * from {{ source('wwi', 'sales__invoices') }}

),

renamed as (

    select
        InvoiceID                                as invoice_id,
        CustomerID                               as customer_id,
        BillToCustomerID                         as bill_to_customer_id,
        OrderID                                  as order_id,
        DeliveryMethodID                         as delivery_method_id,
        ContactPersonID                          as contact_person_id,
        AccountsPersonID                         as accounts_person_id,
        SalespersonPersonID                      as salesperson_person_id,
        PackedByPersonID                         as packed_by_person_id,
        InvoiceDate                              as invoice_date,
        CustomerPurchaseOrderNumber              as customer_purchase_order_number,
        IsCreditNote                             as is_credit_note,
        TotalDryItems                            as total_dry_items,
        TotalChillerItems                        as total_chiller_items,
        DeliveryRun                              as delivery_run,
        RunPosition                              as run_position,
        ConfirmedDeliveryTime                    as confirmed_delivery_at,
        ConfirmedReceivedBy                      as confirmed_received_by,
        LastEditedWhen                           as last_edited_at,
        _loaded_at                               as _loaded_at
    from source

)

select * from renamed
