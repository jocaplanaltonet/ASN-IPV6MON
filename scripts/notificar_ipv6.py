#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import requests
import sys
import subprocess

# Configurações de Caminho (Usa o novo asn_metrics.sh com fallback para ipv6.sh)
SCRIPT_PATH = "/usr/lib/zabbix/externalscripts/asn_metrics.sh"
if not os.path.exists(SCRIPT_PATH):
    SCRIPT_PATH = "/usr/lib/zabbix/externalscripts/ipv6.sh"

# Configurações da API WhatsApp (Ajuste com as credenciais do seu servidor WPPConnect)
WPP_URL = "http://127.0.0.1:21465/api/SUA_SESSAO/send-mentioned"
TOKEN = "SEU_TOKEN_AQUI"
TARGET_GROUP = "ID_DO_GRUPO@g.us"
NUMEROS_PARA_MENCIONAR = ["558187654321"]


def get_status_emoji_percent(hoje: float, ontem: float) -> str:
    """Compara métricas percentuais (Capacidade e Preferência: Maior é melhor)."""
    if hoje > ontem:
        return "📈 *Subiu*"
    elif hoje < ontem:
        return "📉 *Baixou*"
    else:
        return "↔️ *Manteve*"


def get_status_emoji_ranking(hoje: int, ontem: int) -> str:
    """
    Compara posições de ranking no Qrator (Menor é melhor, ex: 100º é melhor que 200º).
    """
    if ontem == 0 or hoje == 0:
        return "↔️ *Sem alteração*"
    if hoje < ontem:
        return "📈 *Melhorou* (subiu no ranking)"
    elif hoje > ontem:
        return "📉 *Caiu* (desceu no ranking)"
    else:
        return "↔️ *Manteve*"


def main():
    # 1. VALIDAÇÃO DO ARGUMENTO ASN NO TERMINAL
    if len(sys.argv) < 2:
        print("❌ Erro: O número do ASN é obrigatório como argumento!")
        print("Uso correto: python3 notificar_ipv6.py <ASN>")
        print("Exemplo:     python3 notificar_ipv6.py 52913")
        sys.exit(1)

    asn = sys.argv[1].strip()

    # Mapeia o arquivo de histórico dinamicamente por Usuário Linux (UID) para evitar erros de permissão no /tmp
    try:
        user_uid = os.getuid()
    except AttributeError:
        user_uid = "default"

    historico_file = f"/tmp/historico_ipv6_{asn}_{user_uid}.json"

    # 2. EXECUTA O SCRIPT SH E CAPTURA O JSON DO MODO "ALL" EM TEMPO REAL
    try:
        resultado = subprocess.run(
            [SCRIPT_PATH, asn, "all"],
            capture_output=True,
            text=True,
            check=True
        )
        dados_atuais = json.loads(resultado.stdout.strip())
    except Exception as e:
        print(f"❌ Erro ao executar o script bash em {SCRIPT_PATH} para o ASN {asn}: {e}")
        sys.exit(1)

    # Extrai as métricas retornadas
    asname = dados_atuais.get("asname", "Unknown")
    cap_hoje = round(float(dados_atuais.get("capable", 0)), 2)
    pref_hoje = round(float(dados_atuais.get("preferred", 0)), 2)
    qv4_hoje = int(dados_atuais.get("qrator_v4", 0))
    qv6_hoje = int(dados_atuais.get("qrator_v6", 0))

    # 3. LEITURA DO HISTÓRICO REAL COM FALLBACK SEGURO PARA O PRÓPRIO DIA
    if os.path.exists(historico_file):
        try:
            with open(historico_file, 'r', encoding='utf-8') as f:
                hist = json.load(f)
        except Exception:
            hist = {"cap": cap_hoje, "pref": pref_hoje, "qv4": qv4_hoje, "qv6": qv6_hoje}
    else:
        hist = {"cap": cap_hoje, "pref": pref_hoje, "qv4": qv4_hoje, "qv6": qv6_hoje}

    cap_ontem = hist.get("cap", cap_hoje)
    pref_ontem = hist.get("pref", pref_hoje)
    qv4_ontem = hist.get("qv4", qv4_hoje)
    qv6_ontem = hist.get("qv6", qv6_hoje)

    # 4. COMPARAÇÕES E FORMATAÇÃO DA MENSAGEM
    status_cap = get_status_emoji_percent(cap_hoje, cap_ontem)
    status_pref = get_status_emoji_percent(pref_hoje, pref_ontem)
    status_qv4 = get_status_emoji_ranking(qv4_hoje, qv4_ontem)
    status_qv6 = get_status_emoji_ranking(qv6_hoje, qv6_ontem)

    mensagem = (
        f"📊 *RELATÓRIO DIÁRIO RESILIÊNCIA & IPv6 - AS{asn}*\n"
        f"🏢 *Provedor:* {asname}\n\n"
        f"🌐 *Capacidade IPv6:* {cap_hoje}%\n"
        f"   Status: {status_cap} (ontem: {cap_ontem}%)\n\n"
        f"⭐ *Preferência IPv6:* {pref_hoje}%\n"
        f"   Status: {status_pref} (ontem: {pref_ontem}%)\n\n"
        f"🛡️ *Ranking Qrator IPv4:* {qv4_hoje}º lugar\n"
        f"   Status: {status_qv4} (ontem: {qv4_ontem}º)\n\n"
        f"🛡️ *Ranking Qrator IPv6:* {qv6_hoje}º lugar\n"
        f"   Status: {status_qv6} (ontem: {qv6_ontem}º)\n\n"
        f"🕒 _Dados atualizados via APNIC Labs & Qrator Radar_"
    )

    # 5. TRATAMENTO DINÂMICO DE MENÇÕES E MONTAGEM DO PAYLOAD
    payload = {
        "phone": TARGET_GROUP,
        "isGroup": True
    }

    mencionados_validos = [str(num).strip() for num in NUMEROS_PARA_MENCIONAR if num and str(num).strip()]

    if mencionados_validos:
        tags_texto = " ".join([f"@{num}" for num in mencionados_validos])
        payload["message"] = f"{mensagem}\n\n🔔 CC: {tags_texto}"
        payload["mentioned"] = mencionados_validos
    else:
        payload["message"] = mensagem

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json; charset=utf-8"
    }

    # 6. ENVIO PARA A API E SALVAMENTO DO NOVO HISTÓRICO
    try:
        response = requests.post(WPP_URL, json=payload, headers=headers, timeout=15)

        if response.status_code in [200, 201]:
            print(f"✅ Relatório do ASN {asn} enviado com sucesso para o grupo {TARGET_GROUP}")

            # Atualiza o arquivo de histórico para ser usado na comparação de amanhã
            with open(historico_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "cap": cap_hoje,
                    "pref": pref_hoje,
                    "qv4": qv4_hoje,
                    "qv6": qv6_hoje
                }, f)

            os.chmod(historico_file, 0o666)
        else:
            print(f"❌ Erro na API do WhatsApp: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Erro ao enviar a requisição HTTP para a API WPPConnect: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
