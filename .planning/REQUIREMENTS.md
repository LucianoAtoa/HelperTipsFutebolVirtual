# Requirements: HelperTips — v1.4 Configurações de Mercado + Dashboard Ajustes

**Defined:** 2026-04-04
**Core Value:** Capturar automaticamente todos os sinais do Telegram e transformar em estatísticas confiáveis para tomada de decisão nas apostas.

## v1.4 Requirements

Requirements para página de configurações editável, listener config-aware e melhorias no dashboard.

### Configuração de Mercado

- [ ] **CFG-01**: Usuário pode editar stake base, fator de progressão e máximo de tentativas na página `/config`
- [ ] **CFG-02**: Usuário pode editar percentual (%) e odd de referência de cada complementar por mercado principal (Over 2.5 / Ambas Marcam)
- [ ] **CFG-03**: Página exibe preview de stakes por tentativa (T1–T4) e total em risco, recalculando em tempo real ao editar
- [ ] **CFG-04**: Ao salvar, configuração persiste no banco e fica ativa para próximos sinais capturados
- [ ] **CFG-05**: Página carrega com valores padrão (odds atualizadas) se não houver config salva

### Listener Config-Aware

- [ ] **LIS-01**: Listener lê config ativa do banco ao processar cada sinal e calcula stakes com base nesses valores
- [ ] **LIS-02**: Sinais já gravados mantêm valores do momento da captura (não retroativo)

### Dashboard Ajustes

- [ ] **DASH-08**: Seções "Configuração de Mercados" e inputs de simulação de ROI (stake/odd/gale) removidas do dashboard
- [ ] **DASH-09**: KPI "Total Investido" no topo mostra soma de todas as stakes (principal + complementares) no período filtrado
- [ ] **DASH-10**: Seção "Performance Individual por Mercado" exibe cards com greens, reds, taxa, investido, retorno, P&L e ROI por mercado (principal + cada complementar)

### Navegação

- [ ] **NAV-01**: Menu/tabs no topo permite alternar entre Dashboard (`/`) e Configurações (`/config`)

## Future Requirements

Deferred to future release.

### Automação

- **AUTO-01**: Automação de apostas na Bet365 via Selenium/Playwright
- **AUTO-02**: Gestão de banca (stop loss/gain)
- **AUTO-03**: Alertas via Telegram pessoal

### Infra Avançada

- **INFRA-01**: HTTPS com certificado Let's Encrypt (requer domínio)
- **INFRA-02**: Monitoramento com CloudWatch ou similar
- **INFRA-03**: Deploy automático via GitHub Actions SSH

### Resiliência

- **RESIL-01**: Utilitário de backfill para gaps de mensagens perdidas durante offline
- **RESIL-02**: Connection pool com limite configurável
- **RESIL-03**: Tratamento de FloodWaitError do Telegram

## Out of Scope

| Feature | Reason |
|---------|--------|
| Configuração retroativa (recalcular sinais antigos) | Complexidade alta, sinais gravados refletem config do momento da captura |
| Edição de nomes dos complementares via UI | Nomes vêm do schema do banco, alteração rara |
| Múltiplos perfis de configuração | Ferramenta pessoal, 1 config ativa é suficiente |
| Docker / ECS / Kubernetes | Over-engineering para ferramenta pessoal |
| OAuth / autenticação avançada | HTTP Basic Auth suficiente para 1 usuário |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| NAV-01 | Phase 16 | Pending |
| CFG-01 | Phase 17 | Pending |
| CFG-02 | Phase 17 | Pending |
| CFG-03 | Phase 17 | Pending |
| CFG-04 | Phase 17 | Pending |
| CFG-05 | Phase 17 | Pending |
| LIS-01 | Phase 18 | Pending |
| LIS-02 | Phase 18 | Pending |
| DASH-08 | Phase 19 | Pending |
| DASH-09 | Phase 19 | Pending |
| DASH-10 | Phase 19 | Pending |

**Coverage:**
- v1.4 requirements: 11 total
- Mapped to phases: 11
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-04*
*Last updated: 2026-04-04 after roadmap creation (Phases 16-19)*
