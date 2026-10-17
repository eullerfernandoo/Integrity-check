# Integrity Check 🔐

Ferramenta de linha de comando em Python que detecta adulteração em arquivos de log usando hashes SHA-256, desenvolvida como projeto de estudo de segurança e escrita de scripts.

## Sobre o projeto

O Integrity Check funciona como um monitor de integridade de arquivos (FIM) simplificado. Ele grava uma "impressão digital" (hash SHA-256) de cada log e, nas verificações seguintes, compara com o estado gravado para apontar qualquer divergência. O projeto foi construído com foco em aplicar na prática conceitos como hash criptográfico, HMAC, leitura de arquivos em blocos e testes automatizados.

## Funcionalidades

- 📁 Aceita um arquivo único ou um diretório inteiro (com subpastas)
- 🔢 Calcula o hash SHA-256 de cada arquivo
- 💾 Grava os hashes em um banco local (JSON) no primeiro uso (`init`)
- 🔍 Compara os hashes atuais com os gravados (`check`)
- ⚠️ Reporta arquivos **modificados**, **removidos** e **novos (não registrados)**
- ✍️ Permite aceitar manualmente uma mudança legítima (`update`)
- 🛡️ Protege o próprio banco contra edição com assinatura HMAC (opcional)
- 🚦 Retorna código de saída 0 (tudo intacto) ou 1 (divergência), útil para agendar a verificação

## Conceitos aplicados

| Conceito | Onde aparece |
| --- | --- |
| **Hash criptográfico** | `sha256_file()` gera uma impressão digital de 64 caracteres hexadecimais; mudar um único byte altera o hash inteiro (efeito avalanche) |
| **Leitura em blocos** | O arquivo é lido em blocos de 64 KB, então logs de vários GB não estouram a memória |
| **HMAC** | Com a variável `INTEGRITY_KEY` definida, o banco é assinado; sem a chave, um invasor não consegue forjar uma assinatura válida |
| **Comparação segura** | `hmac.compare_digest()` evita ataques de temporização na verificação da assinatura |
| **Escrita atômica** | O banco é gravado em um arquivo temporário e trocado com `os.replace()`, evitando banco corrompido se o programa travar |
| **Separação de responsabilidades** | `check` nunca altera o banco; só um humano, via `update`, decide aceitar uma mudança |
| **Testes automatizados** | `pytest` valida que o hash calculado bate com o da biblioteca padrão |

## Estrutura do projeto

```
Integrity check/
├── integrity_check.py  → Ferramenta (hash, banco de hashes, comandos init/check/update)
├── test_integrity.py   → Testes automatizados (pytest)
├── .gitignore          → Ignora a pasta de laboratório e arquivos gerados
└── README.md           → Documentação
```

## Como executar

### Pré-requisitos

- Python 3.8 ou superior (o código usa o operador `:=`)
- Nenhuma biblioteca externa para usar a ferramenta (só a biblioteca padrão)
- `pytest` apenas para rodar os testes

### Comandos

Os exemplos usam caminhos do Windows. No Linux ou macOS, troque `\` por `/` e `python` por `python3`.

```
python integrity_check.py --db lab\db\hashes.json init lab\logs
python integrity_check.py --db lab\db\hashes.json check lab\logs
python integrity_check.py --db lab\db\hashes.json update lab\logs\auth.log
```

| Comando | O que faz |
| --- | --- |
| `init` | Calcula e grava os hashes (cria o estado de referência) |
| `check` | Recalcula e compara com os hashes gravados (não altera o banco) |
| `update` | Recalcula e sobrescreve o hash, aceitando a mudança como legítima |

A opção `--db` define onde o banco de hashes fica. Por padrão, ele é salvo em `~/.integrity-check/hashes.json`.

## Exemplo de uso

1. Crie uma pasta de testes com alguns logs de mentira (nunca teste em logs reais do sistema)
2. Rode o `init` para gravar o estado de referência
3. Rode o `check`: todos os arquivos aparecem como `Unmodified`
4. Altere um log e rode o `check` de novo
5. Aceite a mudança com o `update` e verifique mais uma vez

Exemplos de saída do `check`:

```
...\lab\logs\auth.log: Status: Unmodified
...\lab\logs\syslog: Status: Modified (Hash mismatch)
...\lab\logs\app.log: Status: Missing (arquivo removido)
...\lab\logs\intruso.log: Status: Not registered (arquivo novo)
```

## Protegendo o banco de hashes (HMAC)

Quem consegue alterar um log também pode tentar alterar o banco de hashes para esconder a