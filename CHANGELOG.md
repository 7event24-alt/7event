# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

## [1.1.1] - 2026-04-15

### Fix
- Error handlers simplificados - resposta simples em produção sem redirects

---

## [1.1.0] - 2026-04-15

### Fix
- ALLOWED_HOSTS com fallback para produção
- Cards de notificação distribuídos harmoniosamente com animações diferenciadas
- Adicionadas notificações "Trabalho Confirmado" e "Orçamento Aceito"

### Fix
- Error handlers com fallback chain para evitar loops

---

## [1.0.7] - 2026-04-15

### Fix
- Error redirect fallback to prevent 400 loop

---

## [1.0.6] - 2026-04-15

### Fix
- Custom error pages redirecionam para home quando DEBUG=False
- Landing page busca planos do banco (mesma lógica da página /planos/)

---

## [1.0.5] - 2026-04-15

### Fix
- Corrige texto "gérer" para "gerenciar" na landing page
- Página de planos agora mostra "Ilimitado" quando limite é 0

---

## [1.0.4] - 2026-04-15

### Fix
- CompanyRequiredMixin verifica usuário autenticado antes de account

---

## [1.0.3] - 2026-04-15

### Fix
- Adiciona domínios confiáveis para CSRF e CORS (7event.com.br, localhost, etc)

---

## [1.0.2] - 2026-04-15

### Fix
- Sistema de notificações: remove filtro de 24h que causava inconsistência entre badge e dropdown

---

## [1.0.1] - 2026-04-15

### Feat
- Sistema de versionamento do app com tag `{% app_version %}`

---

## [1.0.0] - 2026-04-15

### Feat
- Sistema completo de gestão de eventos para autônomos e empresas
- Cadastro de clientes com histórico de trabalhos e receita
- Sistema de trabalhos (jobs) com status: Pendente → Confirmado → Concluído/Cancelado
- Diferença entre confirmar (envia email ao cliente) e aprobar (validação interna/financeira)
- Sistema de workers (membros da equipe) associados aos trabalhos
- Registro de despesas vinculadas a trabalhos por categoria
- Agenda mensal com FullCalendar e filtros por status
- Sistema de planos com limites (Tester, Basic, Professional, Business)
- Painel administrativo para gestão de empresas e métricas
- Notificações internas e emails transacionais

### Feat
- Email de confirmação ao cliente quando trabalho é confirmado
- Campo `notify_on_job_confirmed` para controlar envio de email
- Template HTML semântico para email de confirmação de trabalho

### Feat
- Filtro por usuário para superusers em: despesas, clientes, agenda
- Campo `created_by` em Cliente para rastrear quem criou
- Dropdown de filtro por usuário nas páginas de lista

### Fix
- Templates de email ajustados para português brasileiro
- Correção de bug na agenda: filtro de usuário agora funciona no calendário
- Adicionada verificação para evitar envio duplicado de email ao confirmar trabalho

---

## Formato de versão

Use o formato: `[MAJOR.MINOR.PATCH] - YYYY-MM-DD`

Exemplo: `[1.0.1] - 2026-04-20`

### Types

- **feat**: nova funcionalidade
- **fix**: correção de bug
- **chore**: tarefas de manutenção
- **refactor**: refatoração
- **docs**: documentação

### Como adicionar entrada

```markdown
## [x.x.x] - YYYY-MM-DD

### Feat
- Descrição da nova funcionalidade

### Fix
- Descrição do bug corrigido

### Refactor
- Descrição da refatoração
```