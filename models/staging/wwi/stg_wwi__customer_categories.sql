with source as (

    select * from {{ source('wwi', 'sales__customer_categories') }}

),

renamed as (

    select
        CustomerCategoryID                       as customer_category_id,
        CustomerCategoryName                     as customer_category_name,
        ValidFrom                                as valid_from,
        _loaded_at                               as _loaded_at
    from source

)

select * from renamed
