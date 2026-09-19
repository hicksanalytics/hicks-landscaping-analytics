select
    cast(date as date) as weather_date,
    city,
    cast(high_temp_f as double) as high_temp_f,
    cast(precip_inches as double) as precip_inches,
    cast(rain_flag as integer) as rain_flag,
    cast(severe_weather_flag as integer) as severe_weather_flag
from {{ ref('weather_daily') }}
