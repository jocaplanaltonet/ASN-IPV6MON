#!/bin/bash

# ==========================================
# CONFIGURAÇÃO DE ESCOPO (Padrão: BR)
# ==========================================
COUNTRY="BR"

# Valida os argumentos mínimos (Ex: ./ipv6.sh 52913 capable)
ASN="${1}"
METRIC="${2}"

if [ -z "$ASN" ] || [ -z "$METRIC" ]; then
    echo "0.00"
    exit 1
fi

# URL de visualização utilizando a variável de escopo geográfico
URL="https://stats.labs.apnic.net/ipv6/AS${ASN}?c=${COUNTRY}&p=1&v=1&w=30&x=1"

# 1. Faz o curl e isola a linha de dados do teu ASN
LINHA_HTML=$(curl -s -k -L -H "User-Agent: Mozilla/5.0" "$URL" | grep "/AS${ASN}" | head -n 1)

if [ -z "$LINHA_HTML" ]; then
    echo "0.00"
    exit 0
fi

# 2. Faz o parse de cada informação usando o AWK e cut
CAPABLE=$(echo "$LINHA_HTML" | awk -F '{v: ' '{print $2}' | cut -d',' -f1 | tr -d ' ')
PREFERRED=$(echo "$LINHA_HTML" | awk -F '{v: ' '{print $3}' | cut -d',' -f1 | tr -d ' ')

# O ASNAME vem logo após "AS52913 - " e vai até fechar as aspas (")
ASNAME=$(echo "$LINHA_HTML" | awk -F "\",\"AS${ASN} - " '{print $2}' | cut -d'"' -f1)

# Se o nome vier vazio por algum motivo, define um padrão
[ -z "$ASNAME" ] && ASNAME="Unknown"

# 3. Trata os retornos baseados no argumento digitado
case "$METRIC" in
    "asnum")
        echo "$ASN"
        ;;
    "asname")
        echo "$ASNAME"
        ;;
    "capable")
        echo "$CAPABLE"
        ;;
    "preferred")
        echo "$PREFERRED"
        ;;
    "all")
        # Saída elegante em formato JSON estruturado incluindo a variável consultada
        echo "{\"asn\": \"$ASN\", \"asname\": \"$ASNAME\", \"country\": \"$COUNTRY\", \"capable\": \"$CAPABLE\", \"preferred\": \"$PREFERRED\"}"
        ;;
    *)
        # Caso digite uma métrica inválida
        echo "0.00"
        ;;
esac
