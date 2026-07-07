#!/usr/bin/env python3
import sys
import json
import os
import subprocess

def buscar_nome_api(asn):
    """Busca o nome fantasia limpo da organização usando a API do HackerTarget"""
    try:
        url = f"https://api.hackertarget.com/aslookup/?q={asn}&output=json&details=true"
        resultado = subprocess.run(
            ["curl", "-s", url], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        
        if resultado.returncode == 0:
            api_data = json.loads(resultado.stdout)
            nome_org = api_data.get("organization")
            if nome_org:
                return str(nome_org).strip()
    except Exception:
        pass
    return f"AS{asn}"

def main():
    if len(sys.argv) < 3:
        sys.exit(1)

    asn = sys.argv[1]
    metrica = sys.argv[2].lower().strip()
    cache_path = f"/tmp/apnic_{asn}.json"

    # 1. TRATAMENTO DO ARGUMENTO ASNUM
    if metrica == "asnum":
        print(asn)
        return

    # 2. BUSCA O NOME DA ORGANIZAÇÃO
    nome_as = f"AS{asn}"
    if metrica in ["asname", "all"]:
        nome_as = buscar_nome_api(asn)

    if metrica == "asname":
        print(nome_as)
        return

    # 3. TRATAMENTO VIA CACHE LOCAL DO APNIC
    if not os.path.exists(cache_path):
        sys.exit(1)

    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        cap_hoje = 0.00
        pref_hoje = 0.00
        
        if 'data' in data and len(data['data']) > 0:
            ultimo_registro = data['data'][-1]
            if "30" in ultimo_registro:
                cap_hoje = round(float(ultimo_registro["30"].get("capable_pc", 0)), 2)
                pref_hoje = round(float(ultimo_registro["30"].get("preferred_pc", 0)), 2)

        # 4. PROCESSAMENTO FINAL COM DESIGN BONITO PARA O 'ALL'
        if metrica == "all":
            print("┌" + "─"*61 + "┐")
            print(f"│ 📊 METRICAS IPv6 - AS{asn:<38} │")
            print("├" + "─"*61 + "┤")
            print(f"│ 🏢 Organização  : {nome_as:<41} │")
            print(f"│ ✅ Capaz (Cap)  : {f'{cap_hoje:.2f}%':<41} │")
            print(f"│ ⭐ Preferido    : {f'{pref_hoje:.2f}%':<41} │")
            print("└" + "─"*61 + "┘")
            
        elif metrica == "capable":
            print(f"{cap_hoje:.2f}")
            
        elif metrica == "preferred":
            print(f"{pref_hoje:.2f}")
            
        else:
            print(f"AS{asn}")

    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    main()
