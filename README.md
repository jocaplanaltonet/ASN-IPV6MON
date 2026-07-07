# ASN-IPV6MON V1 📊🌐

Este projeto automatiza a coleta, o monitoramento temporal e a notificação de métricas de transição IPv6 (Capacidade e Preferência) para Sistemas Autônomos (ASN), utilizando dados oficiais consolidados do **APNIC Labs** .

A solução conta com monitoramento nativo via **Zabbix (External Check)**, dashboards analíticos no **Grafana** e alertas diários com comparativo de variação percentual enviados para o **WhatsApp**.

---

## 🛑 Pré-requisitos & Dependências Globais

Para que todo o ecossistema funcione (especialmente os alertas diários e os gráficos), a sua infraestrutura precisa contar com:

1. **WPPConnect-Server Ativo:** É obrigatório ter o servidor do WPPConnect rodando (localmente ou em VPS) para intermediar o envio das mensagens e marcações no WhatsApp.
   * 🔗 **Repositório Oficial:** https://github.com/wppconnect-team/wppconnect-server
2. **Sessão Iniciada:** Uma sessão válida e conectada via QR Code no WPPConnect-Server para disparar os alertas.
3. **Zabbix Server 7.4+** com o plugin `alexanderzobnin-zabbix-datasource` ativo e configurado no Grafana.

---

## 📂 Estrutura do Repositório
```
├── README.md
├── scripts/
│   ├── update_apnic_cache.sh   # Download e renovação do cache local do APNIC (3.5MB)
│   ├── ipv6.py                 # Parser inteligente para integração com terminais e Zabbix
│   └── notificar_ipv6.py       # Gerador de relatórios diários e bot de envio para o WhatsApp
├── extra/
│   └── get_groups.py          # Script auxiliar para capturar o ID (JID) dos grupos do WhatsApp
├── templates/
│   └── ASN-IPV6MON.yaml        # Template pronto para importação no Zabbix 7.4+
└── grafana/
    └── dashboard_apnic.json    # Código JSON declarativo do painel para o Grafana v13+
```

---

## 🛠️ 1. Configuração dos Scripts no Servidor

### Passo 1: Instalar dependências do sistema e do Python
Certifique-se de instalar os pacotes globais do Linux. Caso use ambientes virtuais (`venv`), lembre-se de instalar a biblioteca `requests` dentro dele:

``
sudo apt update
sudo apt install curl whois python3-requests -y
``

# Se utilizar ambiente virtual do Python, execute:
``
pip install requests
``
### Passo 2: Organizar os scripts e aplicar permissions
O script `ipv6.py` precisa ficar na pasta de checagens externas do Zabbix Server. Os demais podem ficar em uma pasta de sua preferência (ex: `/home/usuario/ASN-IPV6MON/scripts/`).
```
chmod +x scripts/update_apnic_cache.sh
chmod +x scripts/notificar_ipv6.py
chmod +x extra/get_groups.py

sudo cp scripts/ipv6.py /usr/lib/zabbix/externalscripts/
sudo chmod +x /usr/lib/zabbix/externalscripts/ipv6.py
sudo chown zabbix:zabbix /usr/lib/zabbix/externalscripts/ipv6.py
```

### Passo 3: Configurar a Automação do Agendamento (Cron)
Configure o agendamento de acordo com o seu interpretador de Cron:
O padrão do Linux utiliza 5 campos de tempo (Minuto Hora Dia Mês Semana):
``
15 03 * * * /usr/lib/zabbix/externalscripts/update_apnic_cache.sh SENASN
30 03 * * * /usr/bin/python3 /path-to-script/notificar_ipv6.py
``
💡 Nota sobre permissões: O script gerencia de forma transparente as permissões do cache gravado em /tmp (0o666), assegurando que tanto o usuário zabbix quanto o usuário local do cron leiam e escrevam nos arquivos sem travar por falta de privilégio.

---

## 📐 2. Integração com o Zabbix

1. Acesse o painel do seu Zabbix Server.
2. Vá em Data collection -> Templates -> Import e selecione o arquivo templates/ASN-IPV6MON.yaml.
3. Associe o template ao Host desejado.
4. Vá na aba Macros do Host (ou do Template) e configure a macro {$ASN_NUM} com o número do seu ASN (ex: 52913).

O Zabbix passará a coletar automaticamente de forma modular:
* asname: O nome fantasia oficial limpo da organização via API HackerTarget.
* capable: Porcentagem de capacidade IPv6 (Média móvel de 30 dias).
* preferred: Porcentagem de preferência de uso IPv6 (Média móvel de 30 dias).

---

## 📉 3. Importação do Dashboard no Grafana

1. No menu lateral do Grafana, clique em Dashboards -> New -> Import.
2. Cole o conteúdo do arquivo grafana/dashboard_apnic.json ou clique em Upload JSON file.
3. Na janela de importação, selecione o seu Data Source do Zabbix correspondente.
4. Clique em Import.

⚠️ Ajuste das Variáveis de Topo (Obrigatório)
* Host no Zabbix ($VISIBLE_NAME): Altere essa variável de texto para o Nome Visível (Visible hostname) exato do host que você cadastrou dentro do seu Zabbix (Exemplo: IPV6MON-52913).
* Número do ASN ($ASN_NUM): Campo preenchido automaticamente, extraindo a informação da macro direto do host selecionado acima.
* Nome do Provedor ($ASN_NOME): Exibe automaticamente o nome fantasia limpo da empresa (Exemplo: PLANALTO NET).

---

## 💬 4. Configuração das Notificações do WhatsApp

Abra o arquivo scripts/notificar_ipv6.py e insira as chaves de acesso correspondentes à sua sessão do WPPConnect-Server:

```
WPP_URL = "http://127.0.0.1:21465/api/SUA_SESSAO/send-mentioned"
TOKEN = "SEU_TOKEN_AQUI"
TARGET_GROUP = "ID_DO_GRUPO@g.us"
NUMEROS_PARA_MENCIONAR = ["558187654321"]
```
💡 Nota técnica: O script de envio faz o uso correto do parâmetro mentioned nativo da API para que os administradores listados recebam o ping sonoro do alerta no grupo.

---

## 🔍 5. Como descobrir o ID (JID) do seu Grupo do WhatsApp

Se você não souber o identificador único (@g.us) do grupo onde deseja receber os alertas diários, configure os parâmetros no arquivo extra/get_groups.py e execute:
``
python3 extra/get_groups.py
``
O script vai retornar uma tabela limpa no terminal estruturada desta forma:

NOME DO GRUPO                       | ID (JID)
---------------------------------------------------------------------------
Grupo de Alertas - Provedor         | 120363318283910280@g.us

---
