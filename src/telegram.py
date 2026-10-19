"""Atendimento interno pelo Telegram (seção 21), configurado exclusivamente pelo ambiente."""
import datetime as dt
import json
import os
import re
import urllib.error
import urllib.request

from .domain import Error, now


def configured():
    return all(os.environ.get(k) for k in ('TELEGRAM_API_URL', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID'))


def send(text, reply_to=None):
    """Envia ao grupo da equipe; devolve o message_id ou None (sem configuração ou falha)."""
    if not configured():
        return None
    payload = {'chat_id': os.environ['TELEGRAM_CHAT_ID'], 'text': text}
    if reply_to:
        payload['reply_to_message_id'] = reply_to
    request = urllib.request.Request(
        os.environ['TELEGRAM_API_URL'].rstrip('/') + '/bot' + os.environ['TELEGRAM_TOKEN'] + '/sendMessage',
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), method='POST',
        headers={'Content-Type': 'application/json'})

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=3) as response:
            data = json.loads(response.read() or b'{}')
        return (data.get('result') or {}).get('message_id')
    except (OSError, ValueError, AttributeError, urllib.error.URLError):
        return None


def stamp(value):
    return dt.datetime.fromisoformat(value).strftime('%d/%m %H:%M')


def opening(item, text):
    lines = [f"#{item['id']} Atendimento humano" + (' — ALTA' if item['prioridade'] == 'alta' else ''),
             f"Telefone: {item['telefone']}"]
    if item.get('nome'):
        lines.append(f"Nome: {item['nome']}")
    lines += [f"Motivo: {item['motivo']}", f"Última mensagem: {text}"]
    return '\n'.join(lines)


def remember(store, item, message_id):
    if message_id:
        item.setdefault('telegram_ids', []).append(message_id)
        store.save('atendimentos', item)


def lessons(app, day):
    from .classes import Classes
    try:
        dt.date.fromisoformat(day)
    except ValueError:
        return 'Data inválida. Use /aulas AAAA-MM-DD.'
    items = [o for o in Classes(app).occurrences({'data': [day]}) if not o['cancelada']]
    if not items:
        return f"{dt.date.fromisoformat(day).strftime('%d/%m')}: sem aulas."
    return '\n'.join(f"{o['inicio'][11:]} {o['modalidade']} ({o['professor']}) — {o['reservadas']}/{o['vagas']}"
                     for o in items)


def webhook(app, body):
    """Update do Telegram já autenticado pelo segredo; só o grupo da equipe tem efeito."""
    from .conversation import Conversation
    message = body.get('message')
    if not isinstance(message, dict):
        return {'ok': True}
    chat = message.get('chat') if isinstance(message.get('chat'), dict) else {}
    if str(chat.get('id')) != os.environ.get('TELEGRAM_CHAT_ID', ''):
        return {'ok': True}
    text = message.get('text')
    if not isinstance(text, str) or not text.strip():
        return {'ok': True}
    text = text.strip()
    store = app.store
    conversation = Conversation(app)
    if text.startswith('/'):
        parts = text.split(None, 2)
        command = parts[0].split('@', 1)[0].lower()
        if command == '/fila':
            open_items = [x for x in store.all('atendimentos') if x['status'] == 'aberto']
            send('\n'.join(f"#{x['id']} {x.get('nome') or x['telefone']} ({x['prioridade']}): {x['motivo']}"
                           for x in open_items) or 'Fila vazia.')
        elif command == '/aulas':
            send(lessons(app, parts[1] if len(parts) > 1 else now().date().isoformat()))
        elif command in ('/responder', '/encerrar'):
            identifier = parts[1].lstrip('#') if len(parts) > 1 else ''
            if not re.fullmatch(r'\d+', identifier) or (command == '/responder' and len(parts) < 3):
                send(f'Uso: {command} <id>' + (' <texto>' if command == '/responder' else ''))
                return {'ok': True}
            try:
                conversation.change_human(int(identifier), command[1:],
                                          {'texto': parts[2]} if command == '/responder' else {})
            except Error:
                send(f'Atendimento #{identifier} não encontrado.')
                return {'ok': True}
            if command == '/encerrar':
                send(f'#{identifier} encerrado. O bot volta a responder.')
        else:
            send('Comandos: /responder <id> <texto>, /encerrar <id>, /fila, /aulas [AAAA-MM-DD]')
        return {'ok': True}
    reply = message.get('reply_to_message')
    if isinstance(reply, dict) and reply.get('message_id') is not None:
        target = next((x for x in store.all('atendimentos') if reply['message_id'] in x.get('telegram_ids', [])), None)
        if target:
            conversation.change_human(target['id'], 'responder', {'texto': text})
    return {'ok': True}
