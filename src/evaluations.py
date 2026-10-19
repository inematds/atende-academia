"""Agenda de avaliação física; resultados acessíveis apenas nas rotas da equipe."""
import datetime as dt
import math
import re

from .classes import Classes, DAYS
from .domain import Error, now, require


class Evaluations:
    def __init__(self, app):
        self.app, self.store = app, app.store

    def candidates(self, day, teacher):
        date = dt.date.fromisoformat(day)
        config = self.store.config
        if (day in config.get('feriados', []) or not teacher.get('ativo', True)
                or not teacher.get('avaliacao', False)):
            return []
        windows = teacher.get('horarios')
        if windows is None:
            windows = config['horarios']
        step = config['passo_min']
        duration = config['avaliacao_duracao_min']
        if step <= 0 or duration <= 0:
            raise Error(422, 'configuracao_de_horarios_invalida')
        earliest = now() + dt.timedelta(hours=config['avaliacao_antecedencia_horas'])
        result = set()
        for opening, closing in windows.get(DAYS[date.weekday()], []):
            start = dt.datetime.fromisoformat(day + 'T' + opening)
            end = dt.datetime.fromisoformat(day + 'T' + closing)
            while start + dt.timedelta(minutes=duration) <= end:
                if start >= earliest:
                    result.add(start)
                start += dt.timedelta(minutes=step)
        return sorted(result)

    def occupied(self, start, teacher_id):
        end = start + dt.timedelta(minutes=self.store.config['avaliacao_duracao_min'])
        def overlaps(item):
            return start < dt.datetime.fromisoformat(item['fim']) and dt.datetime.fromisoformat(item['inicio']) < end
        if any(a['professor'] == teacher_id and a['status'] in ('agendada', 'realizada')
               and overlaps(a) for a in self.store.all('avaliacoes')):
            return True
        classes = Classes(self.app)
        # Include the previous date for lessons crossing midnight.
        for lesson in self.store.all('grade'):
            if lesson['professor'] != teacher_id:
                continue
            for day in (start.date() - dt.timedelta(days=1), start.date()):
                occurrence = classes.occurrence(lesson, day.isoformat())
                if occurrence and not occurrence['cancelada'] and overlaps(occurrence):
                    return True
        return False

    def teachers(self, identifier=None):
        if identifier is not None:
            return [self.app.get('professores', identifier)]
        return sorted(self.store.all('professores'), key=lambda t: t['id'])

    def slots(self, query):
        day = query.get('data', [None])[0]
        if day is None:
            raise Error(400, 'data_obrigatoria')
        dt.date.fromisoformat(day)
        result = []
        for teacher in self.teachers(query.get('professor', [None])[0]):
            for start in self.candidates(day, teacher):
                if not self.occupied(start, teacher['id']):
                    result.append(dict(inicio=start.isoformat(timespec='minutes'), professor=teacher['id']))
        return sorted(result, key=lambda a: (a['inicio'], a['professor']))

    def schedule(self, body):
        require(body, {'aluno_id': int, 'inicio': str})
        if 'professor' in body:
            require(body, {'professor': str})
        self.app.get('alunos', body['aluno_id'])
        teachers = self.teachers(body.get('professor'))
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}', body['inicio']):
            raise Error(400, 'inicio_invalido')
        start = dt.datetime.fromisoformat(body['inicio'])
        eligible = [t for t in teachers if start in self.candidates(start.date().isoformat(), t)]
        if not eligible:
            raise Error(422, 'horario_invalido')
        teacher = next((t for t in eligible if not self.occupied(start, t['id'])), None)
        if teacher is None:
            raise Error(409, 'horario_ocupado')
        item = dict(id=self.store.next_id('avaliacoes'), aluno_id=body['aluno_id'],
                    professor=teacher['id'], inicio=body['inicio'],
                    fim=(start + dt.timedelta(minutes=self.store.config['avaliacao_duracao_min'])).isoformat(timespec='minutes'),
                    status='agendada', resultado=None)
        return self.store.save('avaliacoes', item)

    def change(self, identifier, action, body):
        item = self.app.get('avaliacoes', identifier)
        if action == 'cancelar':
            item['status'] = 'cancelada'
        else:
            for field in ('peso_kg', 'altura_cm'):
                value = body.get(field)
                if value is None:
                    raise Error(422, 'resultado_incompleto')
                if type(value) not in (float, int):
                    raise Error(400, 'campo_invalido:' + field)
                if not math.isfinite(value) or value <= 0:
                    raise Error(422, 'resultado_invalido')
            if 'gordura_pct' in body and type(body['gordura_pct']) not in (int, float):
                raise Error(400, 'campo_invalido:gordura_pct')
            require(body, {k: t for k, t in {'medidas': dict, 'observacoes': str}.items() if k in body})
            item['resultado'] = {k: body[k] for k in ('peso_kg', 'altura_cm', 'gordura_pct', 'medidas', 'observacoes') if k in body}
            item['status'] = 'realizada'
        return self.store.save('avaliacoes', item)

    def listing(self, student_id):
        self.app.get('alunos', student_id)
        return sorted((a for a in self.store.all('avaliacoes') if a['aluno_id'] == student_id),
                      key=lambda a: (a['inicio'], a['id']))
