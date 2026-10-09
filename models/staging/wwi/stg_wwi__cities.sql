with source as (

    select * from {{ source('wwi', 'application__cities') }}

),

renamed as (

    select
        CityID                                   as city_id,
        CityName                                 as city_name,
        StateProvinceID                          as state_province_id,
        Location                                 as location_wkt,
        cast(LatestRecordedPopulation as bigint) as latest_recorded_population,
        ValidFrom                                as valid_from,
        _loaded_at                               as _loaded_at
    from source

)

select * from renamed
