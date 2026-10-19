"""Servidor HTTP concorrente; transações serializam mudanças no estado."""
import argparse
import hmac
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from .evolution import webhook
from . import telegram
from .backup import backup, restore
from .catalogs import catalog
from .privacy import Privacy
from .raiox import report, update
from .conversation import Conversation
from .classes import Classes, filtered
from .attendance import Attendance
from .training import Training
from .evaluations import Evaluations
from .exercise_pages import Resource, exercise_resource
from .domain import Academia, Error, norm, require
from .store import ROOT, Store


def public(method, path, query):
    if method == 'POST':
        return path in ('/api/mensagens', '/webhook/telegram') or path.startswith('/webhook/evolution/')
    if method != 'GET':
        return False
    return (path in ('/', '/equipe', '/api/saude', '/api/planos', '/api/modalidades',
                     '/api/exercicios', '/api/avaliacoes/horarios')
            or path.startswith('/exercicios/') or path.startswith('/api/exercicios/')
            or (path == '/api/aulas' and 'data' in query and 'de' not in query and 'ate' not in query))


def route(app, method, path, query, body):
    store = app.store
    if method == 'POST' and path.startswith('/webhook/evolution/'):
        return 200, webhook(app, body)
    if method == 'POST' and path == '/webhook/telegram':
        return 200, telegram.webhook(app, body)
    if method == 'GET' and path in ('/', '/equipe'):
        page = 'index.html' if path == '/' else 'equipe.html'
        return 200, Resource((ROOT / 'web' / page).read_bytes(), 'text/html; charset=utf-8')
    match = re.fullmatch(r'/api/(professores|grade|faq|modalidades|salas)(?:/([\w-]+))?', path)
    if match:
        return catalog(app, match[1], match[2], method, body)
    if method == 'GET' and path.startswith('/exercicios/'):
        return 200, exercise_resource(app, path)
    if method == 'GET' and path == '/api/saude':
        return 200, {'ok': True, 'versao': (ROOT / 'VERSION').read_text().strip()}
    privacy = Privacy(app)
    if path == '/api/campanhas' and method == 'POST':
        return privacy.campaign(body)
    if path == '/api/raiox' and method == 'GET':
        return 200, report(app, query.get('mes', [''])[0])
    match = re.fullmatch(r'/api/alunos/(\d+)/dados', path)
    if match and method == 'GET':
        return 200, privacy.export(int(match[1]))
    match = re.fullmatch(r'/api/alunos/(\d+)', path)
    if match and method == 'DELETE':
        privacy.anonymize(int(match[1]))
        return 204, None
    conversation = Conversation(app)
    if path == "/api/mensagens" and method == "POST":
        return 200, conversation.receive(body)
    if path == "/api/atendimento-humano" and method == "GET":
        return 200, {"fila": [x for x in store.all("atendimentos") if x["status"] == "aberto"]}
    match = re.fullmatch(r"/api/atendimento-humano/(\d+)/(responder|encerrar)", path)
    if match and method == "POST":
        return 200, conversation.change_human(int(match[1]), match[2], body)
    classes = Classes(app)
    attendance = Attendance(app)
    training = Training(app)
    evaluations = Evaluations(app)
    if path == '/api/avaliacoes/horarios' and method == 'GET':
        return 200, {'horarios': evaluations.slots(query)}
    if path == '/api/avaliacoes' and method == 'POST':
        return 201, evaluations.schedule(body)
    match = re.fullmatch(r'/api/avaliacoes/(\d+)/(cancelar|resultado)', path)
    if match and method == 'POST':
        return 200, evaluations.change(int(match[1]), match[2], body)
    match = re.fullmatch(r'/api/alunos/(\d+)/avaliacoes', path)
    if match and method == 'GET':
        return 200, {'avaliacoes': evaluations.listing(int(match[1]))}
    match = re.fullmatch(r'/api/exercicios(?:/([\w-]+))?', path)
    if match:
        identifier = match[1]
        if method == 'GET':
            return 200, training.exercise(identifier) if identifier else {'exercicios': training.catalog()}
        if (method == 'POST' and identifier is None) or (method in ('PUT', 'DELETE') and identifier is not None):
            return training.edit_exercise(method, body, identifier)
    match = re.fullmatch(r'/api/alunos/(\d+)/ficha', path)
    if match and method in ('GET', 'PUT', 'DELETE'):
        return training.ficha(int(match[1]), method, body)
    if path == '/api/checkins':
        if method == 'POST':
            return attendance.checkin(body)
        if method == 'GET':
            return 200, {'checkins': attendance.listing(query)}
    if path == '/api/tarefas/rodar' and method == 'POST':
        return 200, attendance.run(body)
    if path == '/api/aulas' and method == 'GET':
        return 200, {'aulas': classes.occurrences(query)}
    if path == '/api/reservas':
        if method == 'POST':
            return 201, classes.reserve(body)
        if method == 'GET':
            return 200, {'reservas': classes.reservations(query)}
    match = re.fullmatch(r'/api/reservas/(\d+)/(cancelar|presenca)', path)
    if match and method == 'POST':
        return 200, classes.change(int(match[1]), match[2], body)
    match = re.fullmatch(r'/api/aulas/([\w-]+)/ocorrencias/([0-9-]+)/cancelar', path)
    if match and method == 'POST':
        return 200, classes.cancel_occurrence(match[1], match[2], body)
    if path == '/api/espera':
        if method == 'POST':
            return 201, classes.wait(body)
        if method == 'GET':
            return 200, {'espera': filtered(store.all('espera'), query)}
    if path == '/api/saida' and method == 'GET':
        return 200, {'mensagens': store.all('saida')}
    if path == '/api/alunos':
        if method == 'POST':
            status, aluno = app.aluno(body)
            return status, {k: aluno[k] for k in ('id', 'codigo')}
        if method == 'GET':
            search = norm(query.get('busca', [''])[0])
            digits = re.sub(r'\D', '', search)
            items = [a for a in store.all('alunos') if not search or search in norm(a['nome'])
                     or (digits and digits in (a['telefone'] or '')) or search == a['codigo']]
            return 200, {'alunos': items}
    match = re.fullmatch(r'/api/alunos/(\d+)(?:/(matriculas))?', path)
    if match:
        identifier = int(match[1])
        app.get('alunos', identifier)
        if method == 'PUT' and not match[2]:
            return app.aluno(body, identifier)
        if method == 'GET' and match[2] == 'matriculas':
            return 200, {'matriculas': [app.matricula_view(m) for m in store.all('matriculas') if m['aluno_id'] == identifier]}
    if path == '/api/matriculas' and method == 'POST':
        return 201, app.matricular(body)
    match = re.fullmatch(r'/api/matriculas/(\d+)/(pagamento|trancar|destrancar|cancelar)', path)
    if match and method == 'POST':
        return 200, app.mudar_matricula(int(match[1]), match[2], body)
    match = re.fullmatch(r'/api/planos(?:/([\w-]+))?', path)
    if match:
        identifier = match[1]
        if method == 'GET' and identifier is None:
            return 200, {'planos': [p for p in store.all('planos') if p['ativo']]}
        if method == 'POST' and identifier is None:
            require(body, {'id': str, 'nome': str, 'vigencia_dias': int})
            if store.get('planos', body['id']):
                raise Error(409, 'id_duplicado')
            item = dict(id=body['id'], ativo=True, aulas=None)
        elif identifier is not None and method in ('PUT', 'DELETE'):
            item = app.get('planos', identifier)
            if method == 'DELETE':
                item['ativo'] = False
                store.save('planos', item)
                return 200, {'ativo': False}
        else:
            raise Error(404, 'rota_inexistente')
        require(body, {k: t for k, t in {'nome': str, 'vigencia_dias': int, 'ativo': bool}.items() if k in body})
        item.update({k: v for k, v in body.items() if k in ('nome', 'preco', 'vigencia_dias', 'aulas', 'ativo')})
        if type(item.get('preco')) not in (int, float) or item['preco'] < 0:
            raise Error(400, 'preco_invalido')
        if item['vigencia_dias'] <= 0 or (item['aulas'] is not None and (type(item['aulas']) is not int or item['aulas'] <= 0)):
            raise Error(422, 'plano_invalido')
        store.save('planos', item)
        return (201 if method == 'POST' else 200), item
    raise Error(404, 'rota_inexistente')


def handler(app):
    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, value):
            if isinstance(value, Resource):
                data, content_type = value.content, value.content_type
            else:
                data = b'' if status == 204 else json.dumps(value, ensure_ascii=False).encode('utf-8')
                content_type = 'application/json; charset=utf-8'
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def dispatch(self):
            try:
                parts = urlsplit(self.path)
                query = parse_qs(parts.query)
                if parts.path.startswith('/webhook/evolution/'):
                    secret = os.environ.get('WEBHOOK_SEGREDO', '')
                    supplied = parts.path.removeprefix('/webhook/evolution/')
                    if not secret or not hmac.compare_digest(secret.encode(), supplied.encode()):
                        raise Error(404, 'rota_inexistente')
                if parts.path == '/webhook/telegram':
                    secret = os.environ.get('TELEGRAM_SEGREDO', '')
                    supplied = self.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
                    if not secret or not hmac.compare_digest(secret.encode(), supplied.encode()):
                        raise Error(401, 'nao_autorizado')
                if not public(self.command, parts.path, query):
                    expected = str(app.store.config['token']).encode()
                    actual = self.headers.get('X-Token', '').encode()
                    if not actual or not hmac.compare_digest(actual, expected):
                        raise Error(401, 'nao_autorizado')
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 <= length <= 1048576:
                    raise Error(400, 'corpo_grande')
                body = json.loads(self.rfile.read(length)) if length else {}
                if not isinstance(body, dict):
                    raise Error(400, 'objeto_json_obrigatorio')
                with app.store.lock, app.store.db:
                    status, result = route(app, self.command, parts.path, query, body)
                self.respond(status, result)
            except Error as exc:
                self.respond(exc.status, {'motivo': exc.motivo})
            except (ValueError, TypeError):
                self.respond(400, {'motivo': 'entrada_invalida'})

        do_GET = do_POST = do_PUT = do_DELETE = dispatch

        def log_message(self, *args):
            pass
    return Handler


def main():
    parser = argparse.ArgumentParser(description='Atendimento ao aluno de academia')
    commands = parser.add_subparsers(dest='command', required=True)
    serve = commands.add_parser('serve')
    serve.add_argument('--porta', type=int, default=8080)
    serve.add_argument('--host', default='127.0.0.1')
    serve.add_argument('--dados', required=True)
    raiox = commands.add_parser('raiox')
    raiox.add_argument('--dados', required=True)
    raiox.add_argument('--mes', required=True)
    raiox.add_argument('--acompanhamento', required=True)
    for name, flag in (("backup", "--saida"), ("restaurar", "--entrada")):
        command = commands.add_parser(name)
        command.add_argument("--dados", required=True)
        command.add_argument(flag, required=True)
    args = parser.parse_args()
    if args.command in ("backup", "restaurar"):
        try:
            if args.command == "backup":
                backup(args.dados, args.saida)
            else:
                restore(args.dados, args.entrada)
        except (OSError, ValueError, KeyError) as exc:
            parser.exit(1, f"falhou: {exc}\n")
        return
    app = Academia(Store(args.dados))
    if args.command == 'raiox':
        try:
            with app.store.lock, app.store.db:
                update(app, args.mes, args.acompanhamento)
        finally:
            app.store.db.close()
        return
    server = ThreadingHTTPServer((args.host, args.porta), handler(app))
    print(f'PORTA={server.server_address[1]}', flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        app.store.db.close()
