# CHANGELOG TÉCNICO - ECOSSISTEMA MULTIAGENTE

Este documento cataloga os casos técnicos (T1-T11) de problemas encontrados, soluções aplicadas e lições aprendidas ao longo do desenvolvimento do ecossistema (v2.1 até v2.9.4).

## Casos Técnicos

### T1: Ownership de Tabelas PostgreSQL
*   **Problema:** Erros de permissão após migração. 297 tabelas do Odoo estavam sobre a posse do utilizador `postgres` em vez de `denispy`.
*   **Solução:** Uso de `ALTER TABLE ... OWNER TO denispy`.
*   **Lição:** Verificar sempre as permissões de base de dados ao migrar ambientes.

### T2: Remoção de Campos no `ir.cron`
*   **Problema:** Odoo 19 removeu os campos `numbercall` e `doall` do modelo `ir.cron`.
*   **Solução:** Adaptação do XML de dados para a nova estrutura do Odoo 19.

### T3: `ir.cron` `name` é JSONB
*   **Problema:** Queries SQL diretas ao nome do cron falhavam.
*   **Solução:** Uso do ORM (`odoo-bin shell`) para criar e ler os crons.

### T4: Recuperação de Filestore
*   **Problema:** Filestore corrompido após formatação.
*   **Solução:** Recuperação e regeneração de assets com o comando `-u web`.

### T5: `project.task.user_id` não existe
*   **Problema:** O campo era usado para atribuir tarefas, mas não existe nativamente.
*   **Solução:** Uso de `user_ids` (Many2many) e `create_uid`.

### T6: Regex Ganancioso (`re.sub`)
*   **Problema:** Uso de `re.sub` apagou 172 linhas de código no `chatbot.py` e funções vitais do `odoo_tools.py`.
*   **Solução:** Proibição de `re.sub` ganancioso. Uso exclusivo de substituições literais (`str.replace`) e validação com `py_compile`.
*   **Lição:** Nunca usar regex complexo em ficheiros grandes.

### T7: Palavras Reservadas RSL/ASL
*   **Problema:** O parser ITLingoCloud rejeitava palavras como `Active`, `Login`, `Role`, `Status`.
*   **Solução:** Uso de prefixos e adaptações estruturais documentadas.

### T8: RBAC Write Keywords
*   **Problema:** Fuzzing audit revelou que verbos como `setup`, `simulate` e `bulk` não estavam no `write_keywords` do PermissionGuard.
*   **Solução:** Adição dos verbos ao guard e aos testes unitários.

### T9: Falsos Positivos de SUCCESS/ERROR
*   **Problema:** `create_project` retornava `SUCCESS` em duplicados; `delete_task` retornava `SUCCESS` se não encontrasse a tarefa.
*   **Solução:** Correção das ferramentas para retornar `INFO` (duplicados) ou `ERROR` (não encontrado).

### T10: Rate Limit da Groq (Free Tier)
*   **Problema:** O envio de prompts grandes (muitas ferramentas e contexto) esgotava os 7000 TPM (Tokens Por Minuto) da Groq, causando falhas durante testes ou demonstrações.
*   **Solução:** Implementação de um sistema de cache em memória no FastAPI (`CACHE_DB` com TTL de 5 minutos) e otimização do prompt de erro.

### T11: Otimização de Agentes (v2.9.4)
*   **Problema:** Os agentes (especialmente o Project Manager) enviavam a documentação de 17 ferramentas para o LLM em cada pedido, consumindo demasiados tokens.
*   **Solução:** Remoção das ferramentas de CRUD básico (já tratadas pelo Router Local via regex) do contexto do LLM. O Project Manager passou de 17 para 8 ferramentas. O Agente de Riscos e Planeamento passaram de 4 para 2. O `verbose` foi desligado.
*   **Resultado:** Redução de ~70% no consumo de tokens por pedido.

---
## Notas de Versão (Histórico)

*   **v2.9.4 (02/Nov/2026):** Otimização de agentes para o Groq Free Tier. Implementação de Cache no FastAPI. Limpeza de 20 projetos de teste na DB. Ruff 0 warnings.
*   **v2.9.3 (30/Out/2026):** Correção do CI (`test_patterns_count_stable`).
*   **v2.9.2 (29/Out/2026):** Fuzzing audit. Fix de SUCCESS/ERROR. RBAC write_keywords.
*   **v2.9.0/2.9.1:** Refactor e limpeza cirúrgica.
*   **v2.8.0:** Agentes de Planeamento e Riscos. BackOffice.

### T12: Substituição de `print()` por Logging
* **Problema:** O uso de `print()` poluía a consola e não permitia categorizar a severidade (Info, Warning, Error).
* **Solução:** Implementação de `import logging` e `_logger`. Logs estruturados para produção.

### T13: Otimização `read_group` para `_read_group` (Odoo 19)
* **Problema:** O método `read_group` foi descontinuado no Odoo 19 (emitia warnings).
* **Solução:** Atualização do `dashboard_utils.py` para a sintaxe nativa `_read_group(aggregates=['id:count'])`.
