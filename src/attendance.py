"""Check-ins e tarefas locais; o relógio da rodada não altera o do processo."""
import datetime as dt

from .evolution import retry
from .classes import Classes, filtered
from .domain import Error, now, require


class Attendance:
    def __init__(self, app):
        self.app, self.store = app, app.store

    def view(self, item):
        return dict(item, nome=self.app.get('alunos', item['aluno_id'])['nome'])

    def checkin(self, body):
        require(body, {'codigo': str})
        student = next((s for s in self.store.all('alunos') if s['codigo'] == body['codigo']), None)
        if student is None:
            raise Error(404, 'codigo_inexistente')
        instant = now()
        today = instant.date().isoformat()
        self.app.ativa(student['id'], today)
        for item in self.store.all('checkins'):
            if item['aluno_id'] == student['id'] and item['quando'][:10] == today:
                return 200, self.view(item)
        item = dict(id=self.store.next_id('checkins'), aluno_id=student['id'],
                    quando=instant.isoformat(timespec='minutes'))
        self.store.save('checkins', item)
        return 201, self.view(item)

    def listing(self, query):
        items = filtered(self.store.all('checkins'), query, 'quando')
        return [self.view(item) for item in sorted(items, key=lambda i: (i['quando'], i['id']))]

    def run(self, body):
        if 'agora' in body:
            require(body, {'agora': str})
        instant = dt.datetime.fromisoformat(body['agora']) if 'agora' in body else now()
        if instant.tzinfo is not None:
            raise Error(400, 'agora_sem_fuso_obrigatorio')
        resent = retry(self.store)
        today = instant.date()
        classes = Classes(self.app)
        created = marked = 0
        checkins = self.store.all('checkins')
        attended = {(c['aluno_id'], c['quando'][:10]) for c in checkins}
        for reservation in self.store.all('reservas'):
            if reservation['status'] != 'reservada':
                continue
            end = dt.datetime.fromisoformat(reservation['fim'])
            if end <= instant:
                reservation['status'] = 'presente' if (reservation['aluno_id'], reservation['data']) in attended else 'falta'
                self.store.save('reservas', reservation)
                marked += 1

        messages = self.store.all('saida')
        warned = {(m['tipo'], m['referencia_id']) for m in messages}
        for enrollment in self.store.all('matriculas'):
            end = dt.date.fromisoformat(enrollment['fim'])
            if (enrollment['situacao'] == 'ativa'
                    and end - dt.timedelta(days=self.store.config['vencimento_aviso_dias']) <= today <= end
                    and ('vencimento', enrollment['id']) not in warned):
                plan = self.app.get('planos', enrollment['plano'])
                message = classes.message(enrollment['aluno_id'], 'vencimento',
                                          f"Seu plano {plan['nome']} vence em {end:%d/%m}.", enrollment['id'], instant)
                created += message is not None

        for evaluation in self.store.all('avaliacoes'):
            start = dt.datetime.fromisoformat(evaluation['inicio'])
            if (evaluation['status'] == 'agendada'
                    and instant < start <= instant + dt.timedelta(hours=self.store.config['avaliacao_lembrete_horas'])
                    and ('avaliacao', evaluation['id']) not in warned):
                teacher = self.app.get('professores', evaluation['professor'])
                message = classes.message(evaluation['aluno_id'], 'avaliacao',
                                          f"Avaliação em {start:%d/%m %H:%M} com {teacher['nome']}.", evaluation['id'], instant)
                created += message is not None

        for student in self.store.all('alunos'):
            if not student['consentimento_marketing'] or student['nao_contatar'] or not student['codigo']:
                continue
            try:
                enrollment = self.app.ativa(student['id'], today.isoformat())
            except Error as exc:
                if exc.status != 422:
                    raise
                continue
            latest = max((c['quando'] for c in checkins if c['aluno_id'] == student['id']),
                         default=enrollment['inicio'] + 'T00:00')
            last = dt.datetime.fromisoformat(latest)
            if (today - last.date()).days < self.store.config['inatividade_dias']:
                continue
            if any(m['tipo'] == 'reativacao' and m['aluno_id'] == student['id']
                   and dt.datetime.fromisoformat(m['quando']) > last for m in messages):
                continue
            message = classes.message(student['id'], 'reativacao',
                                      'Sentimos sua falta! Vamos voltar a treinar?', enrollment['id'], instant)
            created += message is not None
        return dict(enviadas=created, reenviadas=resent, presencas=marked)
