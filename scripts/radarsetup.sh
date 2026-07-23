#!/bin/bash

# 1. Criar o diretório base
mkdir -p /opt/qrator

# 2. Criar o ambiente virtual isolado
python3 -m venv /opt/qrator/venv

# 3. Definir o caminho de cache do Chromium dentro do diretório do Qrator
export PLAYWRIGHT_BROWSERS_PATH="/opt/qrator/browser_cache"

# 4. Instalar as dependências e o Chromium
/opt/qrator/venv/bin/pip install --upgrade pip
/opt/qrator/venv/bin/pip install playwright
/opt/qrator/venv/bin/python3 -m playwright install chromium

# 5. Conceder acesso de execução a todos os usuários (incluindo o zabbix)
chmod -R 755 /opt/qrator

echo "✅ Instalação em /opt/qrator concluída com sucesso!"
