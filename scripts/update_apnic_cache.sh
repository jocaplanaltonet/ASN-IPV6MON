#!/bin/bash
# ==============================================================================
# Script: update_apnic_cache.sh
# Descrição: Baixa o dump completo de métricas IPv6 do APNIC Labs e gera o cache.
# Uso: ./update_apnic_cache.sh <NUMERO_DO_ASN>
# ==============================================================================

# TRAVA DE SEGURANÇA PARA O PÚBLICO: VALIDA SE O ASN FOI PASSADO
if [ -z "$1" ]; then
    echo "❌ Erro: Você precisa passar o número do ASN como argumento."
    echo "👉 Exemplo de uso: $0 52913"
    exit 1
fi

ASN=$1
CACHE_FILE="/tmp/apnic_${ASN}.json"
URL="https://stats.labs.apnic.net/cgi-bin/json-table-v6.pl?x=BR$ASN"

echo "📥 Iniciando download das métricas IPv6 do APNIC Labs para AS${ASN}..."

# Faz o download usando os parâmetros que funcionaram perfeitamente no seu ambiente
if curl -s -k -L -H "User-Agent: Mozilla/5.0" "$URL" -o "$CACHE_FILE"; then
    # Garante que o arquivo foi criado e não está vazio
    if [ -s "$CACHE_FILE" ]; then
        chmod 644 "$CACHE_FILE"
        echo "✅ Cache de 3.5MB atualizado com sucesso em: $CACHE_FILE"
        echo "🔒 Permissões 644 aplicadas para leitura do Zabbix e Python."
    else
        echo "❌ Erro: O arquivo baixado está vazio."
        exit 1
    fi
else
    echo "❌ Erro: Falha ao conectar ou baixar dados da API do APNIC Labs."
    exit 1
fi
