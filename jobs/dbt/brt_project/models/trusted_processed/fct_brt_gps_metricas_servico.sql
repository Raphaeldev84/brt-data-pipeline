{{
  config(
    materialized='incremental',
    unique_key=['data', 'linha', 'periodo_dia'],
    partition_by={
      "field": "data",
      "data_type": "date",
      "granularity": "day"
    }
  )
}}

WITH silver_data AS (
    SELECT *
    FROM {{ ref('fct_brt_gps_data') }}
    WHERE coordenadas_validas = TRUE
),

agregacao_diaria AS (
    SELECT
        data_gps AS data,
        linha,
        periodo_dia,
        COUNT(DISTINCT id_veiculo) AS qtd_veiculos,
        COUNT(*) AS total_registros,
        ROUND(AVG(velocidade), 2) AS velocidade_media,
        MIN(velocidade) AS velocidade_minima,
        MAX(velocidade) AS velocidade_maxima,
        COUNTIF(categoria_velocidade = 'parado') AS veiculos_parados,
        COUNTIF(categoria_velocidade = 'lento') AS veiculos_lentos,
        COUNTIF(categoria_velocidade = 'moderado') AS veiculos_moderados,
        COUNTIF(categoria_velocidade = 'rapido') AS veiculos_rapidos,
        ROUND(AVG(delay_segundos), 2) AS delay_medio_segundos,
        MAX(delay_segundos) AS delay_maximo_segundos,
        AVG(capacidade_total) AS capacidade_media_frota,
        SUM(capacidade_total) AS capacidade_total_frota,
        ROUND(AVG(hodometro), 2) AS hodometro_medio,
        MAX(etl_update_date) AS etl_update_date
    FROM silver_data
    GROUP BY data_gps, linha, periodo_dia
)

SELECT 
    data,
    linha,
    periodo_dia,
    qtd_veiculos,
    total_registros,
    velocidade_media,
    velocidade_minima,
    velocidade_maxima,
    veiculos_parados,
    veiculos_lentos,
    veiculos_moderados,
    veiculos_rapidos,
    delay_medio_segundos,
    delay_maximo_segundos,
    capacidade_media_frota,
    capacidade_total_frota,
    hodometro_medio,
    ROUND(SAFE_DIVIDE(veiculos_parados, total_registros) * 100, 2) AS pct_parados,
    ROUND(SAFE_DIVIDE(veiculos_lentos, total_registros) * 100, 2) AS pct_lentos,
    ROUND(SAFE_DIVIDE(veiculos_moderados, total_registros) * 100, 2) AS pct_moderados,
    ROUND(SAFE_DIVIDE(veiculos_rapidos, total_registros) * 100, 2) AS pct_rapidos,
    etl_update_date
FROM agregacao_diaria
WHERE 1=1
{% if is_incremental() %}
  AND etl_update_date > (SELECT MAX(etl_update_date) FROM {{ this }})
{% endif %}

