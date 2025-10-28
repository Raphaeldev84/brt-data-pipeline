{{
  config(
    materialized='table',
    partition_by={
      "field": "timestamp_gps",
      "data_type": "timestamp",
      "granularity": "day"
    },
    cluster_by=["linha", "id_veiculo"]
  )
}}

WITH source_data AS (
    SELECT *
    FROM {{ ref('brt_gps_data') }}
),

cleaned_data AS (
    SELECT
        id_veiculo,
        linha,
        placa,
        latitude,
        longitude,
        velocidade,
        direcao,
        sentido,
        vista,
        CASE 
            WHEN latitude BETWEEN -23.1 AND -22.7 
             AND longitude BETWEEN -43.8 AND -43.1 
            THEN TRUE 
            ELSE FALSE 
        END AS coordenadas_validas,
        timestamp_gps,
        timestamp_captura,
        TIMESTAMP_DIFF(timestamp_captura, timestamp_gps, SECOND) AS delay_segundos,
        ignicao,
        hodometro,
        capacidade_pe,
        capacidade_sentado,
        capacidade_pe + capacidade_sentado AS capacidade_total,
        id_migracao_trajeto,
        CASE
            WHEN velocidade = 0 THEN 'parado'
            WHEN velocidade > 0 AND velocidade <= 20 THEN 'lento'
            WHEN velocidade > 20 AND velocidade <= 60 THEN 'moderado'
            WHEN velocidade > 60 THEN 'rapido'
            ELSE 'desconhecido'
        END AS categoria_velocidade,
        DATE(timestamp_gps) AS data_gps,
        EXTRACT(HOUR FROM timestamp_gps) AS hora_gps,
        EXTRACT(DAYOFWEEK FROM timestamp_gps) AS dia_semana,
        FORMAT_TIMESTAMP('%A', timestamp_gps) AS nome_dia_semana,
        CASE
            WHEN EXTRACT(HOUR FROM timestamp_gps) BETWEEN 6 AND 9 THEN 'pico_manha'
            WHEN EXTRACT(HOUR FROM timestamp_gps) BETWEEN 17 AND 20 THEN 'pico_tarde'
            ELSE 'fora_pico'
        END AS periodo_dia
    FROM source_data
    WHERE 
        id_veiculo IS NOT NULL
        AND latitude IS NOT NULL
        AND longitude IS NOT NULL
        AND timestamp_gps IS NOT NULL
),

deduplicated AS (
    SELECT * EXCEPT(row_num)
    FROM (
        SELECT *,
            ROW_NUMBER() OVER (
                PARTITION BY id_veiculo, timestamp_gps 
                ORDER BY timestamp_captura DESC
            ) AS row_num
        FROM cleaned_data
    )
    WHERE row_num = 1
)

SELECT * FROM deduplicated
