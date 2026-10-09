with source as (

    select * from {{ source('wwi', 'application__state_provinces') }}

),

renamed as (

    select
        StateProvinceID                          as state_province_id,
        StateProvinceCode                        as state_province_code,
        StateProvinceName                        as state_province_name,
        CountryID                                as country_id,
        SalesTerritory                           as sales_territory,
        LatestRecordedPopulation                 as latest_recorded_population,
        ValidFrom                                as valid_from,
        _loaded_at                               as _loaded_at
    from source

)

select * from renamed
