---
phase: 08-dashboard-proxy
plan: 02
subsystem: infra
tags: [nginx, reverse-proxy, http-basic-auth, htpasswd, security-group]

# Dependency graph
requires:
  - phase: 08-01
    provides: dashboard rodando via gunicorn em 127.0.0.1:8050
provides:
  - nginx reverse proxy porta 80 -> 127.0.0.1:8050 com HTTP Basic Auth
  - deploy/07-setup-nginx.sh script idempotente para producao
  - .env.example com DASHBOARD_USER e DASHBOARD_PASSWORD documentados
affects: [producao, seguranca, acesso-externo]

# Tech tracking
tech-stack:
  added: [nginx, apache2-utils, htpasswd-bcrypt]
  patterns: [nginx reverse proxy com auth_basic, htpasswd -cbB para scripting nao-interativo, www-data como grupo nginx no Ubuntu 24.04]

key-files:
  created:
    - deploy/07-setup-nginx.sh
  modified:
    - .env.example

key-decisions:
  - "htpasswd -cbB com bcrypt em vez de MD5 padrao — seguranca maior sem custo adicional"
  - "owner root:www-data em .htpasswd — grupo correto do nginx no Ubuntu 24.04 (nao nginx)"
  - "proxy_read_timeout 120s igual ao timeout gunicorn — evita 504 em callbacks Dash lentos"
  - "aviso explicito sobre porta 8050 no Security Group — passo manual documentado no output do script"

patterns-established:
  - "nginx server block com auth_basic no nivel do server (nao no location) — protege todas as rotas"
  - "source .env + validacao de variaveis antes de usar htpasswd — script falha cedo com mensagem clara"

requirements-completed: [DEP-03, DEP-04]

# Metrics
duration: 2min
completed: 2026-04-04
---

# Phase 8 Plan 02: Nginx Reverse Proxy + HTTP Basic Auth Summary

**nginx configurado como reverse proxy com HTTP Basic Auth protegendo o dashboard gunicorn: porta 80 -> 127.0.0.1:8050 com credenciais via .htpasswd bcrypt lidas do .env**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-04-04T04:39:47Z
- **Completed:** 2026-04-04T04:39:47Z
- **Tasks:** 1 (+ 1 checkpoint auto-aprovado)
- **Files modified:** 2

## Accomplishments

- deploy/07-setup-nginx.sh criado: instala nginx+apache2-utils, gera .htpasswd com bcrypt a partir do .env, configura server block com proxy_pass+auth_basic, desabilita site default, habilita nginx no boot
- .env.example atualizado com DASHBOARD_USER e DASHBOARD_PASSWORD na secao Dashboard
- Script avisa explicitamente para fechar porta 8050 no AWS Security Group apos nginx ativo

## Task Commits

1. **Task 1: Criar deploy/07-setup-nginx.sh e atualizar .env.example** - `8dd98f9` (feat)

## Files Created/Modified

- `deploy/07-setup-nginx.sh` - Script idempotente para nginx reverse proxy + HTTP Basic Auth
- `.env.example` - Adicionado DASHBOARD_USER e DASHBOARD_PASSWORD na secao Dashboard

## Decisions Made

- `htpasswd -cbB` usa bcrypt (flag `-B`) em vez do MD5 padrao — mais seguro sem custo adicional de implementacao
- `chown root:www-data` no .htpasswd — grupo correto do nginx no Ubuntu 24.04 (pitfall documentado na pesquisa: usar `nginx` causaria Permission denied 500)
- `proxy_read_timeout 120s` igual ao timeout gunicorn (D-01) — evita 504 Gateway Timeout em callbacks Dash lentos (pitfall 6 da pesquisa)
- Porta 8050 documentada como passo manual no output do script — sem dependencia de AWS CLI, instrucao clara para o operador

## Deviations from Plan

Nenhuma — plano executado exatamente como especificado.

## Issues Encountered

Nenhum — todos os 14 criterios de aceitacao passaram na primeira tentativa.

## User Setup Required

Para ativar o nginx na EC2:

1. Definir `DASHBOARD_USER` e `DASHBOARD_PASSWORD` em `/home/helpertips/.env`
2. `sudo bash deploy/06-setup-dashboard.sh` (se ainda nao executado)
3. `sudo bash deploy/07-setup-nginx.sh`
4. Verificar: `curl -I http://localhost/` deve retornar 401
5. Fechar porta 8050 no AWS Security Group (helpertips-sg)

## Next Phase Readiness

- Phase 08 completa: gunicorn (plan 01) + nginx (plan 02) prontos para deploy na EC2
- Verificacao final: `http://32.194.158.134` deve pedir usuario/senha e carregar dashboard com dados reais
- Porta 8050 deve ser fechada no Security Group apos verificacao bem-sucedida

---
*Phase: 08-dashboard-proxy*
*Completed: 2026-04-04*
