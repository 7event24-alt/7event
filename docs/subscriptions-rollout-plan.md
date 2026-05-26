# Plano Completo: Migracao para Assinatura Recorrente

## Objetivo

Migrar o sistema de cobranca de pagamento unico para assinatura recorrente com Mercado Pago, preservando funcionamento atual, sem mudancas destrutivas, com rollout gradual, testes completos e limpeza de legado somente apos estabilizacao em producao.

## Premissas e decisoes

- Plano FREE obrigatorio como fallback de downgrade.
- Tolerancia global de inadimplencia: 5 dias a partir de `past_due_since`.
- Cancelamento solicitado pelo usuario: encerra renovacao, mas mantém acesso ate fim do ciclo pago.
- Ciclo de cobranca individual por usuario.
- Limpeza de codigo nao usado apenas depois do go-live e apos janela de observacao.

## Principios de seguranca e nao destrutividade

- Nao remover fluxos legados antes da validacao em producao do fluxo recorrente.
- Introduzir mudancas com feature flags para permitir ativacao gradual.
- Garantir compatibilidade retroativa dos endpoints/servicos por periodo de transicao.
- Usar migracoes aditivas primeiro (adicionar campos/tabelas), sem alterar dados antigos de forma irreversivel.
- Toda rotina critica com idempotencia e logs auditaveis.

## Arquitetura alvo

### Dominio de assinatura

- Modelo de assinatura com campos:
  - `user_id`
  - `plan_id` (dinamico, FK para catalogo de planos)
  - `mp_subscription_id`
  - `status_financeiro` (`regular`, `inadimplente`, `suspenso`, `cancelamento_agendado`, `cancelado`)
  - `billing_anchor_date`
  - `current_period_start`, `current_period_end`, `next_charge_date`
  - `past_due_since`
  - `cancel_at_period_end`, `cancelled_at`
  - `metadata/raw_payload` para rastreabilidade

### Integracao Mercado Pago

- Criacao de assinatura recorrente por usuario/plano.
- Persistencia de request/response brutos para diagnostico.
- Webhook idempotente por `event_id` e/ou `resource_id`.
- Rotina de reconciliacao para eventos perdidos.

### Regras de acesso

- `regular`: acesso normal.
- `inadimplente` dentro de 5 dias: acesso mantido com aviso.
- `inadimplente` apos 5 dias: `suspenso` + downgrade FREE.
- `cancelamento_agendado`: acesso ate `current_period_end`.
- `cancelado`: sem renovacao, permanece no FREE.

## Plano de implementacao end-to-end

### Fase 0: Preparacao

1. Criar task principal e subtasks tecnicas.
2. Definir branch a partir de `develop` com convencao do projeto (`feat/<task-id>-...`).
3. Mapear pontos impactados: pagamentos, planos, middleware de limite, webhooks, jobs agendados, UI de assinatura, admin e notificacoes.
4. Definir feature flags:
   - `SUBSCRIPTIONS_RECURRING_ENABLED`
   - `SUBSCRIPTIONS_ENFORCEMENT_ENABLED`
   - `SUBSCRIPTIONS_CANCEL_AT_PERIOD_END_ENABLED`
5. Definir metricas de sucesso e alertas.

### Fase 1: Modelagem e migracoes (nao destrutiva)

1. Criar/ajustar modelo de assinatura com novos campos.
2. Adicionar indices para consultas por `user_id`, `status_financeiro`, `next_charge_date`.
3. Criar tabela de eventos processados para idempotencia de webhook.
4. Manter modelos/fluxos antigos intactos nesta fase.
5. Criar migration de backfill leve (sem apagar nada):
   - usuarios ativos recebem estado inicial coerente.

### Fase 2: Servicos de negocio

1. Implementar servico de criacao de assinatura recorrente.
2. Implementar servico de cancelamento no fim do ciclo.
3. Implementar servico de downgrade para FREE.
4. Implementar servico de reativacao apos pagamento.
5. Padronizar contratos de erro e logging estruturado.

### Fase 3: Webhooks e reconciliacao

1. Criar endpoint de webhook recorrente com validacao de autenticidade.
2. Implementar idempotencia forte (evento duplicado nao altera estado duas vezes).
3. Mapear status externos para estado interno.
4. Criar job de reconciliacao periodica no MP por assinatura ativa/inadimplente.
5. Criar job de corte por tolerancia de 5 dias.

### Fase 4: Aplicacao de regras no produto

1. Atualizar fluxo de "Assinar agora" para recorrencia via flag.
2. Incluir botao "Cancelar assinatura" na area do usuario.
3. Exibir status e datas de ciclo de forma clara.
4. Aplicar bloqueios de limite/acesso conforme estado financeiro.
5. Garantir que FREE seja aplicado automaticamente no downgrade.

### Fase 5: Rollout gradual

1. Ativar apenas para ambiente de homologacao.
2. Ativar para grupo piloto de usuarios em producao.
3. Medir erros, latencia, divergencia de estado e taxa de recuperacao de webhook.
4. Expandir para 25%, 50%, 100% com checkpoints entre etapas.
5. Ativar enforcement global so apos estabilidade.

### Fase 6: Pos go-live e limpeza de legado

1. Janela de observacao recomendada: 14 dias.
2. Levantar candidatos de remocao:
   - fluxo de pagamento unico,
   - rotas de compatibilidade expiradas,
   - comandos antigos,
   - templates/JS nao referenciados,
   - env vars obsoletas.
3. Remover em PRs pequenos por modulo.
4. Manter rollback simples por PR.

## Estrategia de testes pos implementacao

### 1) Testes automatizados

- Unitarios:
  - transicao de estados financeiros,
  - regra de tolerancia de 5 dias,
  - cancelamento no fim do ciclo,
  - downgrade/reativacao,
  - idempotencia do webhook.
- Integracao:
  - criacao de assinatura com gateway mockado,
  - recebimento de webhook aprovado/pendente/falha/cancelado,
  - reconciliacao corrigindo estado divergente.
- E2E:
  - usuario assina,
  - usuario cancela e mantem acesso ate fim do ciclo,
  - inadimplencia e corte apos 5 dias,
  - reativacao por regularizacao de pagamento.

### 2) Testes manuais guiados (UAT)

- Assinatura nova em plano pago.
- Troca de plano.
- Cancelamento com acesso mantido no periodo.
- Webhook duplicado (nao deve duplicar efeito).
- Falha temporaria no webhook e recuperacao por reconciliacao.
- Downgrade para FREE no prazo correto.
- Reativacao automatica apos pagamento.

### 3) Testes de resiliencia

- Reprocessamento seguro de eventos.
- Execucao concorrente de jobs sem corrupcao de estado.
- Cenarios de indisponibilidade temporaria do MP.

## Observabilidade e operacao

- Logs estruturados com `subscription_id`, `user_id`, `event_id`.
- Dashboard operacional com:
  - assinaturas por status,
  - falhas de webhook,
  - reconciliacoes com divergencia,
  - downgrades por inadimplencia,
  - reativacoes.
- Alertas:
  - aumento de falhas em webhook,
  - backlog de reconciliacao,
  - crescimento anormal de `inadimplente`.

## Rollback e contingencia

- Rollback funcional por feature flag, sem destruir dados novos.
- Manter fluxo antigo disponivel durante transicao.
- Em incidente:
  1. desativar flag de recorrencia,
  2. manter cobranca anterior,
  3. corrigir servico,
  4. reativar rollout gradual.

## Criterios de aceite finais

- Todas as assinaturas novas entram pelo fluxo recorrente.
- Cancelamento funciona no fim do ciclo pago.
- Tolerancia de 5 dias aplicada corretamente.
- Downgrade FREE e reativacao automatica validados.
- Webhook idempotente e reconciliacao sem divergencias criticas.
- Sem regressao em limites/plano/fluxos existentes.
- Testes automatizados e UAT aprovados.

## Entregaveis

- Documento tecnico de arquitetura e regras.
- Migrations e servicos com cobertura de testes.
- Endpoints/webhooks e jobs agendados operacionais.
- Dashboard e alertas de operacao.
- Relatorio de go-live + relatorio de limpeza de legado.
