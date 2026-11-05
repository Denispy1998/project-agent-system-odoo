from odoo import models, fields

class AiTemplate(models.Model):
    _name = 'ai.template'
    _description = 'AI Agent Template'
    _order = 'name'

    name = fields.Char(string='Template Name', required=True)
    workspace_id = fields.Many2one('project.project', string='Workspace', ondelete='cascade', 
                                   help="The Workspace (Project) this agent belongs to.")
    description = fields.Text(string='Description')
    
    prompt_template = fields.Text(string='System Prompt', required=True,
                                  help="The system prompt that defines the agent's persona and rules.")
    
    # NOVO: Guardrails
    guardrails = fields.Text(string='Guardrails (Safety Rules)', 
                             help="Specific restrictions or safety rules (e.g., 'Do not delete projects', 'Only answer in English').")
    
    model_name = fields.Selection([
        ('groq', 'Groq (qwen3.8-27b)'),
        ('openai', 'OpenAI (GPT-4o)'),
        ('anthropic', 'Anthropic (Claude 3.5)')
    ], string='LLM Provider', default='groq', required=True)
    
    # NOVOS: Parâmetros do LLM
    temperature = fields.Float(string='Temperature', default=0.0, 
                               help="Controls randomness. 0.0 is deterministic, 1.0 is very creative.")
    max_tokens = fields.Integer(string='Max Tokens', default=512)
    
    max_iterations = fields.Integer(string='Max Iterations', default=1)
    active = fields.Boolean(string='Active', default=True)
