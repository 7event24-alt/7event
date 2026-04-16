# 7Event - Como Usar

**Versão:** 1.2.0

Sistema de gestão de eventos para autônomos e empresas.

---

## 1. Usuários e Empresas

### Tipos de Conta
- **Autônomo**: Para profissionais individuais
- **Empresa**: Para múltiplos usuários

### Planos
| Plano | Máx. Usuários | Máx. Clientes | Máx. Trabalhos |
|-------|---------------|---------------|----------------|
| Tester | 1 | 5 | 10 |
| Basic | 2 | 50 | 100 |
| Professional | 5 | 200 | 500 |
| Business | 10 | 1000 | Ilimitado |

### Gestão de Equipe
- Admin pode convidar membros via email
- Convite expires em 7 dias
- Cada membro pode ter função de admin ou worker

---

## 2. Clientes

- Cadastro com nome, email, telefone, CPF/CNPJ
- Endereço e observações
- Visualização de histórico de trabalhos
- Total de receita gerada

---

## 3. Trabalhos (Jobs)

### Status do Trabalho
```
Pendente → Confirmado → Concluído
    ↓          ↓           ↓
Cancelado (possível em qualquer fase)
```

### Diferença entre Confirmar e Aprovar

**Confirmar**
- Qualquer usuário (admin ou worker)
- Status: PENDING → CONFIRMED
- Envia email de confirmação ao cliente
- Apenas se status for "Pendente"

**Aprovar**
- Apenas administradores
- Status: permanece CONFIRMED
- Define quem aprovou e quando
- Apenas se status for "Confirmado" e ainda não aprovado
- Usado para validação interna/financeira

### Dados do Trabalho
- Cliente associado
- Tipo de evento (Corporativo, Shows, Podcast, etc.)
- Data/hora de início e término
- Local
- Valor (cache)
--workers vinculados
- Pagamento (tipo, valores, datas)

---

## 4. Despesas

- Vinculadas a um trabalho
- Categorias: Equipamento, Transporte, Alimentação, Hospedagem, Marketing, Taxas, Outro
- Valor e data
- Soma total calculada automaticamente no trabalho

---

## 5. Agenda

- Visualização mensal com calendário
- Cores por status:
  - Amarelo: Pendente
  - Verde: Confirmado
  - Roxo: Concluído
  - Vermelho: Cancelado
- Lista de próximos eventos (10 próximos)
- Filtros por status
- Superusers podem filtrar por usuário

---

## 6. Notificações e Emails

### Notificações Internas
- Trabalho criado
- Cliente criado
- Trabalho confirmado (envia email ao cliente)
- Serviço criado
- Despesa criada
- Orçamento criado

### Configuração
- Cada empresa pode habilitar/desabilitar cada tipo de notificação
- Configuração disponível no painel administrativo

---

## 7. Painel Admin

- Gestão de empresas
- Visualização de métricas
- Configuração de planos
- Preferências de notificação por empresa

---

## Fluxo Resumido

1. **Criar cliente** → Define quem contratará
2. **Criar trabalho** → Associa cliente,define data, valor, workers
3. **Confirmar trabalho** → Envia email ao cliente confirmando
4. **Aprovar trabalho** → Admin valida para fechamento
5. **Registrar despesas** → Vincula ao trabalho
6. **Concluir trabalho** → Após evento realizado
7. **Cancelar** → Se necessário

---

##URLs Principais

- `/` - Dashboard
- `/trabalhos/` - Lista de trabalhos
- `/clientes/` - Lista de clientes
- `/despesas/` - Lista de despesas
- `/agenda/` - Calendário
- `/planos/` - Planos disponíveis
- `/equipe/` - Gestão de membros