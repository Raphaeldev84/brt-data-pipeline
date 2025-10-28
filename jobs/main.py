"""
Pipeline ELT - BRT Rio de Janeiro
Ponto de entrada principal da aplicação
"""

import os
from pathlib import Path
from src.flows import brt_scheduler_flow
from src.utils import log
from src.constants import constants

def setup_credentials():
    """Configura automaticamente as credenciais do GCP"""
    # Caminho para o arquivo de credenciais
    credentials_file = "credentials/brt-pipeline-517842fb3685.json"
    credentials_path = Path(__file__).parent / credentials_file
    
    if credentials_path.exists():
        # Define a variável de ambiente
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(credentials_path.absolute())
        log(f"Credenciais GCP configuradas: {credentials_path.name}")
        return True
    else:
        log(f"Arquivo de credenciais não encontrado: {credentials_file}")
        log("Upload para GCS não será possível.")
        return False

def setup_environment():
    """Configura todas as variáveis de ambiente necessárias"""
    # Configura credenciais GCP
    setup_credentials()
    
    # Configura variáveis de ambiente do GCP
    os.environ['GCP_PROJECT_ID'] = constants.GCP_PROJECT_ID.value
    os.environ['GCP_BUCKET_NAME'] = constants.GCP_BUCKET_NAME.value
    os.environ['GCP_DATASET_ID'] = constants.GCP_DATASET_ID.value
    
    # Configura diretórios do DBT
    os.environ['DBT_PROJECT_DIR'] = './dbt/brt_project'
    os.environ['DBT_PROFILES_DIR'] = './dbt'
    
    log("Pipeline BRT configurada e pronta para execução")

if __name__ == "__main__":
    # Configura ambiente completo
    setup_environment()
    
    # Inicia o scheduler automático usando scheduler.json
    # Irá executar de 1 em 1 minuto conforme configurado no scheduler.json
    brt_scheduler_flow()