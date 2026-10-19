"""Catálogo e fichas prescritas pela equipe; seleção determinística do treino."""
import re

from .domain import Error, now, require
from .store import ROOT


class Training:
    def __init__(self, app):
        self.app = app
        self.store = app.store

    def exercise(self, identifier):
        item = self.app.get('exercicios', identifier)
        for key in ('apelidos', 'passos', 'erros_comuns', 'cuidados'):
            item.setdefault(key, [])
        item.setdefault('grupo', '')
        # IDs são segmentos, nunca caminhos fornecidos pelo cliente.
        item['svg'] = bool(re.fullmatch(r'[\w-]+', identifier) and
                           (ROOT / 'web' / 'exercicios' / (identifier + '.svg')).is_file())
        return item

    def catalog(self):
        return [self.exercise(e['id']) for e in self.store.all('exercicios') if e['ativo']]

    def edit_exercise(self, method, body, identifier=None):
        if method == 'POST':
            require(body, {'id': str, 'nome': str, 'passos': list})
            identifier = body['id']
            if not re.fullmatch(r'[\w-]+', identifier):
                raise Error(400, 'id_invalido')
            if self.store.get('exercicios', identifier):
                raise Error(409, 'id_duplicado')
            item = dict(id=identifier, ativo=True, apelidos=[], grupo='',
                        erros_comuns=[], cuidados=[])
        else:
            item = self.app.get('exercicios', identifier)
            if method == 'DELETE':
                item['ativo'] = False
                self.store.save('exercicios', item)
                return 200, {'ativo': False}
        fields = dict(nome=str, grupo=str, apelidos=list, passos=list,
                      erros_comuns=list, cuidados=list, ativo=bool)
        require(body, {k: t for k, t in fields.items() if k in body})
        for key in ('apelidos', 'passos', 'erros_comuns', 'cuidados'):
            if key in body and any(type(s) is not str or not s.strip() for s in body[key]):
                raise Error(400, 'campo_invalido:' + key)
        item.update({k: v for k, v in body.items() if k in fields})
        if not item['passos']:
            raise Error(422, 'passos_vazios')
        self.store.save('exercicios', item)
        return (201 if method == 'POST' else 200), self.exercise(identifier)

    def ficha(self, identifier, method, body):
        self.app.get('alunos', identifier)
        if method == 'DELETE':
            self.store.delete('fichas', identifier)
            return 204, None
        if method == 'GET':
            return 200, {'treinos': self.app.get('fichas', identifier)['treinos']}
        require(body, {'treinos': list})
        if not body['treinos']:
            raise Error(422, 'treinos_vazios')
        workouts = []
        for workout in body['treinos']:
            if type(workout) is not dict:
                raise Error(400, 'treino_invalido')
            require(workout, {'nome': str, 'itens': list})
            if not workout['itens']:
                raise Error(422, 'itens_vazios')
            items = []
            for item in workout['itens']:
                if type(item) is not dict:
                    raise Error(400, 'item_invalido')
                require(item, {'exercicio': str, 'series': int, 'repeticoes': int})
                require(item, {k: t for k, t in {'carga': str, 'descanso_s': int}.items() if k in item})
                exercise = self.store.get('exercicios', item['exercicio'])
                if not exercise or not exercise['ativo']:
                    raise Error(422, 'exercicio_invalido')
                if item['series'] <= 0 or item['repeticoes'] <= 0:
                    raise Error(422, 'quantidade_invalida')
                items.append({k: item[k] for k in ('exercicio', 'series', 'repeticoes', 'carga', 'descanso_s') if k in item})
            workouts.append({'nome': workout['nome'], 'itens': items})
        self.store.save('fichas', {'id': identifier, 'treinos': workouts})
        return 200, {'treinos': workouts}

    def today(self, identifier):
        """Texto para a regra 13 do chat; não altera a ficha nem o check-in."""
        self.app.get('alunos', identifier)
        today = now().date().isoformat()
        try:
            self.app.ativa(identifier, today)
        except Error as exc:
            if exc.status != 422:
                raise
            return 'Confira seu plano com a recepção.'
        ficha = self.store.get('fichas', identifier)
        if ficha is None:
            return 'Peça sua ficha ao professor.'
        previous = {c['quando'][:10] for c in self.store.all('checkins')
                    if c['aluno_id'] == identifier and c['quando'][:10] < today}
        workout = ficha['treinos'][len(previous) % len(ficha['treinos'])]
        lines = ['Treino ' + workout['nome']]
        for item in workout['itens']:
            exercise = self.exercise(item['exercicio'])
            line = f"- {exercise['nome']}: {item['series']}x{item['repeticoes']}"
            if 'carga' in item:
                line += ', ' + item['carga']
            if 'descanso_s' in item:
                line += f", descanso {item['descanso_s']} s"
            lines.append(line)
        first = self.exercise(workout['itens'][0]['exercicio'])['nome']
        lines.append('Para ver como faz, peça: explica ' + first)
        return '\n'.join(lines)
