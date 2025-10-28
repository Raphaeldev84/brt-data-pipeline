# 🚍 Pipeline ELT - BRT Rio de Janeiro

Pipeline de dados em tempo real para captura, armazenamento e transformação de dados GPS dos veículos do BRT, seguindo a arquitetura Medallion (Staging → Trusted Base → Trusted Processed).

## 📋 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Arquitetura](#arquitetura)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Pré-requisitos](#pré-requisitos)
- [Configuração](#configuração)
- [Como Executar](#como-executar)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Modelos DBT](#modelos-dbt)
- [Extras Implementados](#extras-implementados)

## 🎯 Sobre o Projeto

Este projeto implementa uma pipeline ELT completa que:

1. **Captura** dados GPS da API do BRT minuto a minuto
2. **Gera** arquivos CSV consolidados a cada 10 minutos de coleta
3. **Armazena** os arquivos no Google Cloud Storage (GCS)
4. **Transforma** os dados no BigQuery através de modelos DBT seguindo a arquitetura Medallion

### Fluxo de Execução

```
API BRT → Coleta (1 min) → CSV (10 min) → GCS → BigQuery (Staging) → Trusted Base → Trusted Processed
```

## 🏗️ Arquitetura

### Arquitetura Medallion

- **Staging (Raw)**: Tabela externa no BigQuery conectada aos arquivos CSV no GCS
- **Trusted Base (Cleaned)**: Dados limpos, tipados e enriquecidos
- **Trusted Processed (Aggregated)**: Métricas e agregações para análise

### Componentes

- **Prefect 1.4.1**: Orquestração da pipeline
- **Docker**: Containerização do Prefect Server e Agent
- **DBT**: Transformação de dados (Staging → Trusted Base → Trusted Processed)
- **GCS**: Armazenamento dos arquivos CSV
- **BigQuery**: Data Warehouse

## 🛠️ Tecnologias Utilizadas

- Python 3.8+
- Prefect 1.4.1
- DBT Core & DBT BigQuery
- Docker & Docker Compose
- Google Cloud Platform (GCS + BigQuery)
- Pandas

## 📦 Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop) instalado
- [Python 3.8+](https://www.python.org/downloads/) instalado
- Conta no [Google Cloud Platform](https://cloud.google.com/)
- Projeto GCP criado com os seguintes serviços habilitados:
  - Google Cloud Storage API
  - BigQuery API

## ⚙️ Configuração

### 1. Clone o Repositório

```bash
git clone <url-do-repositorio>
cd desafio_civitas
```

### 2. Configuração do Google Cloud Platform

#### 2.1. Criar Service Account

1. Acesse o [Console GCP](https://console.cloud.google.com/)
2. Navegue até **IAM & Admin → Service Accounts**
3. Clique em **Create Service Account**
4. Defina um nome (ex: `brt-pipeline`)
5. Adicione as seguintes permissões:
   - **Storage Admin**
   - **BigQuery Admin**
6. Crie e faça download da chave JSON

#### 2.2. Criar Bucket no GCS

```bash
# Substitua pelo nome único do seu bucket
gsutil mb -l southamerica-east1 gs://brt-data-pipeline-123
```

#### 2.3. Criar Dataset no BigQuery

```bash
bq mk --location=southamerica-east1 brt_gps
```

### 3. Configurar Credenciais

1. Salve o arquivo JSON de credenciais em:
   ```
   jobs/credentials/brt-pipeline-517842fb3685.json
   ```

2. Atualize as constantes no arquivo `jobs/src/constants.py`:
   ```python
   GCP_PROJECT_ID = "seu-projeto-id"
   GCP_BUCKET_NAME = "seu-bucket-name"
   GCP_DATASET_ID = "brt_gps"
   ```

### 4. Instalar Dependências (Opcional - para desenvolvimento local)

```bash
cd jobs
pip install -r requirements.txt
```

### 5. Instalar Dependências do DBT (Obrigatório - apenas uma vez)

```bash
cd jobs/dbt/brt_project
dbt deps
```

**Nota**: Este comando instala o pacote `dbt_external_tables` necessário para criar tabelas externas no BigQuery. Precisa ser executado apenas uma vez após clonar o repositório.

## 🚀 Como Executar

### Método 1: Docker (Recomendado)

#### 1. Iniciar Prefect Server e Agent

```bash
cd jobs
docker-compose up -d
```

Aguarde alguns segundos para os serviços iniciarem. Verifique o status:

```bash
docker-compose ps
```

#### 2. Acessar a UI do Prefect

Abra o navegador em: [http://localhost:4200](http://localhost:4200)

#### 3. Executar a Pipeline

**Importante**: Antes da primeira execução, instale as dependências do DBT:

```bash
# Dentro do container (apenas na primeira vez)
cd dbt/brt_project
dbt deps
cd ../..
```

Agora execute o flow principal:

```bash
# Execute o flow principal
python main.py
```

A pipeline irá:
- Coletar dados da API a cada 1 minuto
- Gerar CSV a cada 10 coletas (10 minutos)
- Fazer upload para o GCS
- Executar modelos DBT automaticamente

#### 4. Parar a Execução

Pressione `Ctrl+C` no terminal onde a pipeline está rodando.

#### 5. Desligar os Serviços

```bash
docker-compose down
```

### Método 2: Execução Local (Desenvolvimento)

```bash
cd jobs

# Configure as variáveis de ambiente
$env:GOOGLE_APPLICATION_CREDENTIALS="./credentials/brt-pipeline-517842fb3685.json"
$env:GCP_PROJECT_ID="seu-projeto-id"
$env:GCP_BUCKET_NAME="seu-bucket-name"

# Execute a pipeline
python main.py
```

## 📁 Estrutura do Projeto

```
desafio_civitas/
├── jobs/
│   ├── main.py                          # Ponto de entrada da aplicação
│   ├── docker-compose.yml               # Orquestração dos containers
│   ├── Dockerfile                       # Imagem do Prefect Agent
│   ├── requirements.txt                 # Dependências Python
│   ├── config/
│   │   └── scheduler.json               # Configuração do agendamento (1 min)
│   ├── credentials/
│   │   └── brt-pipeline-*.json          # Credenciais GCP (não versionado)
│   ├── data/
│   │   └── brt_10min_data_*.csv         # CSVs gerados (10 minutos cada)
│   ├── dbt/
│   │   ├── profiles.yml                 # Configuração de conexão DBT
│   │   └── brt_project/
│   │       ├── dbt_project.yml          # Configuração do projeto DBT
│   │       ├── packages.yml             # Dependências (dbt_external_tables)
│   │       ├── macros/
│   │       │   └── get_brazil_date_path.sql  # Macro para particionamento
│   │       └── models/
│   │           ├── staging/
│   │           │   ├── sources.yml      # Tabela externa (GCS → BigQuery)
│   │           │   ├── brt_gps_data.sql # Modelo Staging
│   │           │   └── schema.yml       # Documentação Staging
│   │           ├── trusted_base/
│   │           │   ├── fct_brt_gps_data.sql  # Modelo Trusted Base
│   │           │   └── schema.yml            # Documentação Trusted Base
│   │           └── trusted_processed/
│   │               ├── fct_brt_gps_metricas_servico.sql  # Métricas agregadas
│   │               └── schema.yml                        # Documentação Trusted Processed
│   └── src/
│       ├── constants.py                 # Constantes e configurações
│       ├── flows.py                     # Definição dos flows Prefect
│       ├── tasks.py                     # Tasks individuais
│       └── utils.py                     # Funções auxiliares
```

## 📊 Modelos DBT

### Staging Layer (`brt_gps_data`)

**Descrição**: Tabela externa no BigQuery conectada aos arquivos CSV no GCS.

**Particionamento**: Por data de extração (`data_extracao`) no formato `YYYYMMDD`

**Campos principais**:
- `id_veiculo`: Código do veículo
- `servico`: Linha/serviço do BRT
- `latitude`, `longitude`: Coordenadas GPS
- `timestamp_gps`: Data/hora do sinal GPS
- `velocidade`: Velocidade do veículo
- `data_extracao`: Data de captura dos dados

### Trusted Base Layer (`fct_brt_gps_data`)

**Descrição**: Dados limpos, tipados e enriquecidos com validações.

**Transformações**:
- Conversão de tipos de dados
- Validação de coordenadas GPS
- Normalização de campos
- Remoção de duplicatas

### Trusted Processed Layer (`fct_brt_gps_metricas_servico`)

**Descrição**: Métricas agregadas por serviço e período.

**Métricas calculadas**:
- Total de veículos por serviço
- Velocidade média, mínima e máxima
- Cobertura geográfica (distância percorrida)
- Percentual de veículos com ignição ligada

## ✨ Extras Implementados

### ✅ Commits Convencionais
- Seguindo padrão [Conventional Commits](https://www.conventionalcommits.org/)
- Exemplos: `feat:`, `fix:`, `docs:`, `refactor:`

### ✅ Documentação Detalhada
- Arquivos `schema.yml` para cada layer (Bronze, Silver, Gold)
- Descrições de modelos e campos
- Propagação automática para BigQuery (`+persist_docs`)

### ✅ Testes de Qualidade
- Testes de unicidade, não-nulidade e relacionamentos
- Validações de valores aceitos e intervalos
- Executados automaticamente pelo DBT

### ✅ Particionamento Inteligente
- Bronze: Particionado por `data_extracao`
- Otimização de queries e custos no BigQuery

### ✅ Organização e Boas Práticas
- Código modular e reutilizável
- Separação de responsabilidades (tasks, flows, utils)
- Type hints e docstrings
- Logging estruturado

### ✅ Arquitetura Medallion Completa
- **Bronze**: Raw data (tabela externa)
- **Silver**: Cleaned data (validado e tipado)
- **Gold**: Business metrics (agregações)

## 📸 Verificação no BigQuery

Após executar a pipeline, você poderá visualizar no BigQuery:

1. **Dataset**: `brt_gps`
2. **Tabelas**:
   - `brt_bronze` (externa, conectada ao GCS)
   - `fct_brt_silver` (transformada)
   - `fct_brt_metricas_servico` (métricas agregadas)

3. **Descrições**: As descrições dos campos estarão visíveis na UI do BigQuery graças à configuração `+persist_docs`

### Queries de Exemplo

```sql
-- Visualizar dados Bronze
SELECT * FROM `brt_gps.brt_bronze` LIMIT 10;

-- Visualizar dados Silver
SELECT * FROM `brt_gps.fct_brt_silver` LIMIT 10;

-- Visualizar métricas Gold
SELECT * FROM `brt_gps.fct_brt_metricas_servico`
ORDER BY data_extracao DESC, total_veiculos DESC
LIMIT 10;
```

## 🔧 Troubleshooting

### Erro de Credenciais

```
google.auth.exceptions.DefaultCredentialsError
```

**Solução**: Verifique se o arquivo de credenciais está no local correto e se as variáveis de ambiente estão configuradas.

### Erro de Permissões no GCS

```
403 Forbidden
```

**Solução**: Verifique se a Service Account tem as permissões `Storage Admin` e `BigQuery Admin`.

### DBT não encontra os arquivos

```
Path does not exist
```

**Solução**: Certifique-se de que ao menos um arquivo CSV foi gerado e enviado ao GCS antes de executar o DBT.

## 📝 Notas

- A pipeline coleta dados a cada **1 minuto**
- Um arquivo CSV é gerado a cada **10 coletas** (10 minutos)
- Os modelos DBT são executados automaticamente após cada upload
- Os arquivos CSV são armazenados em `jobs/data/` localmente e no GCS

## 👨‍💻 Autor

Desenvolvido como solução para o Desafio Técnico de Data Engineer - CIVITAS

## 📄 Licença

Este projeto foi desenvolvido para fins educacionais e de avaliação técnica.
