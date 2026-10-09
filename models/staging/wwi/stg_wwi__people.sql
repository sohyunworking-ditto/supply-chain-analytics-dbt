with source as (

    select * from {{ source('wwi', 'application__people') }}

),

renamed as (

    select
        PersonID                                 as person_id,
        FullName                                 as full_name,
        PreferredName                            as preferred_name,
        IsEmployee                               as is_employee,
        IsSalesperson                            as is_salesperson,
        IsSystemUser                             as is_system_user,
        EmailAddress                             as email_address,
        PhoneNumber                              as phone_number,
        ValidFrom                                as valid_from,
        _loaded_at                               as _loaded_at
    from source

)

select * from renamed
