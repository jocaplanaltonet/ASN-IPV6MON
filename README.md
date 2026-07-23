# ASN-IPV6MON & Qrator Radar V3 📊🌐

Este projeto automatiza a coleta, o monitoramento temporal e a notificação de métricas de transição IPv6 (Capacidade e Preferência) e resiliência de roteamento BGP (**Rankings IPv4 e IPv6 do Qrator Radar**) para Sistemas Autônomos (ASN).

A solução conta com monitoramento nativo via **Zabbix (External Check)** usando um script leve em Bash/Python, dashboards analíticos no **Grafana** e relatórios diários inteligentes com alertas comparativos enviados para o **WhatsApp** via **WPPConnect**.

## 🛑 Pré-requisitos & Dependências Globais

Para que todo o ecossistema funcione (especialmente os alertas diários e os gráficos):

1. **WPPConnect-Server Ativo:** É obrigatório ter o servidor do WPPConnect rodando (localmente ou em VPS) para intermediar o envio das mensagens e marcações no WhatsApp.
   * 🔗 **Repositório Oficial:** https://github.com/wppconnect-team/wppconnect-server

2. **Sessão Iniciada:** Uma sessão válida e conectada via QR Code no WPPConnect-Server para disparar os alertas.

3. **Zabbix Server 7.0+** com o plugin `alexanderzobnin-zabbix-datasource` ativo e configurado no Grafana.

4. **Python 3 com Venv & Playwright:** Utilizado para consultar o Qrator Radar sem bloquear a execução do Zabbix.

## 📁 Estrutura do Repositório e Ambiente Global (`/opt/qrator/`)

Para garantir que a biblioteca Playwright e o navegador Chromium fiquem isolados, com alta performance (execução em 1~2s) e acesso garantido para qualquer usuário (incluindo o usuário `zabbix`), o projeto centraliza seu ambiente em `/opt/qrator/`:

```
/opt/qrator/
├── venv/            # Ambiente virtual Python isolado
└── browser_cache/   # Cache e binários do Chromium (Playwright)
```

## 📂 Estrutura de Arquivos do Repositório

```
ASN-IPV6MON
├── extra
│   └── get_groups.py           # Script auxiliar para capturar o ID (JID) dos grupos do WhatsApp
├── grafana
│   └── ASN-IPV6MONv3.json      # Código JSON do painel para o Grafana v13+
├── README.md                   # Este manual de instruções
├── scripts
│   ├── asn_metrics.sh          # Script Bash integrado ao Zabbix External Check (tempo real)
│   ├── notificar_ipv6.py       # Consome asn_metrics.sh, gerencia histórico e envia alertas no WhatsApp
│   └── radarsetup.sh           # Script de setup para criar e preparar /opt/qrator/
└── templates
    └── ASN-IPV6MONv3.yaml      # Template atualizado para importação no Zabbix
```

## 🛠️ 1. Instalação do Ambiente Global (`scripts/radarsetup.sh`)

Execute o script de instalação uma única vez como `root` ou `sudo` no servidor Zabbix para preparar o diretório `/opt/qrator/`:

```bash
chmod +x scripts/radarsetup.sh
sudo ./scripts/radarsetup.sh
```

Conteúdo de referência do `scripts/radarsetup.sh`:

```bash
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
```

## ⚙️ 2. Configuração do Script Principal (`asn_metrics.sh`)

Copie o script `asn_metrics.sh` para o diretório de scripts externos do Zabbix (`/usr/lib/zabbix/externalscripts/`):

```bash
sudo cp scripts/asn_metrics.sh /usr/lib/zabbix/externalscripts/
sudo chmod +x /usr/lib/zabbix/externalscripts/asn_metrics.sh
sudo chown zabbix:zabbix /usr/lib/zabbix/externalscripts/asn_metrics.sh
```

### Sintaxe de Teste via Terminal:

`asn_metrics.sh <NÚMERO_DO_ASN> <MÉTRICA>`

```bash
# Consultar nome do ASN
/usr/lib/zabbix/externalscripts/asn_metrics.sh 52913 asname

# Consultar numero do ASN
/usr/lib/zabbix/externalscripts/asn_metrics.sh 52913 asnum

# Consultar posição no Ranking Qrator IPv4
/usr/lib/zabbix/externalscripts/asn_metrics.sh 52913 qrator_v4

# Consultar posição no Ranking Qrator IPv6
/usr/lib/zabbix/externalscripts/asn_metrics.sh 52913 qrator_v6

# Consultar capacidade IPv6 (%)
/usr/lib/zabbix/externalscripts/asn_metrics.sh 52913 capable

# Consultar preferência IPv6 (%)
/usr/lib/zabbix/externalscripts/asn_metrics.sh 52913 preferred

# Retornar JSON completo
/usr/lib/zabbix/externalscripts/asn_metrics.sh 52913 all
```

## 📐 3. Configuração dos Itens no Zabbix

1. Acesse o painel web do seu Zabbix Server.
2. Vá em **Data collection** -> **Templates** -> **Import** e selecione o arquivo `templates/ASN-IPV6MONv3.yaml`.
3. Associe o template ao Host de monitoramento desejado.
4. **Configuração Obrigatória da Macro:** Na aba **Macros** do Host ou Template, configure:
   * **Macro:** `{$ASN_NUM}`
   * **Valor:** `52913` (ou o ASN da sua rede)

### Tabela de Itens Padronizados:

| Nome do Item | Tipo | Chave (Key) | Unidade | Intervalo |
| :--- | :--- | :--- | :--- | :--- |
| 🆔 **Número do ASN: {$ASN_NUM}** | External Check | `asn_metrics.sh["{$ASN_NUM}","asnum"]` | - | 1d |
| 🏢 **Provedor: AS{$ASN_NUM}** | External Check | `asn_metrics.sh["{$ASN_NUM}","asname"]` | - | 1d |
| 🌐 **Capacidade IPv6: AS{$ASN_NUM}** | External Check | `asn_metrics.sh["{$ASN_NUM}","capable"]` | % | 1h |
| 🚀 **Preferência IPv6: AS{$ASN_NUM}** | External Check | `asn_metrics.sh["{$ASN_NUM}","preferred"]` | % | 1h |
| 🛡️ **Ranking Qrator IPv4: AS{$ASN_NUM}** | External Check | `asn_metrics.sh["{$ASN_NUM}","qrator_v4"]` | º | 6h |
| 🛡️ **Ranking Qrator IPv6: AS{$ASN_NUM}** | External Check | `asn_metrics.sh["{$ASN_NUM}","qrator_v6"]` | º | 6h |

## 💬 4. Notificações Diárias no WhatsApp (`notificar_ipv6.py`)

O script `notificar_ipv6.py` executa o `asn_metrics.sh <ASN> all`, compara os valores com o arquivo de histórico mantido em `/tmp/historico_ipv6_{ASN}_{UID}.json` e envia o relatório formatado para o seu grupo de WhatsApp.

### Configuração no script:

Edite as credenciais no início de `scripts/notificar_ipv6.py`:

```python
WPP_URL = "http://127.0.0.1:21465/api/SUA_SESSAO/send-mentioned"
TOKEN = "SEU_TOKEN_AQUI"
TARGET_GROUP = "ID_DO_GRUPO@g.us"
NUMEROS_PARA_MENCIONAR = ["558187654321"]
```

### Agendamento no Cron:

Configure a chamada diária no `crontab -e`:

```bash
30 08 * * * /usr/bin/python3 /usr/lib/zabbix/externalscripts/notificar_ipv6.py 52913
```

## 🔍 5. Descobrir o ID (JID) do Grupo no WhatsApp

Execute o script utilitário para listar os IDs de todos os grupos ativos na sua sessão do WPPConnect:

```bash
python3 extra/get_groups.py
```

Saída no terminal:

```
NOME DO GRUPO                         | ID (JID)
---------------------------------------------------------------------------
Grupo de Alertas - Provedor          | 558194669193-1234567890@g.us
```

## 📉 6. Importação do Dashboard no Grafana

1. No menu lateral do Grafana, clique em **Dashboards** -> **New** -> **Import**.
2. Cole o conteúdo do arquivo `grafana/ASN-IPV6MONv2.json` ou faça upload do arquivo JSON.
3. Selecione o seu Data Source do Zabbix correspondente.
4. Ajuste as variáveis no topo do painel:
   * **`$VISIBLE_NAME`**: Nome do Host cadastrado no Zabbix.
   * **`$ASN_NUM`**: Número do ASN monitorado.

## 📜 Histórico de Alterações (Changelog)

### v2.0 - Consolidação de Métricas e Unificação de Diretórios

* **Novo Nome do Script (`asn_metrics.sh`)**: Atualizado a partir de `ipv6.sh` para refletir a adição das métricas de resiliência BGP.
* **Ambiente Isolado `/opt/qrator/`**:
  * Unificação do ambiente virtual Python (`/opt/qrator/venv`) e do cache Chromium (`/opt/qrator/browser_cache`).
  * Inclusão do script de automação `scripts/radarsetup.sh`.
* **Métricas do Qrator Radar no WhatsApp**:
  * Inclusão dos dados dos rankings IPv4 e IPv6 no relatório diário.
  * Comparativo dinâmico de tendência (interpretação invertida para rankings: posição menor = melhoria 📈).
* **Otimizações de Desempenho**:
  * Implementação de *Lazy Loading* em `asn_metrics.sh` (requisições isoladas só consultam a fonte correspondente).
  * Tratamento de ordinais em inglês para ranking (`1st`, `2nd`, `3rd`, `4th`).

## 🔗 Fontes dos Dados

* **APNIC Labs (Métricas IPv6):** https://stats.labs.apnic.net/ipv6
* **Qrator Radar (Resiliência BGP):** https://radar.qrator.net/
