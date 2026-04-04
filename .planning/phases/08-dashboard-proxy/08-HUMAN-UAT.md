---
status: partial
phase: 08-dashboard-proxy
source: [08-VERIFICATION.md]
started: 2026-04-04T00:00:00Z
updated: 2026-04-04T00:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Executar scripts de deploy na EC2
expected: `sudo bash deploy/06-setup-dashboard.sh && sudo bash deploy/07-setup-nginx.sh` concluem sem erros
result: [pending]

### 2. HTTP 401 sem credenciais
expected: `curl -I http://32.194.158.134/` retorna 401 Unauthorized
result: [pending]

### 3. Dashboard com dados reais via browser
expected: Login com credenciais mostra KPI cards com contagens corretas do banco
result: [pending]

### 4. Serviço dashboard sobrevive a reboot
expected: Após `sudo reboot`, `systemctl status helpertips-dashboard` mostra active (running)
result: [pending]

### 5. Porta 8050 fechada no Security Group
expected: Regra 8050 removida do Security Group — apenas 80/443 + SSH abertos
result: [pending]

## Summary

total: 5
passed: 0
issues: 0
pending: 5
skipped: 0
blocked: 0

## Gaps
