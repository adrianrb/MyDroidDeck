# MyDroidDeck

**MyDroidDeck** transforma um dispositivo Android em um *Stream Deck* programável. O app cliente exibe perfis com botões e, ao tocá-los, envia ações ao servidor FastAPI, que executa programas e comandos no host Windows via interop com WSL.

## Visão Geral

- **Cliente Android** (`app/`): App nativo em Kotlin + Jetpack Compose (Material 3). Renderiza perfis em grade, exibe ícones reais dos executáveis, suporta temas claro/escuro/sistema, edge-to-edge e adaptação paisagem/retrato.
- **Servidor** (`server/`): Backend FastAPI com painel administrativo em Jinja. Armazena perfis, botões e ações, gerencia pareamento de dispositivos e despacha comandos para o Windows.
- **Instaladores** (`setup/`): Pacotes para Windows (Inno Setup, sem login por padrão no instalador) e Linux/WSL para facilitar a instalação.

## Arquitetura

```
[App Android] --(REST + Bearer Token)--> [Servidor FastAPI (WSL)]
                                              |-- Painel Admin (Jinja/HTML)
                                              |-- SQLite (SQLAlchemy)
                                              |-- Cache de ícones (PNG extraídos)
                                              '-- PowerShell/WSL interop --> Executáveis Windows
```

## Principais Recursos

- **Perfis e botões**: Organize ações em perfis. Botões exibem ícones reais dos programas mapeados.
- **Pareamento por código ou QR**: Primeiro acesso pelo código mostrado no admin ou escaneando QR (`mydroiddeck://pair?...`).
- **Execução restrita**: Apenas ações cadastradas em `/admin/actions` são executadas. Chaves desconhecidas retornam `status: "unknown"` sem executar nada.
- **Painel Admin completo**: Gerenciar perfis, ações (com seletor de arquivo nativo no Windows), dispositivos, conectividade, backup/exportar-importar.
- **Conectividade flexível**: Suporte a USB (`adb reverse`), Wi-Fi/LAN (com portproxy no Windows) e TLS com certificado auto-assinado.
- **Temas**: Menu no cabeçalho do deck para alternar entre *seguir sistema*, *claro* ou *escuro*.
- **Internacionalização**: pt-BR como padrão, com suporte a inglês (app e servidor).
- **Backup/Restore**: Exporta e importa configurações completas via JSON (ações, perfis e configurações de runtime).

## Estrutura do Projeto

| Diretório | Descrição | Versão |
|---|---|---|
| [`app/`](./app) | Cliente Android nativo (Kotlin + Compose). | `0.5.6` |
| [`server/`](./server) | Servidor FastAPI + painel admin Jinja. | `0.5.3` |
| [`setup/`](./setup) | Instaladores Windows (Inno Setup) e Linux/WSL. | — |
| [`docs/`](./docs) | Plano de testes, recursos livres e licenças. | — |

## Documentação

- [**Servidor**](./server/README.md) — Setup, execução, TLS, ações/executáveis, ícones, backup, deploy em LAN
- [**App Android**](./app/README.md) — Build, pareamento, deck, temas, configurações
- [**Instaladores**](./setup/README.md) — Windows offline bundle + Inno Setup, Linux/WSL, conectividade USB/Wi-Fi
- [**Plano de testes**](./docs/TEST_PLAN.md) — Casos de teste e verificação em dispositivo físico
- [**Recursos livres**](./docs/FREE_RESOURCES.md) — Bibliotecas, assets e atribuições
- [**AGENTS.md**](./AGENTS.md) — Diretrizes para desenvolvimento no ambiente

## Início Rápido (Desenvolvimento)

### Servidor (WSL/Linux)

```bash
cd server
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest                    # Rodar testes
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Para HTTPS em desenvolvimento:
```bash
deploy/gen-cert.sh
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 \
  --ssl-keyfile deploy/tls/key.pem --ssl-certfile deploy/tls/cert.pem
```

### App Android (Windows)

O SDK Android e Gradle não rodam bem no WSL — use o helper do projeto:

```bat
cd app
C:\Desenv\_Projetos\IA\MyDroidDeck\app\gradlew-win.bat --no-daemon test
C:\Desenv\_Projetos\IA\MyDroidDeck\app\gradlew-win.bat --no-daemon assembleDebug
```

O APK será gerado em `app/build/outputs/apk/debug/`.

## Segurança

- **API REST**: Autenticação por token Bearer via `POST /pair` com código de pareamento compartilhado
- **Painel Admin**: Login com usuário/senha + cookie HMAC assinado (`httponly`, `samesite=lax`). **Troque as credenciais padrão** em `server/.env`
- **Execução controlada**: Apenas ações mapeadas em `/admin/actions` são executadas. Chaves não configuradas retornam `status: "unknown"`
- **Tokens revogáveis**: Dispositivos pareados podem ser revogados pelo admin (após revogação, o app retorna à tela de pareamento)
- **TLS**: Suporte a HTTPS com certificado auto-assinado para uso em LAN

## Stack Tecnológica

| Componente | Tecnologias |
|---|---|
| **App** | Kotlin 1.9.24, Jetpack Compose (Material 3), Compose BOM 2024.06.00, Retrofit 2.11, OkHttp 4.12, ZXing (QR) |
| **Servidor** | Python 3.10+, FastAPI, Uvicorn, SQLAlchemy 2, Pydantic v2, Jinja2, Segno (QR) |
| **Build** | Gradle 8.7, AGP 8.5.2, Inno Setup 6.3+ (Windows), shell scripts (Linux/WSL) |

## Licenças

Consulte [`docs/FREE_RESOURCES.md`](./docs/FREE_RESOURCES.md) para a lista completa de dependências, assets e suas licenças.
