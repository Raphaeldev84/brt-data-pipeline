{{
  config(
    materialized='table',
    schema='staging',
    pre_hook=[
      "DROP EXTERNAL TABLE IF EXISTS `{{ target.project }}.{{ schema }}.brt_raw_data_external`",
      """
      CREATE EXTERNAL TABLE `{{ target.project }}.{{ schema }}.brt_raw_data_external`
      (
        id_veiculo STRING,
        linha STRING,
        latitude STRING,
        longitude STRING,
        timestamp_gps STRING,
        velocidade STRING,
        sentido STRING,
        vista STRING,
        placa STRING,
        direcao STRING,
        ignicao STRING,
        hodometro STRING,
        capacidade_pe STRING,
        capacidade_sentado STRING,
        id_migracao_trajeto STRING,
        timestamp_captura STRING
      )
      OPTIONS (
        format = 'CSV',
        uris = ['gs://{{ var('gcs_bucket') }}/staging/{{ get_brazil_date_path() }}/*'],
        skip_leading_rows = 1,
        field_delimiter = ',',
        max_bad_records = 10000,
        allow_jagged_rows = true,
        allow_quoted_newlines = true,
        ignore_unknown_values = true,
        encoding = 'UTF-8'
      )
      """
    ]
  )
}}

SELECT
    SAFE_CAST(id_veiculo AS STRING) as id_veiculo,
    SAFE_CAST(linha AS INT64) as linha,
    SAFE_CAST(latitude AS FLOAT64) as latitude,
    SAFE_CAST(longitude AS FLOAT64) as longitude,
    SAFE.PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%Ez', timestamp_gps) as timestamp_gps,
    SAFE_CAST(velocidade AS FLOAT64) as velocidade,
    sentido,
    vista,
    placa,
    SAFE_CAST(direcao AS FLOAT64) as direcao,
    SAFE_CAST(ignicao AS INT64) as ignicao,
    SAFE_CAST(hodometro AS FLOAT64) as hodometro,
    SAFE_CAST(capacidade_pe AS INT64) as capacidade_pe,
    SAFE_CAST(capacidade_sentado AS INT64) as capacidade_sentado,
    SAFE_CAST(id_migracao_trajeto AS INT64) as id_migracao_trajeto,
    SAFE.PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*S', timestamp_captura) as etl_update_date
FROM `{{ target.project }}.{{ schema }}.brt_raw_data_external`
