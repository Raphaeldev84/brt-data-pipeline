# -*- coding: utf-8 -*-
"""
Constant values for BRT GPS data processing
"""

from enum import Enum


class constants(Enum):  # pylint: disable=c0103
    """
    Constant values for BRT projects
    """

    # DEFAULT TIMEZONE #
    TIMEZONE = "America/Sao_Paulo"

    # RETRY POLICY #
    MAX_TIMEOUT_SECONDS = 60

    # GPS BRT #
    GPS_BRT_API_URL = "https://dados.mobilidade.rio/gps/brt"
    GPS_BRT_DATASET_ID = "br_rj_riodejaneiro_veiculos"

    # GOOGLE CLOUD PLATFORM #
    GCP_PROJECT_ID = "brt-pipeline"
    GCP_BUCKET_NAME = "brt-data-pipeline-123"
    GCP_DATASET_ID = "brt_gps"
    GCP_TABLE_STAGING = "brt_gps_data"

    GPS_BRT_MAPPING_KEYS = {
        "codigo": "id_veiculo",
        "linha": "linha",
        "latitude": "latitude",
        "longitude": "longitude",
        "dataHora": "timestamp_gps",
        "velocidade": "velocidade",
        "sentido": "sentido",
        "trajeto": "vista",
        "placa": "placa",
        "direcao": "direcao",
        "ignicao": "ignicao",
        "hodometro": "hodometro",
        "capacidadePeVeiculo": "capacidade_pe",
        "capacidadeSentadoVeiculo": "capacidade_sentado",
        "id_migracao_trajeto": "id_migracao_trajeto",
    }
