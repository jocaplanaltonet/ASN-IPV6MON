import requests
import json

# --- CONFIGURAÇÕES DA INSTÂNCIA WPPCONNECT ---
SESSION = "SUA_SESSAO"
URL = f"http://127.0.0.1:21465/api/{SESSION}/list-chats"
TOKEN = "SEU_TOKEN_AQUI"
# ---------------------------------------------

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "onlyGroups": True
}

try:
    r = requests.post(URL, json=payload, headers=headers)
    
    if r.status_code in [200, 201]:
        dados = r.json()
        
        # Se a API encapsular a lista em uma chave "response", desempacota
        if isinstance(dados, dict) and "response" in dados:
            dados = dados["response"]
            
        if isinstance(dados, list):
            print(f"{'NOME DO GRUPO':<35} | {'ID (JID)':<35}")
            print("-" * 75)
            for chat in dados:
                # Tenta buscar o nome do grupo em múltiplos nós possíveis
                nome = chat.get('name') or chat.get('formattedTitle')
                
                if not nome and chat.get('contact'):
                    nome = chat.get('contact').get('name') or chat.get('contact').get('pushname')
                
                if not nome:
                    nome = "Sem Nome"

                # Extrai o ID único (JID) do grupo
                jid = chat.get('id')
                if isinstance(jid, dict):
                    jid = jid.get('_serialized')
                
                print(f"{str(nome)[:34]:<35} | {str(jid):<35}")
        else:
            print("⚠️ A resposta da API não veio no formato de lista esperado.")
    else:
        print(f"❌ Erro na API ({r.status_code}): {r.text}")

except Exception as e:
    print(f"❌ Falha de conexão ou processamento: {e}")
