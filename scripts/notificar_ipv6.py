#!/usr/bin/env python3
# ==============================================================================
# Script: notificar_ipv6.py
# Descrição: Lê o cache local do APNIC gerado pelo .sh, compara os dados
#            com o histórico do dia anterior e envia um relatório para o WhatsApp.
# ==============================================================================

import json
import os
import requests
import sys

# ==============================================================================
# CONFIGURAÇÕES DO UTILIZADOR (ALTERE COM OS SEUS DADOS PARA PRODUÇÃO)
# ==============================================================================
ASN = "52913"

# Configurações da API do WPPConnect-Server
WPP_URL = "http://127.0.0.1:21465/api/SUA_SESSAO/send-mentioned"
TOKEN = "SEU_TOKEN_WPPCONNECT_AQUI"

# --- CONFIGURAÇÕES DE DESTINO ---
TARGET_GROUP = "SEU_ID_DE_GRUPO@g.us"          # ID do grupo do WhatsApp
NUMEROS_PARA_MENCIONAR = ["5581999999999"]     # Números (sem @c.us) para marcar no grupo
# ==============================================================================

# Caminhos centralizados no /tmp para evitar problemas de permissão de escrita
CACHE_FILE = f"/tmp/apnic_{ASN}.json"
HISTORICO_FILE = f"/tmp/historico_ipv6_{ASN}.json"

def get_status_emoji(hoje, ontem):
    if hoje > ontem:
        return "📈 *Subiu*"
    elif hoje < ontem:
        return "📉 *Baixou*"
    else:
        return "↔️ *Manteve*"

def main():
    # Verifica se o arquivo de cache existe
    if not os.path.exists(CACHE_FILE):
        print(f"❌ Erro: Ficheiro de cache local não encontrado em: {CACHE_FILE}")
        sys.exit(1)

    try:
        # 1. LEITURA DO CACHE (Sincronizado com a lógica do ipv6.py)
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'data' in data and len(data['data']) > 0:
            # Pega o último registro (hoje)
            ultimo_registro = data['data'][-1]
            
            # Pega a média de 30 dias ("30")
            if "30" in ultimo_registro:
                cap_hoje = round(float(ultimo_registro["30"].get("capable_pc", 0)), 2)
                pref_hoje = round(float(ultimo_registro["30"].get("preferred_pc", 0)), 2)
            else:
                print("❌ Erro: Chave '30' não encontrada no último registro do JSON.")
                sys.exit(1)
        else:
            print("❌ Erro: Estrutura 'data' inválida ou vazia no JSON.")
            sys.exit(1)

        # 2. LEITURA DO HISTÓRICO LOCAL DO DIA ANTERIOR (NO /TMP)
        if os.path.exists(HISTORICO_FILE):
            with open(HISTORICO_FILE, 'r', encoding='utf-8') as f:
                hist = json.load(f)
        else:
            # Se for a primeira execução ou pós-reboot, assume os valores de hoje
            hist = {"cap": cap_hoje, "pref": pref_hoje}

        cap_ontem = hist.get("cap", cap_hoje)
        pref_ontem = hist.get("pref", pref_hoje)

        status_cap = get_status_emoji(cap_hoje, cap_ontem)
        status_pref = get_status_emoji(pref_hoje, pref_ontem)

        # 3. FORMATAÇÃO DA MENSAGEM DO RELATÓRIO
        mensagem = (
            f"📊 *RELATÓRIO DIÁRIO IPv6 - AS{ASN}*\n\n"
            f"✅ *Capacidade:* {cap_hoje}%\n"
            f"   Status: {status_cap} (ontem: {cap_ontem}%)\n\n"
            f"⭐ *Preferência:* {pref_hoje}%\n"
            f"   Status: {status_pref} (ontem: {pref_ontem}%)\n\n"
            f"🕒 _Dados extraídos via APNIC Labs Cache_"
        )

        # 4. ENVIO VIA API WPPCONNECT (ENDPOINT 'send-mentioned')
        payload_wpp = {
            "phone": TARGET_GROUP,
            "message": mensagem,
            "isGroup": True,
            "mentioned": NUMEROS_PARA_MENCIONAR
        }
        
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json; charset=utf-8"
        }

        # Realiza o envio do relatório para o grupo do WhatsApp
        response = requests.post(WPP_URL, json=payload_wpp, headers=headers, timeout=15)
        
        if response.status_code in [200, 201]:
            print(f"✅ Relatório diário enviado com sucesso para o grupo {TARGET_GROUP}")
            
            # Salva os dados no /tmp para o histórico de amanhã
            with open(HISTORICO_FILE, 'w', encoding='utf-8') as f:
                json.dump({"cap": cap_hoje, "pref": pref_hoje}, f)
            
            # Altera a permissão para 666 para evitar bloqueios de permissão no /tmp
            os.chmod(HISTORICO_FILE, 0o666)
        else:
            print(f"❌ Erro na API do WhatsApp: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Erro na execução do script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
