"""Regras de alunos e matrículas, independentes do transporte HTTP."""
import datetime as dt
import os
import re
import secrets
import unicodedata


class Error(Exception):
    def __init__(self, status, motivo):
        self.status, self.motivo = status, motivo


def norm(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')


def now():
    return dt.datetime.fromisoformat(os.environ['ATENDE_AGORA']) if os.environ.get('ATENDE_AGORA') else dt.datetime.now().replace(second=0, microsecond=0)


def phone(value):
    if not isinstance(value, str) or re.search(r'[^\d+\s()\-]', value):
        raise Error(400, 'telefone_invalido')
    digits = re.sub(r'\D', '', value)
    if len(digits) in (12, 13) and digits.startswith('55'):
        digits = digits[2:]
    if len(digits) not in (10, 11):
        raise Error(400, 'telefone_invalido')
    return '+55' + digits


def require(body, fields):
    for field, kind in fields.items():
        if field not in body or type(body[field]) is not kind:
            raise Error(400, 'campo_invalido:' + field)
        if kind is str and not body[field].strip():
            raise Error(400, 'campo_invalido:' + field)


class Academia:
    def __init__(self, store):
        self.store = store

    def get(self, collection, identifier):
        item = self.store.get(collection, identifier)
        if item is None:
            raise Error(404, 'inexistente')
        return item

    def aluno(self, body, identifier=None):
        if identifier is None:
            require(body, {'nome': str, 'telefone': str})
        allowed = {'nome': str, 'telefone': str, 'email': str, 'nascimento': str,
                   'consentimento_marketing': bool, 'nao_contatar': bool}
        require(body, {k: t for k, t in allowed.items() if k in body})
        current = self.get('alunos', identifier) if identifier is not None else None
        changes = {k: v for k, v in body.items() if k in allowed}
        if 'telefone' in changes:
            changes['telefone'] = phone(changes['telefone'])
            duplicate = next((a for a in self.store.all('alunos') if a['telefone'] == changes['telefone']), None)
            if duplicate and (current is None or current['id'] != duplicate['id']):
                if current:
                    raise Error(409, 'telefone_duplicado')
                return 200, duplicate
        if current is None:
            used = {a['codigo'] for a in self.store.all('alunos')}
            while True:
                code = str(secrets.randbelow(90000000) + 10000000)
                if code not in used:
                    break
            current = dict(id=self.store.next_id('alunos'), codigo=code, email=None,
                           nascimento=None, consentimento_marketing=False, nao_contatar=False)
        current.update(changes)
        self.store.save('alunos', current)
        return (201 if identifier is None else 200), current

    def matricula_view(self, item):
        result = dict(item)
        situation = result.pop('situacao')
        result['status'] = 'vencida' if situation == 'ativa' and now().date().isoformat() > item['fim'] else situation
        return result

    def matricular(self, body):
        require(body, {'aluno_id': int, 'plano': str})
        self.get('alunos', body['aluno_id'])
        plan = self.get('planos', body['plano'])
        if not plan['ativo']:
            raise Error(422, 'plano_inativo')
        if 'inicio' in body:
            require(body, {'inicio': str})
        start = dt.date.fromisoformat(body.get('inicio', now().date().isoformat()))
        item = dict(id=self.store.next_id('matriculas'), aluno_id=body['aluno_id'], plano=plan['id'],
                    inicio=start.isoformat(), fim=(start + dt.timedelta(days=plan['vigencia_dias'] - 1)).isoformat(),
                    situacao='ativa', pagamento='pendente', aulas_restantes=plan.get('aulas'))
        self.store.save('matriculas', item)
        return self.matricula_view(item)

    def mudar_matricula(self, identifier, action, body):
        item = self.get('matriculas', identifier)
        if item['situacao'] == 'cancelada':
            raise Error(409, 'matricula_cancelada')
        if action == 'pagamento':
            require(body, {'pago': bool})
            item['pagamento'] = 'pago' if body['pago'] else 'pendente'
        elif action == 'trancar':
            if item['situacao'] == 'trancada':
                raise Error(409, 'matricula_trancada')
            item['situacao'] = 'trancada'
        elif action == 'destrancar':
            if item['situacao'] != 'trancada':
                raise Error(409, 'matricula_nao_trancada')
            item['situacao'] = 'ativa'
        elif action == 'cancelar':
            item.update(situacao='cancelada', cancelada_em=now().date().isoformat())
        else:
            raise Error(404, 'rota_inexistente')
        self.store.save('matriculas', item)
        return self.matricula_view(item)

    def ativa(self, aluno_id, date):
        """Seleção compartilhada para reservas e check-in nos próximos ciclos."""
        items = [m for m in self.store.all('matriculas') if m['aluno_id'] == aluno_id and m['situacao'] != 'cancelada']
        covers = [m for m in items if m['inicio'] <= date <= m['fim']]
        active = [m for m in covers if m['situacao'] == 'ativa']
        if active:
            return max(active, key=lambda m: (m['fim'], m['id']))
        raise Error(422, 'sem_matricula' if not items else 'matricula_trancada' if covers else 'matricula_vencida')
