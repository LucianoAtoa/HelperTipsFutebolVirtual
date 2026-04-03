---
status: resolved
phase: 01-foundation
source: [01-VERIFICATION.md]
started: 2026-04-03T11:10:00Z
updated: 2026-04-03T12:35:00Z
---

## Current Test

[all tests complete]

## Tests

### 1. Listener conecta e captura sinal
expected: Signal aparece como row na tabela signals sem erro de DB no terminal
result: passed — GREEN e NOVO capturados corretamente, parse failure para mensagem de celebração (esperado)

### 2. Startup Panel com rich
expected: Rich Panel com título do grupo e contagem de sinais (zero ou não)
result: passed — Panel "HelperTips – {VIP} ExtremeTips – Over 2.5" com tabela de estatísticas

### 3. MessageEdited atualiza row (não duplica)
expected: SELECT COUNT(*) WHERE message_id=X retorna 1; resultado atualizado
result: passed — NOVO apareceu seguido de GREEN para mesmo sinal (Premiership, Over 2.5)

### 4. Ctrl+C shutdown limpo
expected: Mensagem de encerramento em rich markup, processo sai sem traceback
result: passed — "Sessao encerrada — cobertura: 80.0% (4/5)", desconexão limpa

## Summary

total: 4
passed: 4
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
