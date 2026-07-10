░▒▓    ~  nano cat                                                                                                     ✔  with joca@grafana  at 12:26:47  ▓▒░
░▒▓    ~  cat README.md                                                                                                ✔  with joca@grafana  at 12:26:51  ▓▒░
# ASN-IPV6MON V2 📊🌐
Este projeto automatiza a coleta, o monitoramento temporal e a notificação de métricas de transição IPv6 (Capacidade e Preferência) para Sistemas Autônomos (ASN), utilizando dados oficiais consolidados em tempo real do **APNIC Labs**.

A solução conta com monitoramento nativo via **Zabbix (External Check)** usando um script leve em Bash, dashboards analíticos no **Grafana** e relatórios diários inteligentes enviados com comparativo de variação percentual para o **WhatsApp**.

---

## 🛑 Pré-requisitos & Dependências Globais

Para que todo o ecossistema funcione (especialmente os alertas diários e os gráficos), a sua infraestrutura precisa contar com:

1. **WPPConnect-Server Ativo:** É obrigatório ter o servidor do WPPConnect rodando (localmente ou em VPS) para intermediar o envio das mensagens e marcações no WhatsApp.
   * 🔗 **Repositório Oficial:** https://github.com/wppconnect-team/wppconnect-server
2. **Sessão Iniciada:** Uma sessão válida e conectada via QR Code no WPPConnect-Server para disparar os alertas.
3. **Zabbix Server 7.0+** com o plugin `alexanderzobnin-zabbix-datasource` ativo e configurado no Grafana.

---

## 📂 Estrutura do Repositório
```
ASN-IPV6MON
├── extra
│   └── get_groups.py           # Script auxiliar para capturar o ID (JID) dos grupos do WhatsApp
├── grafana
│   └── ASN-IPV6MONv2.json      # Código JSON do painel para o Grafana v13+
├── README.md                   # Este manual de instruções
├── scripts
│   ├── ipv6.sh                 # Script Bash integrado ao Zabbix External Check (tempo real)
│   └── notificar_ipv6.py       # Consome o ipv6.sh, gerencia o histórico e envia alertas ao WhatsApp
└── templates
    └── ASN-IPV6MONv2.yaml      # Template atualizado para importação no Zabbix
```

---

## 🛠️ 1. Configuração dos Scripts no Servidor

### Passo 1: Instalar dependências do sistema
Certifique-se de instalar os pacotes necessários no Linux para o correto funcionamento dos comandos de manipulação de texto e requisições no Bash (`curl` e `awk`):

```bash
sudo apt update
sudo apt install curl awk -y
```

### Passo 2: Organizar os scripts e aplicar permissões
O script `ipv6.sh` **precisa obrigatoriamente** ficar localizado na pasta de checagens externas do seu Zabbix Server (`externalscripts`). O de notificação pode ficar na pasta de sua preferência.

```bash
# Dar permissão de execução nos scripts locais
chmod +x scripts/notificar_ipv6.py
chmod +x extra/get_groups.py

# Copiar o script Bash para o diretório correto do Zabbix
sudo cp scripts/ipv6.sh /usr/lib/zabbix/externalscripts/
sudo chmod +x /usr/lib/zabbix/externalscripts/ipv6.sh
sudo chown zabbix:zabbix /usr/lib/zabbix/externalscripts/ipv6.sh
```

### Passo 3: Configurar a Automação do Agendamento (Cron)
Como o script aceita o ASN de forma dinâmica por argumento, você deve passar o número do seu ASN desejado no final da chamada de execução:

```bash
30 08 * * * /usr/bin/python3 /path-to-script/notificar_ipv6.py 52913
```

💡 *Nota sobre permissões:* O histórico de comparação de variação é salvo automaticamente na pasta `/tmp` com o sufixo do ID do usuário do Linux que o executou (`/tmp/historico_ipv6_{ASN}_{UID}.json`) com permissão liberada (`0o666`), garantindo que tanto o usuário `zabbix` quanto o usuário do `cron` possam ler e gravar dados sem conflitos de privilégio (`Permission denied`).

---

## 🌐 2. Como Adaptar para Outros Países (Internacionalización)

Por padrão, este ecossistema vem configurado para coletar e monitorar dados de ASNs do **Brasil (BR)**.

Se você precisar monitorar um ASN de outro país, basta abrir o arquivo `/usr/lib/zabbix/externalscripts/ipv6.sh` e alterar o código da região na variável localizada logo no início do código:

```bash
# Altere para a sigla ISO desejada (Ex: AR para Argentina, US para Estados Unidos, PT para Portugal)
COUNTRY="BR"
```

💡 *Dica:* Para consultar as siglas oficiais de cada região aceitas pela API, acesse a tabela global direto na fonte: [APNIC Labs ISO Country Codes](https://stats.labs.apnic.net/ipv6)

---

## 📐 3. Integração com o Zabbix

1. Acesse o painel web do seu Zabbix Server.
2. Vá em **Data collection** -> **Templates** -> **Import** e selecione o arquivo `templates/ASN-IPV6MONv2.yaml`.
3. Associe o template ao Host de monitoramento desejado.
4. **Configuração Obrigatória da Macro:** Vá na aba **Macros** do seu Host e preencha o valor da macro `{$ASN_NUM}` com o número do seu ASN (exemplo: `52913`). Sem isso, o Zabbix não saberá qual operadora monitorar.
5. Os parâmetros posicionais aceitos nativamente pelo `ipv6.sh` são:
   * `ipv6.sh[{#ASN},asnum]` -> Retorna o número do ASN.
   * `ipv6.sh[{#ASN},asname]` -> Retorna o Nome Fantasia oficial da Organização no APNIC.
   * `ipv6.sh[{#ASN},capable]` -> Retorna a porcentagem de Capacidade IPv6.
   * `ipv6.sh[{#ASN},preferred]` -> Retorna a porcentagem de Preferência IPv6.

---

## 📉 4. Importação do Dashboard no Grafana

1. No menu lateral do Grafana, clique em **Dashboards** -> **New** -> **Import**.
2. Cole o conteúdo do arquivo `grafana/ASN-IPV6MONv2.json` ou clique em *Upload JSON file*.
3. Na janela de importação, selecione o seu Data Source do Zabbix correspondente.
4. Clique em **Import**.

⚠️ **Ajuste das Variáveis de Topo (Obrigatório):**
Logo após importar, você verá os seletores no topo da tela. Ajuste os seguintes campos para sincronizar os dados:
* **Host no Zabbix (`$VISIBLE_NAME`):** Altere essa variável de texto para o nome exato (Visible hostname) que você cadastrou no seu Zabbix (Ex: `IPV6MON-52913`).
* **Número do ASN (`$ASN_NUM`):** Este campo puxará automaticamente o ASN que você configurou na macro `{$ASN_NUM}` dentro do Zabbix no passo anterior.

---

## 💬 5. Configuração das Notificações do WhatsApp

Abra o arquivo `scripts/notificar_ipv6.py` e configure os parâmetros de produção da sua API WPPConnect-Server:

```python
# Configurações da API WhatsApp (Seus dados reais de Produção)
WPP_URL = "http://127.0.0.1:21465/api/SUA_SESSAO/send-mentioned"
TOKEN = "SEU_TOKEN_AQUI"

# Configurações de Destino no Grupo
TARGET_GROUP = "ID_DO_GRUPO@g.us"
NUMEROS_PARA_MENCIONAR = ["558187654321"]
```
💡 *Nota técnica:* O script consome os dados do modo unificado `all` do script Bash, descobre o nome do provedor dinamicamente e faz o uso correto do parâmetro `mentioned` nativo da API para dar o ping sonoro nos administradores marcados no grupo.

---

## 🔍 6. Como descobrir o ID (JID) do seu Grupo do WhatsApp

Se você não souber o identifier único (`@g.us`) do grupo onde deseja receber os alertas diários, configure os parâmetros de sessão no arquivo `extra/get_groups.py` e execute:

```bash
python3 extra/get_groups.py
```
O script vai retornar uma tabela limpa e estruturada no seu terminal:

```
NOME DO GRUPO                       | ID (JID)
---------------------------------------------------------------------------
Grupo de Alertas - Provedor         | 558194669193-1588514048@g.us
```

---

## 🔗 Fonte dos Dados

Todas as informações estatísticas são construidas diretamente do painel global do:
* [APNIC Labs - IPv6 Capability Metrics](https://stats.labs.apnic.net/ipv6)
░▒▓    ~                                                                                                               ✔  with joca@grafana  at 12:26:56  ▓▒░
