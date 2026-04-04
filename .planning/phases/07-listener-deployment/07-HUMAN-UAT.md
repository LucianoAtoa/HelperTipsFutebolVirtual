---
status: partial
phase: 07-listener-deployment
source: [07-VERIFICATION.md]
started: 2026-04-04T00:00:00Z
updated: 2026-04-04T00:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. systemctl status helpertips-listener mostra active (running)
expected: Output contém "active (running)" após enable --now
result: [pending]

### 2. Arquivo .session gerado com owner correto
expected: /home/helpertips/helpertips_listener.session existe com owner helpertips:helpertips
result: [pending]

### 3. Sinais capturados no banco
expected: SELECT COUNT(*) FROM signals retorna > 0
result: [pending]

### 4. Logs em formato correto
expected: /var/log/helpertips/listener.log contém entradas sem escape codes ANSI
result: [pending]

### 5. Serviço sobrevive a reboot
expected: Após sudo reboot, systemctl status helpertips-listener mostra active (running)
result: [pending]

## Summary

total: 5
passed: 0
issues: 0
pending: 5
skipped: 0
blocked: 0

## Gaps
