# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

## [Unreleased]

### Feat
- Novo domínio de pagamentos (`base/payments`) com rastreio ponta a ponta para Checkout Pro: criação de transações mensais, referência externa única por usuário/plano/mês, webhook Mercado Pago e atualização automática de assinatura/plano.
- Integração base com n8n para disparo de mensagens WhatsApp via webhook, com helper reutilizável (`base/core/n8n.py`) e variáveis de ambiente dedicadas.
- Catálogo central de mensagens WhatsApp por motivo/evento (`base/core/whatsapp_messages.py`), com templates para cadastro, ativação e status de pagamento.
- Helper de n8n expandido para aceitar payload extra e simulação de evento real (`send_whatsapp_event`) com metadados (`event_id`, `event`, `source`, `sent_at`, `context`).
- Perfil do usuário agora possui campo de **Chave PIX** com exibição e edição na tela de perfil.
- Lista de **Minha Agenda Pessoal** passou a reutilizar o mesmo modal para criar e editar itens.
- Orçamentos aceitos agora permitem criar trabalho pré-preenchido com dados do orçamento (`cache` usando total do orçamento).
- PDF de orçamento foi reestruturado com logo dinâmica da empresa (fallback 7event) e assinatura de marca no rodapé.
- Agenda ganhou suporte ao modelo **Agenda Pessoal** (`PersonalAgendaEvent`) com status e validação de horário (`hora fim > hora início`).
- Calendário e sidebar de agenda agora exibem itens de agenda pessoal em roxo, separados de tarefas e com ordenação por data/hora.
- Área pessoal ganhou página dedicada **Agenda Pessoal** com listagem, filtros e CRUD dos eventos.
- Agenda Pessoal ganhou opção de recorrência com frequências: diariamente, semanalmente, mensalmente e anualmente (com data final opcional).
- Agenda Pessoal passou a usar campo de horário + duração (30m, 1h, 2h, 3h, 4h e dia inteiro), refletindo corretamente no calendário semanal.
- Agenda recebeu micro animações suaves na troca de visão e navegação (mês/semana/lista) com fallback para `prefers-reduced-motion`.
- Agenda ganhou legenda fixa de cores dos tipos de evento, com versão compacta no mobile.
- Estado da agenda passou a persistir via `localStorage` (visão, filtros de tipo/status e aba da sidebar).
- Lógica de limite de plano foi unificada e aplicada em criações de clientes (incluindo rápido), trabalhos, orçamentos, despesas, tarefas e agenda pessoal, com aviso de upgrade ao exceder limite.
- Planos ganharam novos limites granulares: `max_quotes`, `max_personal_tasks` e `max_personal_agenda_events` (mantendo semântica `0 = sem limite`).
- Testes automatizados de limite de plano foram adicionados para validar bloqueio e fluxo de liberação quando o limite é infinito.
- Listas de Trabalhos, Orçamentos, Clientes, Tarefas e Despesas foram padronizadas no layout em cards (estilo Agenda Pessoal), com melhor leitura, ações consistentes e badges no formato "rótulo: valor".
- Sistema de tema com modos Claro, Escuro e Automático foi adicionado no Dashboard e na Landing Page, com persistência em `localStorage` e aplicação antecipada no `<head>` para evitar flash de tema.

### Fix
- Fluxo de planos pagos deixou de depender de aprovação manual de suporte e passou a usar checkout dinâmico por transação, com páginas de retorno (`success`, `pending`, `failure`) e processamento idempotente de webhook para evitar duplicidade.
- Perfil agora normaliza telefone para salvar no padrão `55DDDNÚMERO`, exibe telefone formatado (`+55 (DD) 9XXXX-XXXX`) e mantém CPF persistido/formatado no formulário e na visualização.
- Preferência do Mercado Pago passou a enviar `payment_methods` explícitos (parcelamento até 12x, sem exclusões) para manter checkout aberto e reduzir chance de fluxo wallet-only.
- Disparo de WhatsApp por motivo agora valida se existe template antes de enviar; sem template, a requisição para n8n é ignorada. Fluxos conectados: cadastro, ativação, pagamento aprovado e downgrade por cutoff.
- Menções de suporte no sistema foram padronizadas para direcionar contato via WhatsApp no número **+55 11 94347-9664** (landing page, suporte, login, FAQ, mensagens de validação e email de boas-vindas).
- Edição de item da agenda pessoal deixou de usar `prompt` e passou para formulário estruturado, mantendo o mesmo fluxo de validação e envio.
- Email de redefinição de senha voltou ao template padrão do Django, mantendo domínio/protocolo do host atual.
- Fluxo de orçamento passou a usar status padrão **Criado** (em vez de rascunho), com campo de status visível apenas na edição.
- Template de email e detalhe de orçamento corrigidos para nomenclatura de diária e formatação monetária brasileira.
- Botão de envio de orçamento no detalhe permanece visível e vira **Reenviar por email** após envio.
- Redefinição de senha agora redireciona diretamente para a tela de login após confirmação da nova senha.
- Página de agenda do dia passou a exibir Agenda Pessoal com organização por blocos (Trabalhos, Agenda Pessoal, Visitas Técnicas e Tarefas) e ações rápidas de criação.
- Botões de adicionar despesa em Trabalho e Orçamento passaram a abrir modal na própria tela, sem redirecionar para formulário externo.
- Lista de mensagens de suporte foi redesenhada em cards para melhor leitura e o bug de exibir múltiplos popups ao abrir a lista foi corrigido.
- FAQ da landing page voltou a funcionar com correção do script de abas/acordeão e ajustes no bloco de instalação PWA.

## [1.5.0] - 2026-04-21

### Feat
- **Agenda com calendário FullCalendar funcional**:
  - Calendário renderiza eventos da API `/app/agenda/api/eventos/`
  - Botão "Novo Trabalho" com data do calendário
  - Página de dia (`/app/agenda/dia/`) com link para criar trabalho
- **Despesas com trabalho pré-selecionado**:
  - Ao criar despesa da página de detalhes do trabalho, trabalho já vem selecionado
- **Landingpage mobile responsivo**:
  - Phone hero centralizado no mobile
  - Trust badges aparecem no mobile
  - Design otimizado para telas menores

### Fix
- **Agenda**: Todos usuários da conta veem todos os trabalhos (remove filtro `user`)
- **Agenda API**: Corrigido filtro de users para não-superuser
- **Agenda calendário**: URL da API corrigida (`/app/agenda/api/eventos/`)
- **Jobs**: Data do evento preenchida ao criar da agenda
- **Jobs**: URLs corrigidas com prefixo `/app/`
- **FCM**: Métricas corrigidas usando `PlanType` ao invés de string
- **Jobs Detail**: Seção "Workers" removida (campo não existe no modelo)

### Remov
- **Workers/Equipes**: Removido código e referências que usavam campo inexistente
  - `agenda/views.py`, `agenda/serializers.py`, `jobs/views.py`
  - Templates: `jobs/detail.html`, `landingpage/index.html`
  - Settings: referência `jobs.JobWorker`

---

## [1.4.1] - 2026-04-19

### Fix
- Banner de update do PWA removido (causava problemas no mobile)
- Botão flutuante de install só aparece se app não estiver instalado
- Context processor: verificado se plan é None antes de acessar atributos

---

## [1.4.0] - 2026-04-19

### Feat
- **Firebase Cloud Messaging (FCM) para notificações push**:
  - Service Worker (`firebase-messaging-sw.js`) para receive push notifications
  - SDK Firebase added to frontend (landingpage)
  - Script to request permission and save FCM token
  - API endpoints: `/api/v1/fcm/token/` and `/api/v1/fcm/send/`
  - Push notifications work even when app is in background
  - VAPID public key configured for web push

---

## [1.3.1] - 2026-04-19

### Feat
- **PWA com atualização automática**:
  - Banner de "Nova versão disponível" quando há update
  - Service Worker mejorado para detectar updates
  - Botão para atualizar com um clique

### Fix
- SITE_ID forçado = 1 para evitar erros de Site lookup
- Tabela django_site criada no banco de produção
- Permissões concedidas ao usuário do banco
- Context processor e outros arquivos pendentes commitados

---

## [1.3.0] - 2026-04-19

### Feat
- **PWA - Progressive Web App**: Sistema instalável como app no celular
  - Arquivo manifest.webmanifest com configurações de instalação
  - Service Worker para cache e funcionamento offline
  - Ícones de tamanho correto (192x192, 512x512)
  - Botão flutuante "Instalar App" no mobile
  - Meta tags para iOS e Android
- **FAQ integrado na LP**: Seção FAQ com abas condicionais
  - Abas: Login, Cadastro (sempre visíveis), Trabalhos, Orçamentos (só logado), Planos
  - Redirecionamento de /app/suporte/faq/ para LP#faq
- **Template suporte unificado**: contact.html e success.html com mesmo header/footer da LP
- **Favicon para atalhos mobile**: Tags específicas para iOS e Android

### Fix
- Página de FAQ removida, integrada à LP
- Footer colado na base (flex-grow)
- Correção do template support para usar header/footer da LP
- Links do menu atualizados para âncoras (#faq, #contato)
- Data do Site atualizada para localhost

### Refactor
- Campos de pagamento no formulário de trabalhos:
  - Valor Total e Restante são readonly (calculados automaticamente)
  --payment_total e payment_remaining_value com campos hidden
  - Payment Type com onchange para atualizar campos
- Datas de pagamento:
  - Pagamento Antecipado: data de hoje
  - Pagamento Total: 20 dias a partir de HOJE
  - Pagamento Parcial: 20 dias após data do evento + 20 dias para restante
- Labels atualizados: "Cache Total" (sem *), "Valor Total", "Valor Restante"
- Disclaimer removido de "Data Pagamento Restante"

---

## [1.2.1] - 2026-04-15

### Feat
- Página de perfil com tags dinâmicas: Super Admin, Admin, Autônomo, Equipe, Sem empresa
- Seção "Empresa" dinâmica com limites do plano (clientes/trabalhos/despesas usados vs limite)
- Para superusers: mostra total de empresas e usuários no sistema
- Adiciona propriedades client_count, job_count, expense_count no Account

---

## [1.2.0] - 2026-04-15

### Feat
- Usuários podem ter plano individual próprio
- Se usuário não tem plano pessoal, usa o plano da empresa
- Novos métodos no User: get_plan(), get_max_*, has_limit()
- Admin Django atualizado para gerenciar plano do usuário

### Fix
- Error handlers simplificados
- ALLOWED_HOSTS com fallback para produção

---

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
