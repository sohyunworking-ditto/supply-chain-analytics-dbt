with source as (

    select * from {{ source('wwi', 'sales__buying_groups') }}

),

renamed as (

    select
        BuyingGroupID                            as buying_group_id,
        BuyingGroupName                          as buying_group_name,
        ValidFrom                                as valid_from,
        _loaded_at                               as _loaded_at
    from source

)

select * from renamed
