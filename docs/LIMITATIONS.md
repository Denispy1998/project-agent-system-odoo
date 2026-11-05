# Limitações Conhecidas do Ecossistema

Estas limitações estão documentadas de forma honesta para garantir o rigor científico da dissertação e orientar o trabalho futuro.

* **L1 — Permission guard e XML-RPC:** A verificação server-side está implementada (v2.5), mas o XML-RPC ainda usa as credenciais `admin/admin` definidas no `.env`. *Nota:* O Odoo 19 emite um aviso de depreciação do XML-RPC (removerão no Odoo 22). A migração para JSON-RPC ou autenticação por sessão no microserviço (FastAPI) eliminará esta limitação no futuro. A ligação foi tornada *Thread-Safe* com `threading.local()`, mas continua a usar as credenciais globais.
* **L2 — Testes unit e smoke sem integração pytest completa em CI:** Apenas o Lint e o Pytest unit correm em CI (GitHub Actions). A certificação end-to-end (`certify.py`) e os testes de fuzzing correm manualmente.
* **L3 — Cache de respostas:** O FastAPI tem um cache em memória (TTL de 5 min) e agora **invalida o cache automaticamente** após qualquer operação de escrita (create, update, delete), garantindo consistência. No entanto, não é um cache distribuído (ex: Redis), pelo que não escala para múltiplos workers uvicorn.
* **L4 — Filestore parcialmente limpo:** 12 assets órfãos foram removidos em v2.6.0; 6 registos foram mantidos por precaução.
* **L5 — Rate limits do Groq (Plano Gratuito):** O plano gratuito da Groq tem um limite de 7.000 tokens/minuto (TPM). Isto foi mitigado através de: (i) router híbrido local; (ii) backoff exponencial; (iii) **Cache de respostas**; (iv) **redução do número de ferramentas injetadas no prompt**; e (v) **validação de input (max 2000 caracteres)** para evitar gastos desnecessários de tokens.
* **L6 — RSL/ASL são documentação, não geram código:** As especificações RSL v3.2 e ASL v3.3 estão validadas no ITLingoCloud com 0 erros, mas não são consumidas por geradores automáticos.
* **L7 — UI server-rendered (f-strings Python):** O deployment é trivial, mas a alteração de HTML/CSS requer a modificação das f-strings no `chatbot.py`.
* **L8 — Ficheiros Docker são artefactos de referência:** Os ficheiros `Dockerfile.agents` e `docker-compose` não foram testados end-to-end; o deployment primário é a execução direta em WSL2.
