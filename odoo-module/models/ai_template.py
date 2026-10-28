from odoo import models, fields

class AiTemplate(models.Model):
    _name = 'ai.template'
    _description = 'AI Agent Template'
    _order = 'name'

    name = fields.Char(string='Template Name', required=True)
    description = fields.Text(string='Description')
    prompt_template = fields.Text(string='System Prompt', required=True, 
                                  help="The system prompt that defines the agent's persona and rules.")
    model_name = fields.Selection([
        ('groq', 'Groq (qwen3.8-27b)'),
        ('openai', 'OpenAI (GPT-4o)'),
        ('anthropic', 'Anthropic (Claude 3.5)')
    ], string='LLM Provider', default='groq', required=True)
    max_iterations = fields.Integer(string='Max Iterations', default=1)
    active = fields.Boolean(string='Active', default=True)
