#!/bin/bash

COUNTRY="BR"
ASN="${1}"
METRIC="${2:-all}"

if [ -z "$ASN" ]; then
    echo "0.00"
    exit 1
fi

APNIC_LOADED=0
CAPABLE="0.00"
PREFERRED="0.00"
ASNAME="Unknown"

get_apnic_data() {
    [ $APNIC_LOADED -eq 1 ] && return
    
    URL_APNIC="https://stats.labs.apnic.net/ipv6/AS${ASN}?c=${COUNTRY}&p=1&v=1&w=30&x=1"
    LINHA_HTML=$(curl -s -k -L -m 10 -H "User-Agent: Mozilla/5.0" "$URL_APNIC" | grep "/AS${ASN}" | head -n 1)

    if [ -n "$LINHA_HTML" ]; then
        CAPABLE=$(echo "$LINHA_HTML" | awk -F '{v: ' '{print $2}' | cut -d',' -f1 | tr -d ' ')
        PREFERRED=$(echo "$LINHA_HTML" | awk -F '{v: ' '{print $3}' | cut -d',' -f1 | tr -d ' ')
        ASNAME=$(echo "$LINHA_HTML" | awk -F "\",\"AS${ASN} - " '{print $2}' | cut -d'"' -f1)
    fi

    [ -z "$ASNAME" ] && ASNAME="Unknown"
    [ -z "$CAPABLE" ] && CAPABLE="0.00"
    [ -z "$PREFERRED" ] && PREFERRED="0.00"
    
    APNIC_LOADED=1
}

get_qrator_data() {
    HTML_QRATOR=$(curl -s -k -L -m 10 -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)" "https://radar.qrator.net/as/${ASN}")

    RESULT=$(python3 -c "
import re

html = '''$HTML_QRATOR'''
v4 = re.search(r'(\d[\d\s]*)(?:st|nd|rd|th)?\s+place in IPv4 score rating', html, re.IGNORECASE)
v6 = re.search(r'(\d[\d\s]*)(?:st|nd|rd|th)?\s+place in IPv6 score rating', html, re.IGNORECASE)

val_v4 = v4.group(1).replace(' ', '').strip() if v4 else ''
val_v6 = v6.group(1).replace(' ', '').strip() if v6 else ''

if val_v4 and val_v6:
    print(f'{val_v4}|{val_v6}')
else:
    print('FAIL')
" 2>/dev/null)

    if [ -n "$RESULT" ] && [ "$RESULT" != "FAIL" ]; then
        echo "$RESULT"
        return
    fi

    # Caminho unificado /opt/qrator
    VENV=""
    if [ -d "/opt/qrator/venv" ]; then
        VENV="/opt/qrator/venv"
        export PLAYWRIGHT_BROWSERS_PATH="/opt/qrator/browser_cache"
    else
        VENV="/tmp/qradar_env"
        export PLAYWRIGHT_BROWSERS_PATH="/tmp/qradar_browser_cache"
        if [ ! -d "$VENV" ]; then
            python3 -m venv "$VENV" >/dev/null 2>&1
        fi
        "$VENV/bin/pip" show playwright >/dev/null 2>&1 || "$VENV/bin/pip" install -q playwright >/dev/null 2>&1
        "$VENV/bin/python3" -m playwright install chromium >/dev/null 2>&1
    fi

    PY_EXEC="$VENV/bin/python3"

    "$PY_EXEC" -c "
from playwright.sync_api import sync_playwright
import re

as_num = '$ASN'

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = browser.new_page()
        page.goto(f'https://radar.qrator.net/as/{as_num}', wait_until='domcontentloaded', timeout=25000)
        
        try:
            page.wait_for_function('() => /place in/i.test(document.body.innerText)', timeout=15000)
        except Exception:
            page.wait_for_timeout(3000)

        text = page.evaluate('() => document.body.innerText')
        browser.close()

        v4 = re.search(r'(\d[\d\s]*)(?:st|nd|rd|th)?\s+place in IPv4 score rating', text, re.IGNORECASE)
        v6 = re.search(r'(\d[\d\s]*)(?:st|nd|rd|th)?\s+place in IPv6 score rating', text, re.IGNORECASE)

        val_v4 = v4.group(1).replace(' ', '').strip() if v4 else '0'
        val_v6 = v6.group(1).replace(' ', '').strip() if v6 else '0'

        print(f'{val_v4}|{val_v6}')
except Exception:
    print('0|0')
" 2>/dev/null
}

case "$METRIC" in
    "asnum")
        echo "$ASN"
        ;;
    "asname")
        get_apnic_data
        echo "$ASNAME"
        ;;
    "capable")
        get_apnic_data
        echo "$CAPABLE"
        ;;
    "preferred")
        get_apnic_data
        echo "$PREFERRED"
        ;;
    "qrator_v4")
        QRATOR_RAW=$(get_qrator_data)
        echo "$QRATOR_RAW" | cut -d'|' -f1
        ;;
    "qrator_v6")
        QRATOR_RAW=$(get_qrator_data)
        echo "$QRATOR_RAW" | cut -d'|' -f2
        ;;
    "all")
        get_apnic_data
        QRATOR_RAW=$(get_qrator_data)
        QRATOR_V4=$(echo "$QRATOR_RAW" | cut -d'|' -f1)
        QRATOR_V6=$(echo "$QRATOR_RAW" | cut -d'|' -f2)

        [ -z "$QRATOR_V4" ] && QRATOR_V4="0"
        [ -z "$QRATOR_V6" ] && QRATOR_V6="0"

        echo "{\"asn\": \"$ASN\", \"asname\": \"$ASNAME\", \"country\": \"$COUNTRY\", \"capable\": \"$CAPABLE\", \"preferred\": \"$PREFERRED\", \"qrator_v4\": \"$QRATOR_V4\", \"qrator_v6\": \"$QRATOR_V6\"}"
        ;;
    *)
        echo "0.00"
        ;;
esac
