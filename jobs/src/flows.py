from prefect import Flow, task
from src.tasks import (
    download_data,
    parse_data,
    save_data_to_csv,
    get_current_timestamp,
    start_scheduler,
    upload_to_gcs,
    run_dbt_models
)

def brt_flow():
    """
    Flow principal para coleta de dados GPS BRT.
    
    Segue o padrão:
    1. Obtém timestamp atual
    2. Download dos dados da API
    3. Parse e mapeamento dos campos
    4. Acumulação dos dados em memória
    5. Consolidação automática de DataFrame a cada 10 coletas
    6. Upload direto para GCS (sem salvar localmente)
    7. Execução dos modelos DBT (Staging → Trusted Base → Trusted Processed)
    """
    with Flow("brt-gps-collector") as flow:
        # Obtém timestamp
        timestamp = get_current_timestamp()
        
        # Download dos dados
        raw_status = download_data()
        
        # Parse dos dados
        treated_status = parse_data(status=raw_status, timestamp=timestamp)
        
        # Acumula dados (retorna DataFrame consolidado ou None)
        data_dict = save_data_to_csv(status=treated_status)
        
        # Upload para GCS (só executa se houver dados consolidados)
        upload_result = upload_to_gcs(data_dict=data_dict)
        
        # Executa modelos DBT (só se upload foi bem-sucedido)
        dbt_result = run_dbt_models(upload_result=upload_result)
    
    return flow.run()

def brt_scheduler_flow():
    """
    Flow para iniciar o scheduler BRT.
    
    Lê configuração do scheduler_config.json e executa brt_flow
    automaticamente no intervalo configurado (padrão: 1 minuto).
    
    Para parar: pressione Ctrl+C
    """
    start_scheduler()