"""Ocorrências semanais, reservas e espera; chamadas sob a transação do servidor."""
import datetime as dt

from .domain import Error, now, require

ACTIVE = ('reservada', 'presente', 'falta')
DAYS = ('seg', 'ter', 'qua', 'qui', 'sex', 'sab', 'dom')


def filtered(items, query, field='data'):
    start = query.get('data', query.get('de', ['0001-01-01']))[0]
    end = query.get('data', query.get('ate', ['9999-12-31']))[0]
    dt.date.fromisoformat(start)
    dt.date.fromisoformat(end)
    student = query.get('aluno_id', [None])[0]
    return [item for item in items if start <= item[field][:10] <= end
            and (student is None or item['aluno_id'] == int(student))]


class Classes:
    def __init__(self, app):
        self.app, self.store = app, app.store

    def occurrence(self, lesson, day):
        date = dt.date.fromisoformat(day)
        if not lesson['ativo'] or lesson['dia'] != DAYS[date.weekday()] or day in self.store.config.get('feriados', []):
            return None
        start = dt.datetime.fromisoformat(day + 'T' + lesson['hora'])
        canceled = self.store.get('ocorrencias_canceladas', lesson['id'] + ':' + day) is not None
        count = sum(r['status'] in ACTIVE and r['aula_id'] == lesson['id'] and r['data'] == day
                    for r in self.store.all('reservas'))
        return dict(aula_id=lesson['id'], data=day, inicio=start.isoformat(timespec='minutes'),
                    fim=(start + dt.timedelta(minutes=lesson['duracao_min'])).isoformat(timespec='minutes'),
                    modalidade=self.app.get('modalidades', lesson['modalidade'])['nome'],
                    professor=self.app.get('professores', lesson['professor'])['nome'],
                    sala=self.app.get('salas', lesson['sala'])['nome'], vagas=lesson['vagas'],
                    reservadas=count, livres=0 if canceled else lesson['vagas'] - count, cancelada=canceled)

    def occurrences(self, query):
        start = query.get('data', query.get('de', [None]))[0]
        end = query.get('data', query.get('ate', [None]))[0]
        if start is None or end is None:
            raise Error(400, 'data_obrigatoria')
        day, last = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
        result = []
        while day <= last:
            for lesson in self.store.all('grade'):
                occurrence = self.occurrence(lesson, day.isoformat())
                if occurrence:
                    result.append(occurrence)
            if day == last:
                break
            day += dt.timedelta(days=1)
        return sorted(result, key=lambda o: (o['inicio'], o['aula_id']))

    def reserve(self, body):
        require(body, {'aluno_id': int, 'aula_id': str, 'data': str})
        self.app.get('alunos', body['aluno_id'])
        lesson = self.app.get('grade', body['aula_id'])
        occurrence = self.occurrence(lesson, body['data'])
        if not occurrence or occurrence['cancelada']:
            raise Error(422, 'sem_aula')
        instant = now()
        if dt.datetime.fromisoformat(occurrence['inicio']) <= instant:
            raise Error(422, 'aula_passada')
        if dt.date.fromisoformat(body['data']) > instant.date() + dt.timedelta(days=self.store.config['reserva_antecedencia_dias']):
            raise Error(422, 'antecedencia')
        enrollment = self.app.ativa(body['aluno_id'], body['data'])
        if enrollment['aulas_restantes'] == 0:
            raise Error(422, 'sem_aulas')
        if any(r['aluno_id'] == body['aluno_id'] and r['aula_id'] == lesson['id'] and r['data'] == body['data']
               and r['status'] in ACTIVE for r in self.store.all('reservas')):
            raise Error(409, 'ja_reservada')
        if occurrence['reservadas'] >= occurrence['vagas']:
            raise Error(409, 'lotada')
        if enrollment['aulas_restantes'] is not None:
            enrollment['aulas_restantes'] -= 1
            self.store.save('matriculas', enrollment)
        reservation = dict(id=self.store.next_id('reservas'), aluno_id=body['aluno_id'], aula_id=lesson['id'],
                           data=body['data'], inicio=occurrence['inicio'], fim=occurrence['fim'],
                           modalidade=occurrence['modalidade'], matricula_id=enrollment['id'], status='reservada')
        self.store.save('reservas', reservation)
        return dict(reservation, aulas_restantes=enrollment['aulas_restantes'])

    def reservations(self, query):
        result = []
        for reservation in filtered(self.store.all('reservas'), query):
            student = self.app.get('alunos', reservation['aluno_id'])
            result.append(dict(reservation, nome=student['nome'], telefone=student['telefone']))
        return sorted(result, key=lambda r: (r['inicio'], r['id']))

    def refund(self, reservation):
        enrollment = self.app.get('matriculas', reservation['matricula_id'])
        if enrollment['aulas_restantes'] is not None:
            enrollment['aulas_restantes'] += 1
            self.store.save('matriculas', enrollment)

    def message(self, student_id, kind, text, reference, instant=None):
        student = self.app.get('alunos', student_id)
        if student['nao_contatar']:
            return None
        return self.store.save('saida', dict(id=self.store.next_id('saida'), tipo=kind, aluno_id=student_id,
                               telefone=student['telefone'], texto=text, referencia_id=reference,
                               quando=(instant or now()).isoformat(timespec='minutes'), status='simulado'))

    def offer(self, reservation):
        for request in self.store.all('espera'):
            if (request['status'] == 'pendente' and request['aula_id'] == reservation['aula_id']
                    and request['data'] == reservation['data']):
                stamp = dt.datetime.fromisoformat(reservation['inicio']).strftime('%d/%m %H:%M')
                if self.message(request['aluno_id'], 'espera', f'Uma vaga em {stamp}. Responda 1 para reservar.', request['id']):
                    request['status'] = 'ofertado'
                    self.store.save('espera', request)
                    break

    def change(self, identifier, action, body):
        reservation = self.app.get('reservas', identifier)
        if action == 'presenca':
            require(body, {'compareceu': bool})
            if reservation['status'] not in ACTIVE:
                raise Error(409, 'reserva_inativa')
            reservation['status'] = 'presente' if body['compareceu'] else 'falta'
        else:
            if reservation['status'] != 'reservada':
                raise Error(409, 'reserva_inativa')
            timely = now() + dt.timedelta(hours=self.store.config['cancelamento_prazo_horas']) <= dt.datetime.fromisoformat(reservation['inicio'])
            reservation['status'] = 'cancelada' if timely else 'cancelada_tarde'
            if timely:
                self.refund(reservation)
            self.offer(reservation)
        self.store.save('reservas', reservation)
        return {'status': reservation['status']}

    def cancel_occurrence(self, identifier, day, body):
        lesson = self.app.get('grade', identifier)
        occurrence = self.occurrence(lesson, day)
        if occurrence is None:
            raise Error(404, 'ocorrencia_inexistente')
        if occurrence['cancelada']:
            raise Error(409, 'ocorrencia_cancelada')
        if 'motivo' in body:
            require(body, {'motivo': str})
        self.store.save('ocorrencias_canceladas', dict(id=identifier + ':' + day, motivo=body.get('motivo')))
        count = 0
        stamp = dt.datetime.fromisoformat(occurrence['inicio']).strftime('%d/%m %H:%M')
        for reservation in self.store.all('reservas'):
            if reservation['aula_id'] == identifier and reservation['data'] == day and reservation['status'] == 'reservada':
                reservation['status'] = 'cancelada_pela_academia'
                self.refund(reservation)
                self.store.save('reservas', reservation)
                self.message(reservation['aluno_id'], 'aula_cancelada', f"Aula {occurrence['modalidade']} em {stamp} cancelada.", reservation['id'])
                self.offer(reservation)
                count += 1
        return {'canceladas': count}

    def wait(self, body):
        require(body, {'aluno_id': int, 'aula_id': str, 'data': str})
        self.app.get('alunos', body['aluno_id'])
        self.app.get('grade', body['aula_id'])
        dt.date.fromisoformat(body['data'])
        item = dict(id=self.store.next_id('espera'), aluno_id=body['aluno_id'], aula_id=body['aula_id'],
                    data=body['data'], status='pendente')
        self.store.save('espera', item)
        return {'id': item['id']}
