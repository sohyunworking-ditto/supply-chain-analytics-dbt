with source as (

    select * from {{ source('wwi', 'sales__customers') }}

),

renamed as (

    select
        CustomerID                               as customer_id,
        CustomerName                             as customer_name,
        BillToCustomerID                         as bill_to_customer_id,
        CustomerCategoryID                       as customer_category_id,
        cast(BuyingGroupID as bigint)            as buying_group_id,
        PrimaryContactPersonID                   as primary_contact_person_id,
        cast(AlternateContactPersonID as bigint) as alternate_contact_person_id,
        DeliveryMethodID                         as delivery_method_id,
        DeliveryCityID                           as delivery_city_id,
        PostalCityID                             as postal_city_id,
        CreditLimit                              as credit_limit,
        AccountOpenedDate                        as account_opened_date,
        StandardDiscountPercentage               as standard_discount_percentage,
        IsStatementSent                          as is_statement_sent,
        IsOnCreditHold                           as is_on_credit_hold,
        PaymentDays                              as payment_days,
        DeliveryLocation                         as delivery_location_wkt,
        ValidFrom                                as valid_from,
        _loaded_at                               as _loaded_at
    from source

)

select * from renamed
