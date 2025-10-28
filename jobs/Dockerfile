FROM prefecthq/prefect:1.4.1-python3.8

WORKDIR /opt/prefect

# Copia os arquivos do projeto
COPY requirements.txt .
COPY main.py .
COPY config/ ./config/
COPY src/ ./src/
COPY dbt/ ./dbt/

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Define variáveis de ambiente
ENV PREFECT__BACKEND=server
ENV PREFECT__SERVER__HOST=http://prefect-server
ENV PREFECT__SERVER__PORT=4200
ENV PYTHONPATH=/opt/prefect

CMD ["python", "main.py"]
