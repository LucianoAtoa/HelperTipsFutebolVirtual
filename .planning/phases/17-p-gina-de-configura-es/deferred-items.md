# Itens Deferidos — Phase 17

## Mudança pré-existente em helpertips/queries.py

**Descoberto durante:** Task 17-01-2 (save_mercado_config e save_complementares_config)

**Descrição:** O arquivo `helpertips/queries.py` continha mudanças não commitadas (visible no git status inicial como `M helpertips/queries.py`) que trocam `4` hardcoded por `attempts` variável nas funções `calculate_roi_complementares` e `calculate_pl_por_entrada`:

- Antes: `invested = stake_comp * 4` (RED: sempre 4 tentativas)
- Depois: `invested = stake_comp * attempts` onde `attempts = 4 if resultado == "RED" else tentativa`

Esta mudança quebra 3 testes pré-existentes:
- `test_calculate_roi_complementares_green_t1_stake_fixa`
- `test_pl_complementares_over_2_5`
- `test_pl_complementares_ambas_marcam`

**Escopo:** Fora do escopo do Plan 17-01. As mudanças pré-existentes devem ser avaliadas e os testes ajustados em uma task separada.

**Ação:** Não corrigido — documentado aqui para resolução futura.
