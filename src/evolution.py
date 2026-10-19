"""Transporte Evolution configurado exclusivamente pelo ambiente."""
import json
import os
import re
import urllib.error
import urllib.request

from .domain import Error, phone
from .exercise_pages import file_path


def send(telephone, text, exercise=None):
    base = os.environ.get('EVOLUTION_URL', '').rstrip('/')
    if not base:
        return 'simulado'
    payload = {'number': re.sub(r'\D', '', telephone), 'text': text}
    operation = 'sendText'
    public = os.environ.get('PUBLIC_URL', '').rstrip('/')
    if exercise and public:
        try:
            file_path(exercise, 'mp4')
        except (Error, OSError):
            pass
        else:
            operation = 'sendMedia'
            payload = dict(number=payload['number'], mediatype='video',
                           media=public + '/exercicios/' + exercise + '.mp4',
                           caption='\n'.join(line for line in text.splitlines()
                                             if not line.startswith('Veja a animação: ')))
    request = urllib.request.Request(
        base + '/message/' + operation + '/' + os.environ.get('EVOLUTION_INSTANCIA', ''),
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), method='POST',
        headers={'Content-Type': 'application/json', 'apikey': os.environ.get('EVOLUTION_API_KEY', '')})
    try:
        # Não seguir redirecionamentos com a credencial da integração.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None
        with urllib.request.build_opener(NoRedirect).open(request, timeout=3) as response:
            return 'enviado' if 200 <= response.status < 300 else 'pendente'
    except (OSError, ValueError, urllib.error.URLError):
        return 'pendente'


def deliver(store, item):
    if item.get('telefone') and item.get('texto'):
        item['status'] = send(item['telefone'], item['texto'])
    return store.save('saida', item)


def retry(store):
    count = 0
    for item in store.all('saida'):
        if item['status'] != 'pendente' or not item.get('telefone') or not item.get('texto'):
            continue
        student = store.get('alunos', item.get('aluno_id'))
        if item['tipo'] != 'humano' and student and student['nao_contatar']:
            continue
        deliver(store, item)
        count += item['status'] == 'enviado'
    return count


def webhook(app, body):
    from .conversation import Conversation
    if body.get('event') != 'messages.upsert':
        return {'ok': True}
    data = body.get('data')
    if not isinstance(data, dict):
        return {'ok': True}
    key = data.get('key')
    if not isinstance(key, dict):
        return {'ok': True}
    jid, identifier = key.get('remoteJid'), key.get('id')
    if (key.get('fromMe') or not isinstance(jid, str) or not jid.endswith('@s.whatsapp.net')
            or not isinstance(identifier, str) or not identifier
            or app.store.get('evolution_recebidas', identifier)):
        return {'ok': True}
    try:
        telephone = phone(jid.split('@', 1)[0])
    except Error:
        return {'ok': True}
    message = data.get('message') or {}
    text = message.get('conversation') if isinstance(message, dict) else None
    if not text and isinstance(message, dict):
        extended = message.get('extendedTextMessage')
        if isinstance(extended, dict):
            text = extended.get('text')
    app.store.save('evolution_recebidas', {'id': identifier})
    if not isinstance(text, str) or not text:
        send(telephone, 'Por enquanto só consigo ler mensagens de texto.')
    else:
        Conversation(app).receive({'telefone': telephone, 'texto': text}, whatsapp=True)
    return {'ok': True}
