# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import request, Response

class SessionManager(http.Controller):

    @http.route('/assistente/sessions', type='http', auth='user', methods=['GET'], csrf=False)
    def list_sessions(self):
        """Return all chat sessions of the current user."""
        sessions = request.env['ai.session'].search([('user_id', '=', request.env.user.id)])
        data = [{
            'id': s.id,
            'name': s.name,
            'model_name': s.model_name,
            'create_date': s.create_date.isoformat() if s.create_date else None,
        } for s in sessions]
        return Response(json.dumps(data), content_type='application/json')

    @http.route('/assistente/sessions/create', type='http', auth='user', methods=['POST'], csrf=False)
    def create_session(self):
        """Create a new chat session."""
        data = json.loads(request.httprequest.data)
        name = data.get('name', 'New Chat')
        session = request.env['ai.session'].create({
            'name': name,
            'user_id': request.env.user.id,
            'model_name': data.get('model_name', 'groq'),
            'messages': json.dumps([]),
        })
        return Response(json.dumps({'id': session.id, 'name': session.name}), content_type='application/json')

    @http.route('/assistente/sessions/<int:session_id>', type='http', auth='user', methods=['GET'], csrf=False)
    def get_session(self, session_id):
        """Get messages of a session."""
        session = request.env['ai.session'].browse(session_id)
        if not session.exists() or session.user_id.id != request.env.user.id:
            return Response(json.dumps({'error': 'Session not found'}), status=404)
        return Response(json.dumps({
            'id': session.id,
            'name': session.name,
            'model_name': session.model_name,
            'messages': json.loads(session.messages or '[]'),
        }), content_type='application/json')

    @http.route('/assistente/sessions/<int:session_id>/messages', type='http', auth='user', methods=['POST'], csrf=False)
    def add_message(self, session_id):
        """Append a message to a session."""
        session = request.env['ai.session'].browse(session_id)
        if not session.exists() or session.user_id.id != request.env.user.id:
            return Response(json.dumps({'error': 'Session not found'}), status=404)
        data = json.loads(request.httprequest.data)
        messages = json.loads(session.messages or '[]')
        messages.append({'role': data.get('role', 'user'), 'content': data.get('content', '')})
        session.messages = json.dumps(messages)
        return Response(json.dumps({'status': 'ok'}), content_type='application/json')

    @http.route('/assistente/sessions/<int:session_id>/model', type='http', auth='user', methods=['POST'], csrf=False)
    def change_model(self, session_id):
        """Change the LLM model for a session."""
        session = request.env['ai.session'].browse(session_id)
        if not session.exists() or session.user_id.id != request.env.user.id:
            return Response(json.dumps({'error': 'Session not found'}), status=404)
        data = json.loads(request.httprequest.data)
        session.model_name = data.get('model_name', 'groq')
        return Response(json.dumps({'status': 'ok'}), content_type='application/json')
