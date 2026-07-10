#!/usr/bin/env python3
# ==============================================================================
# Script: notificar_ipv6.py
# Descrição: Chama o ipv6.sh em tempo real, compara os dados com o histórico
#            do dia anterior e envia o relatório para o WhatsApp via WPPConnect.
# ==============================================================================

import json
import os
import requests
import sys
import subprocess

# Configurações do ASN e Caminhos do Zabbix
ASN = "52913"
SCRIPT_PATH = "/usr/lib/zabbix/externalscripts/ipv6.sh"

# Configurações da API WhatsApp (Seus dados reais de Produção)
```
WPP_URL = "http://127.0.0.1:21465/api/SUA_SESSAO/send-mentioned"
TOKEN = "SEU_TOKEN_AQUI"
TARGET_GROUP = "ID_DO_GRUPO@g.us"
NUMEROS_PARA_MENCIONAR = ["558187654321"]
```
# Resolve conflito de permissão no /tmp mapeando o histórico pelo ID do usuário Linux atual (UID)
try:
    user_uid = os.getuid()
except AttributeError:
    user_uid = "default"

HISTORICO_FILE = f"/tmp/historico_ipv6_{ASN}_{user_uid}.json"

def get_status_emoji(hoje, ontem):
    if hoje > ontem:
        return "📈 *Subiu*"
    elif hoje < ontem:
        return "📉 *Baixou*"
    else:
        return "↔️ *Manteve*"

def main():
    # 1. EXECUTA O SCRIPT SH E CAPTURA O JSON DO MODO "ALL" EM TEMPO REAL
    try:
        resultado = subprocess.run(
            [SCRIPT_PATH, ASN, "all"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        dados_atuais = json.loads(resultado.stdout.strip())
    except Exception as e:
        print(f"❌ Erro ao executar o script bash em {SCRIPT_PATH}: {e}")
        sys.exit(1)

    # Coleta as variáveis extraídas do bash
    asname = dados_atuais.get("asname", "Unknown")
    cap_hoje = round(float(dados_atuais.get("capable", 0)), 2)
    pref_hoje = round(float(dados_atuais.get("preferred", 0)), 2)

    # 2. LEITURA DO HISTÓRICO REAL COM FALLBACK SEGURO PARA O PROPRIO DIA
    if os.path.exists(HISTORICO_FILE):
        try:
            with open(HISTORICO_FILE, 'r', encoding='utf-8') as f:
                hist = json.load(f)
        except Exception:
            hist = {"cap": cap_hoje, "pref": pref_hoje}
    else:
        hist = {"cap": cap_hoje, "pref": pref_hoje}

    cap_ontem = hist.get("cap", cap_hoje)
    pref_ontem = hist.get("pref", pref_hoje)

    status_cap = get_status_emoji(cap_hoje, cap_ontem)
    status_pref = get_status_emoji(pref_hoje, pref_ontem)

    # 3. FORMATAÇÃO DA MENSAGEM DO RELATÓRIO DO WHATSAPP
    mensagem = (
        f"📊 *RELATÓRIO DIÁRIO IPv6 - AS{ASN}*\n"
        f"🏢 *Provedor:* {asname}\n\n"
        f"✅ *Capacidade:* {cap_hoje}%\n"
        f"   Status: {status_cap} (ontem: {cap_ontem}%)\n\n"
        f"⭐ *Preferência:* {pref_hoje}%\n"
        f"   Status: {status_pref} (ontem: {pref_ontem}%)\n\n"
        f"🕒 _Dados atualizados em tempo real via APNIC Labs_"
    )

    # 4. TRATAMENTO DINÂMICO DE MENÇÕES (Evita erros se a lista estiver vazia)
    payload = {
        "phone": TARGET_GROUP,
        "isGroup": True
    }

    # Filtra apenas números válidos na lista (remove strings vazias ou nulas)
    mencionados_validos = [str(num).strip() for num in NUMEROS_PARA_MENCIONAR if num and str(num).strip()]

    if mencionados_validos:
        # Se houver números, cria a tag @ no texto e adiciona ao payload
        tags_texto = " ".join([f"@{num}" for num in mencionados_validos])
        payload["message"] = f"{mensagem}\n\n🔔 CC: {tags_texto}"
        payload["mentioned"] = mencionados_validos
    else:
        # Se não houver números cadastrados, envia a mensagem limpa sem mencionar ninguém
        payload["message"] = mensagem

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json; charset=utf-8"
    }

    try:
        response = requests.post(WPP_URL, json=payload, headers=headers, timeout=15)
        
        if response.status_code in [200, 201]:
            print(f"✅ Relatório enviado com sucesso para o grupo {TARGET_GROUP}")
            
            # Salva os dados atuais reais que virarão o histórico oficial de amanhã
            with open(HISTORICO_FILE, 'w', encoding='utf-8') as f:
                json.dump({"cap": cap_hoje, "pref": pref_hoje}, f)
            
            # Libera permissão total de leitura/escrita no ficheiro do /tmp
            os.chmod(HISTORICO_FILE, 0o666)
        else:
            print(f"❌ Erro na API do WhatsApp: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Erro ao processar arquivo ou requisição: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
