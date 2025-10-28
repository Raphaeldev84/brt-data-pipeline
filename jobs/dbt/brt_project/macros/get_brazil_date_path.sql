{% macro get_brazil_date_path() %}
    {%- set utc_now = run_started_at -%}
    {%- set brazil_offset = -3 -%}  {# UTC-3 para horário de Brasília #}
    {%- set brazil_time = modules.datetime.datetime(
        utc_now.year,
        utc_now.month,
        utc_now.day,
        utc_now.hour,
        utc_now.minute,
        utc_now.second
    ) + modules.datetime.timedelta(hours=brazil_offset) -%}
    {{- brazil_time.strftime('%Y/%m/%d') -}}
{% endmacro %}
