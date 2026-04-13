# Medium Daily Genie

Protótipo em Python para ler emails do Gmail recebidos nos últimos 1 dia com assunto `Medium Daily Digest` e imprimir no terminal um Markdown com todos os links encontrados.

## Estrutura

- `main.py`: ponto de entrada do protótipo
- `src/medium_daily_digest/services/`: autenticação Gmail, leitura dos emails e geração do relatório
- `src/medium_daily_digest/utils/`: extração de links
- `credentials/google_oauth_client.json` ou `client_secret_*.json` na raiz: credenciais OAuth do Google
- `credentials/token.json`: token gerado localmente após a primeira autenticação

## Como rodar

1. Ative a Gmail API em um projeto do Google Cloud.
2. Crie um OAuth Client ID do tipo `Desktop app`.
3. Baixe o JSON e salve em `credentials/google_oauth_client.json` ou deixe o arquivo `client_secret_*.json` na raiz do projeto.
4. Instale as dependências:

```bash
.venv/bin/pip install -r requirements.txt
```

5. Execute:

```bash
.venv/bin/python main.py
```

Na primeira execução, o navegador abrirá para autenticação da conta Google e um `token.json` será salvo localmente.
