"""Servidor HTTP concorrente; transações serializam mudanças no estado."""
import argparse
import hmac
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from .classes import Classes, filtered
from .attendance import Attendance
from .domain import Academia, Error, norm, require
from .store import ROOT, Store


def public(method, path, query):
    if method == 'POST':
        return path == '/api/mensagens'
    if method != 'GET':
        return False
    return (path in ('/', '/equipe', '/api/saude', '/api/planos', '/api/modalidades',
                     '/api/exercicios', '/api/avaliacoes/horarios')
            or path.startswith('/exercicios/') or path.startswith('/api/exercicios/')
            or (path == '/api/aulas' and 'data' in query and 'de' not in query and 'ate' not in query))


def route(app, method, path, query, body):
    store = app.store
    if method == 'GET' and path == '/api/saude':
        return 200, {'ok': True, 'versao': (ROOT / 'VERSION').read_text().strip()}
    classes = Classes(app)
    attendance = Attendance(app)
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
    if path == '/api/modalidades' and method == 'GET':
        return 200, {'modalidades': store.all('modalidades')}
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
            data = json.dumps(value, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def dispatch(self):
            try:
                parts = urlsplit(self.path)
                query = parse_qs(parts.query)
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
    args = parser.parse_args()
    app = Academia(Store(args.dados))
    server = ThreadingHTTPServer((args.host, args.porta), handler(app))
    print(f'PORTA={server.server_address[1]}', flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        app.store.db.close()
