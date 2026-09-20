# -*- coding: utf-8 -*-
import logging
from odoo import models, api, fields

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.model
    def _send_weekly_report(self):
        """Generate and send a weekly ecosystem report email."""
        # Read configuration from system parameters (fallbacks to defaults)
        ICP = self.env['ir.config_parameter'].sudo()
        recipient = ICP.get_param(
            'meu_assistente_ia.weekly_report_recipient',
            'denilsonfragoso1998@gmail.com'
        )
        sender = ICP.get_param(
            'meu_assistente_ia.weekly_report_sender',
            'denilsonfragoso1998@gmail.com'
        )

        projects = self.search([])
        total_tasks = self.env['project.task'].search_count([])

        lines = [
            "<h2 style='color:#714B67;'>Weekly AI Ecosystem Report</h2>",
            f"<p><strong>Generated:</strong> {fields.Datetime.now()}</p>",
            f"<p><strong>Total projects:</strong> {len(projects)}</p>",
            f"<p><strong>Total tasks:</strong> {total_tasks}</p>",
            "<h3 style='color:#714B67;'>Project Breakdown</h3>",
            "<ul>",
        ]

        for project in projects:
            tasks = self.env['project.task'].search([('project_id', '=', project.id)])
            no_stage = sum(1 for t in tasks if not t.stage_id)
            risk = (no_stage / len(tasks) * 100) if tasks else 0
            risk_label = "HIGH" if risk > 70 else "MEDIUM" if risk > 40 else "LOW"
            lines.append(
                f"<li><strong>{project.name}</strong>: {len(tasks)} tasks · "
                f"{no_stage} without stage · Risk: {risk_label} ({risk:.0f}%)</li>"
            )

        lines.append("</ul>")
        lines.append(
            "<p style='color:#9ca3af;font-size:0.85em;'>"
            "Generated automatically by AI Project Management Ecosystem v2.0"
            "</p>"
        )
        body_html = "".join(lines)

        _logger.info(
            f"[Weekly Report] Generated for {len(projects)} projects, {total_tasks} tasks"
        )

        mail = self.env['mail.mail'].create({
            'subject': f'Weekly AI Ecosystem Report — {fields.Date.today()}',
            'body_html': body_html,
            'email_to': recipient,
            'email_from': sender,
        })
        try:
            mail.send()
            _logger.info(f"[Weekly Report] Mail sent to {recipient}")
        except Exception as e:
            _logger.warning(f"[Weekly Report] Could not send mail: {e}")

        return True
