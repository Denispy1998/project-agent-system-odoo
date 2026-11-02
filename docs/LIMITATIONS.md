# LIMITAÇÕES CONHECIDAS DO ECOSSISTEMA

Estas limitações estão documentadas de forma honesta para garantir o rigor científico da dissertação e orientar o trabalho futuro.

*   **L1 — Permission guard e XML-RPC:** A verificação server-side está implementada (v2.5), mas o XML-RPC ainda usa as credenciais `admin/admin` definidas no `.env`. Um atacante com acesso shell à máquina pode contornar o RBAC. *Nota:* O Odoo 19 emite um aviso de depreciação do XML-RPC (removerão no Odoo 22). A migração para JSON-RPC ou autenticação por sessão no microserviço (FastAPI) eliminará esta limitação no futuro.
*   **L2 — Testes unit e smoke sem integração pytest completa em CI:** Apenas o Lint e o Pytest unit correm em CI (GitHub Actions). A certificação end-to-end (`certify.py`) e os testes de fuzzing correm manualmente.
*   **L3 — Cache de roles:** O cache de verificação de roles tem um TTL de 60s. Outras leituras recorrentes ao Odoo não estão em cache.
*   **L4 — Filestore parcialmente limpo:** 12 assets órfãos foram removidos em v2.6.0; 6 registos foram mantidos por precaução.
*   **L5 — Rate limits do Groq (Plano Gratuito):** O plano gratuito da Groq tem um limite de 7.000 tokens/minuto (TPM). Isto foi mitigado através de: (i) router híbrido local (~90% dos comandos não usam LLM); (ii) backoff exponencial; (iii) **Cache de respostas em memória no FastAPI com TTL de 5 minutos (novo em v2.9.4)**; e (iv) **redução drástica do número de ferramentas injetadas no prompt dos agentes (novo em v2.9.4)**.
*   **L6 — RSL/ASL são documentação, não geram código:** As especificações RSL v3.2 e ASL v3.3 estão validadas no ITLingoCloud com 0 erros, mas não são consumidas por geradores automáticos.
*   **L7 — UI server-rendered (f-strings Python):** O deployment é trivial, mas a alteração de HTML/CSS requer a modificação das f-strings no `chatbot.py`.
*   **L8 — Ficheiros Docker são artefactos de referência:** Os ficheiros `Dockerfile.agents` e `docker-compose` não foram testados end-to-end; o deployment primário é a execução direta em WSL2.
