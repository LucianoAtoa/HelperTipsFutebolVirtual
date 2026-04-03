---
status: partial
phase: 01-foundation
source: [01-VERIFICATION.md]
started: 2026-04-03T11:10:00Z
updated: 2026-04-03T11:10:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Listener conecta e captura sinal
expected: Signal aparece como row na tabela signals sem erro de DB no terminal
result: [pending]

### 2. Startup Panel com rich
expected: Rich Panel com título do grupo e contagem de sinais (zero ou não)
result: [pending]

### 3. MessageEdited atualiza row (não duplica)
expected: SELECT COUNT(*) WHERE message_id=X retorna 1; resultado atualizado
result: [pending]

### 4. Ctrl+C shutdown limpo
expected: Mensagem de encerramento em rich markup, processo sai sem traceback
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
