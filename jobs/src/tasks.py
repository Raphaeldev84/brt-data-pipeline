import requests
import pandas as pd
from prefect import task
from src.utils import log
import os
from datetime import datetime, timedelta
import json
import time
import subprocess
from src.constants import constants
from google.cloud import storage

# Acumulador em memória para as coletas (persistirá enquanto o processo scheduler estiver rodando)
ACCUMULATED = []

@task
def download_data():
    """Baixa dados da API BRT usando constantes"""
    url = constants.GPS_BRT_API_URL.value
    timeout = constants.MAX_TIMEOUT_SECONDS.value
    
    try:
        response = requests.get(url, timeout=timeout)
        data = response.json()
        log("Dados baixados com sucesso")
        return {"data": data, "error": None}
    except Exception as e:
        error_msg = f"Erro ao baixar dados: {e}"
        log(error_msg)
        return {"data": None, "error": error_msg}

@task
def parse_data(status: dict, timestamp):
    """Processa dados aplicando mapeamento de campos das constantes"""
    
    # Check previous error
    if status["error"] is not None:
        return {"data": pd.DataFrame(), "error": status["error"]}
    
    try:
        # Pega timezone e mapeamento das constantes
        timezone = constants.TIMEZONE.value
        mapping = constants.GPS_BRT_MAPPING_KEYS.value
        
        # Extrai dados
        data = status["data"]
        veiculos = data.get('veiculos', data) if isinstance(data, dict) else data
        
        # Aplica mapeamento aos dados
        dados_mapeados = []
        for veiculo in veiculos:
            veiculo_mapeado = {}
            for api_key, db_key in mapping.items():
                if api_key in veiculo:
                    veiculo_mapeado[db_key] = veiculo[api_key]
            dados_mapeados.append(veiculo_mapeado)
        
        # Cria DataFrame
        df = pd.DataFrame(dados_mapeados)
        df['timestamp_captura'] = timestamp
        
        # Converte timestamp_gps se existir
        if 'timestamp_gps' in df.columns:
            df['timestamp_gps'] = (
                pd.to_datetime(df['timestamp_gps'], unit='ms')
                .dt.tz_localize('UTC')
                .dt.tz_convert(timezone)
            )
        
        # Remove duplicatas mantendo o primeiro registro
        df = df.drop_duplicates(subset=['id_veiculo', 'timestamp_gps'], keep='first')
        
        log(f"Processados {len(df)} veículos")
        return {"data": df, "error": None}
        
    except Exception as e:
        error_msg = f"Erro ao processar dados: {e}"
        log(error_msg)
        return {"data": pd.DataFrame(), "error": error_msg}

@task
def save_data_to_csv(status: dict):
    """Acumula dados em memória e prepara DataFrame a cada 10 coletas (10 minutos).

    Observação: isto funciona porque o `start_scheduler()` mantém o loop no mesmo
    processo. Se executar vários processos separados, será necessário um armazenamento
    externo (DB/arquivo).
    
    Retorna o DataFrame consolidado se atingir 10 coletas, None caso contrário.
    """

    # Check previous error
    if status["error"] is not None:
        return None

    try:
        df = status["data"]

        if df.empty:
            return None

        # Converte para dict (transforma Timestamps em strings)
        df_dict = df.to_dict(orient='records')

        # Converte timestamps para string
        for record in df_dict:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, pd.Timestamp):
                    record[key] = value.isoformat()

        # Adiciona novos dados no acumulador em memória
        ACCUMULATED.append({
            'timestamp': datetime.now().isoformat(),
            'data': df_dict
        })

        # Remove coletas antigas (mais de 10 minutos) — proteção adicional
        now = datetime.now()
        cutoff = now - timedelta(minutes=10)
        ACCUMULATED[:] = [
            item for item in ACCUMULATED
            if datetime.fromisoformat(item['timestamp']) >= cutoff
        ]

        log(f"Acumuladas {len(ACCUMULATED)} coletas")

        # Se temos 10 ou mais coletas, gera DataFrame consolidado e limpa o acumulador
        if len(ACCUMULATED) >= 10:
            df_consolidated = generate_consolidated_dataframe(ACCUMULATED)
            # limpa o acumulador após gerar o DataFrame
            ACCUMULATED.clear()
            return df_consolidated

        return None

    except Exception as e:
        error_msg = f"Erro ao processar dados: {e}"
        log(error_msg)
        return None

def generate_consolidated_dataframe(accumulated_data):
    """Gera DataFrame consolidado com dados acumulados (10 minutos).

    Usa o timestamp da primeira coleta do período para compor metadados.
    
    Retorna dict com DataFrame e metadados.
    """
    try:
        # Concatena todos os registros
        all_records = []
        for item in accumulated_data:
            all_records.extend(item['data'])

        if not all_records:
            return None

        # Cria DataFrame final
        df = pd.DataFrame(all_records)
        
        # Remove duplicatas do DataFrame final
        # Mantém o último registro em caso de duplicatas (mais recente)
        if 'id_veiculo' in df.columns and 'timestamp_gps' in df.columns:
            df = df.drop_duplicates(subset=['id_veiculo', 'timestamp_gps'], keep='last')

        # Usa o timestamp da primeira coleta para nome do arquivo
        try:
            start_ts = datetime.fromisoformat(accumulated_data[0]['timestamp'])
        except Exception:
            start_ts = datetime.now()

        log(f"DataFrame consolidado: {len(df)} registros")
        
        return {
            'dataframe': df,
            'timestamp': start_ts,
            'filename': f"brt_10min_data_{start_ts.strftime('%Y%m%d_%H%M%S')}.csv"
        }

    except Exception as e:
        log(f"Erro ao gerar DataFrame: {e}")
        return None

@task
def get_current_timestamp():
    """Retorna timestamp atual"""
    return datetime.now()

@task
def upload_to_gcs(data_dict: dict):
    """Faz upload do DataFrame para Google Cloud Storage como CSV
    
    Args:
        data_dict: Dict contendo 'dataframe', 'timestamp' e 'filename'
        
    Returns:
        dict com status do upload
    """
    if not data_dict or data_dict is None:
        return {"error": "No data", "uploaded": False}
    
    try:
        # Extrai informações
        df = data_dict['dataframe']
        filename = data_dict['filename']
        file_date = data_dict['timestamp']
        
        # Obtém configurações das constantes
        bucket_name = os.getenv('GCP_BUCKET_NAME', constants.GCP_BUCKET_NAME.value)
        
        # Inicializa cliente GCS
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        # Define o nome do blob (arquivo no GCS)
        # Organiza em partições por data: staging/YYYY/MM/DD/arquivo.csv
        blob_name = f"staging/{file_date.year}/{file_date.month:02d}/{file_date.day:02d}/{filename}"
        
        # Converte DataFrame para CSV string
        csv_string = df.to_csv(index=False)
        
        # Faz upload direto da string
        blob = bucket.blob(blob_name)
        blob.upload_from_string(csv_string, content_type='text/csv')
        
        log(f"Upload concluído: gs://{bucket_name}/{blob_name} ({len(df)} registros)")
        
        return {
            "error": None,
            "uploaded": True,
            "gcs_path": f"gs://{bucket_name}/{blob_name}",
            "blob_name": blob_name
        }
        
    except Exception as e:
        error_msg = f"Erro ao fazer upload para GCS: {e}"
        log(error_msg)
        return {"error": error_msg, "uploaded": False}

@task
def run_dbt_models(upload_result: dict):
    """Executa modelos DBT após upload bem-sucedido
    
    Args:
        upload_result: Resultado da task de upload
        
    Returns:
        dict com status da execução do DBT
    """
    # Só executa se o upload foi bem-sucedido
    if not upload_result.get('uploaded', False):
        return {"error": "Upload failed", "executed": False}
    
    try:
        dbt_project_dir = os.getenv('DBT_PROJECT_DIR', './dbt/brt_project')
        dbt_profiles_dir = os.getenv('DBT_PROFILES_DIR', './dbt')
        
        log("Executando DBT...")
        
        # Executa modelos
        result = subprocess.run(
            ['dbt', 'run', '--project-dir', dbt_project_dir, '--profiles-dir', dbt_profiles_dir],
            capture_output=True,
            text=True
        )
        
        # Verifica se houve erro
        if result.returncode != 0:
            if result.stdout:
                log(f"DBT stdout: {result.stdout}")
            if result.stderr:
                log(f"DBT stderr: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
        
        log("DBT executado com sucesso")
        
        return {
            "error": None,
            "executed": True,
            "output": result.stdout
        }
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Erro ao executar DBT:\nStdout: {e.stdout}\nStderr: {e.stderr}"
        log(error_msg)
        return {"error": error_msg, "executed": False}
    except Exception as e:
        error_msg = f"Erro ao executar DBT: {str(e)}"
        log(error_msg)
        return {"error": error_msg, "executed": False}

# ===== FUNCIONALIDADES DO SCHEDULER ===== #

def load_scheduler_config(config_file='config/scheduler.json'):
    """Carrega configuração do scheduler"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        log(f"Arquivo {config_file} não encontrado!")
        return None
    except json.JSONDecodeError:
        log(f"Erro ao ler {config_file}!")
        return None

def run_scheduled_flow():
    """Executa o flow BRT agendado"""
    try:
        from src.flows import brt_flow
        log(f"Executando coleta BRT...")
        result = brt_flow()
        log(f"Coleta concluída")
        return result
    except Exception as e:
        log(f"Erro na execução: {e}")
        return None

def start_scheduler():
    """Inicia o scheduler que executa coleta BRT em intervalos regulares"""
    config = load_scheduler_config()
    if not config:
        raise Exception("Não foi possível carregar a configuração do scheduler")
    
    interval_seconds = config['schedule']['interval']['minutes'] * 60
    
    log(f"Iniciando scheduler: {config['name']}")
    log(f"Intervalo: {config['schedule']['interval']['minutes']} minuto(s)")
    log("Pressione Ctrl+C para parar o scheduler")
    
    try:
        while True:
            run_scheduled_flow()
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        log("Scheduler parado!")
        return
