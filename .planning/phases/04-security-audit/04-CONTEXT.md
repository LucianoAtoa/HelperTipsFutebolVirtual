# Phase 4: Security Audit - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Preparar o repositório para publicação segura no GitHub: auditar histórico git, corrigir debug=True no dashboard, atualizar .env.example, e criar README.md completo.

</domain>

<decisions>
## Implementation Decisions

### Debug Mode
- **D-01:** Controlar debug mode via variável de ambiente: `debug=os.getenv('DASH_DEBUG', 'false').lower() == 'true'`. Desligado por padrão (seguro em produção), liga com `DASH_DEBUG=true` no .env local para desenvolvimento.

### README
- **D-02:** README completo com: descrição do projeto, stack, setup local (pip install, .env, PostgreSQL), como rodar listener + dashboard, aviso de segurança sobre .session, badges CI (após Phase 5).

### Git History Audit
- **D-03:** Abordagem grep-based: rodar busca por padrões de secrets no histórico git (API keys, passwords, tokens, .env conteúdo). Se limpo, prosseguir sem BFG Repo Cleaner. Não reescrever histórico desnecessariamente.

### .env.example
- **D-04:** Atualizar .env.example com variáveis necessárias para AWS deploy (a serem definidas na Phase 6). Manter sem valores reais.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above and REQUIREMENTS.md (SEC-01..04).

### Código relevante
- `helpertips/dashboard.py` linha 997 — `app.run(debug=True, host="0.0.0.0", port=8050)` a ser corrigido
- `.gitignore` — já configurado corretamente (*.session, .env)
- `.env.example` — template atual com 8 variáveis

</canonical_refs>

<code_context>
## Existing Code Insights

### Estado Atual de Segurança
- `.gitignore` correto: `*.session`, `*.session-journal`, `.env` — configurado desde o primeiro commit
- `git log` não mostra nenhum .env ou .session no histórico — limpo
- `dashboard.py:997` tem `debug=True` hardcoded — único blocker de segurança
- `.env.example` existe com 8 variáveis sem valores — precisa ser expandido para deploy

### Integration Points
- `dashboard.py` é o único arquivo que precisa de mudança de código (debug flag)
- README.md é um arquivo novo (não existe)
- `.env.example` precisa de atualização (adicionar DASH_DEBUG)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-security-audit*
*Context gathered: 2026-04-03*
