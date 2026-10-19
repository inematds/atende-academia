"""Conversa determinística, com estado por telefone e histórico persistente."""
import datetime as dt
import os
import re

from .attendance import Attendance
from .classes import Classes
from .domain import Error, norm, now, phone, require
from .training import Training

STOPWORDS = set('que qual quais quem como onde quando para com sem por dos das nos nas uma uns umas voce voces vcs tem ter sao esta estao ele ela eles elas isso isto aqui ali ai'.split())
HEALTH = ('dor forte', 'dor no peito', 'falta de ar', 'desmaio', 'desmaiou', 'tontura', 'lesao', 'machuquei', 'torci', 'sangrando', 'sangramento', 'infarto')
PLAN = 'Confira seu plano com a recepção.'


def normalize(text):
    return ' '.join(re.sub(r'[^\w\s]|_', ' ', norm(text)).split())


def stamp(value):
    return dt.datetime.fromisoformat(value).strftime('%d/%m %H:%M')


class Conversation:
    def __init__(self, app):
        self.app, self.store = app, app.store
        self.classes = Classes(app)

    def opened(self, telephone):
        return next((x for x in self.store.all('atendimentos') if x['telefone'] == telephone and x['status'] == 'aberto'), None)

    def human(self, telephone, student, text, priority='normal'):
        item = self.opened(telephone)
        if item is None:
            item = dict(id=self.store.next_id('atendimentos'), telefone=telephone,
                        nome=student['nome'] if student else None, motivo=text,
                        prioridade=priority, status='aberto', ultima_mensagem=text)
        elif priority == 'alta':
            item.update(prioridade='alta', motivo=text, ultima_mensagem=text)
        self.store.save('atendimentos', item)
        return item

    def record(self, telephone, student, text, direction):
        self.store.save('mensagens', dict(id=self.store.next_id('mensagens'), telefone=telephone,
                        aluno_id=student['id'] if student else None, texto=text,
                        direcao=direction, quando=now().isoformat(timespec='minutes')))

    def receive(self, body):
        require(body, {'telefone': str, 'texto': str})
        telephone, text = phone(body['telefone']), body['texto']
        student = next((a for a in self.store.all('alunos') if a['telefone'] == telephone), None)
        state = self.store.get('conversas', telephone) or dict(id=telephone, erros=0)
        self.record(telephone, student, text, 'entrada')
        result = self.decide(telephone, student, text, state)
        self.store.save('conversas', state)
        # Cadastro durante a conversa associa também o histórico anterior ao aluno.
        student = next((a for a in self.store.all('alunos') if a['telefone'] == telephone), None)
        if student:
            for entry in self.store.all('mensagens'):
                if entry['telefone'] == telephone and entry['aluno_id'] is None:
                    entry['aluno_id'] = student['id']
                    self.store.save('mensagens', entry)
        for response in result:
            self.record(telephone, student, response, 'saida')
        return {'respostas': result}

    def reserve(self, student, option):
        try:
            result = self.classes.reserve(dict(aluno_id=student['id'], aula_id=option['aula_id'], data=option['data']))
            return 'Aula reservada: ' + stamp(result['inicio'])
        except Error as exc:
            if 'matricula' in exc.motivo:
                return PLAN
            return exc.motivo.replace('_', ' ')

    def decide(self, telephone, student, text, state):
        t = normalize(text)
        previous_errors = state.get('erros', 0)
        state['erros'] = 0
        if any(word in t for word in HEALTH):
            self.human(telephone, student, text, 'alta')
            return ['Pare o exercício, avise o professor e procure ajuda: 192.']
        # §21 suspende o bot durante atendimento humano, exceto alerta de saúde.
        if self.opened(telephone):
            return []
        if t in ('parar', 'sair', 'pare'):
            state['nao_contatar'] = True
            if student:
                self.app.aluno({'nao_contatar': True}, student['id'])
            return ['Você não vai mais receber mensagens automáticas.']
        if any(word in t for word in ('atendente', 'humano', 'falar com alguem')):
            self.human(telephone, student, text)
            return ['Vou chamar um atendente.']
        flow = state.get('fluxo')
        if flow:
            if flow['tipo'] == 'reservar' and t == 'cancelar':
                state.pop('fluxo')
                return ['Ok, saímos da reserva.']
            if not t.isdecimal() or not 1 <= int(t) <= len(flow['opcoes']):
                return [flow['texto']]
            option = flow['opcoes'][int(t) - 1]
            state.pop('fluxo')
            if flow['tipo'] == 'reservar':
                return [self.reserve(student, option)]
            try:
                result = self.classes.change(option['id'], 'cancelar', {})
                return ['Reserva cancelada' + (' fora do prazo.' if result['status'] == 'cancelada_tarde' else '.')]
            except Error as exc:
                return [exc.motivo.replace('_', ' ')]
        output = [m for m in self.store.all('saida') if m['telefone'] == telephone]
        if student and output and output[-1]['tipo'] == 'espera' and not output[-1].get('respondida') and t in ('1', 'sim'):
            message = output[-1]
            message['respondida'] = True
            self.store.save('saida', message)
            request = self.app.get('espera', message['referencia_id'])
            request['status'] = 'respondido'
            self.store.save('espera', request)
            return [self.reserve(student, request)]
        if state.pop('aguarda_nome', False) and not student:
            _, student = self.app.aluno(dict(nome=text.strip(), telefone=telephone, nao_contatar=state.get('nao_contatar', False)))
            return [PLAN]
        triggers = [('checkin', ('check in', 'checkin', 'cheguei')), ('avaliacao', ('avaliacao',)),
                    ('cancelar', ('cancelar', 'desmarcar')), ('reservar', ('reservar', 'reserva', 'agendar', 'marcar', 'inscrever')),
                    ('aulas', ('aula', 'grade')), ('plano', ('plano', 'vencimento', 'vence', 'mensalidade', 'matricula')),
                    ('treino', ('treino', 'ficha'))]
        command = next((key for key, words in triggers if any(w in t for w in words)), None)
        if command and not student:
            state['aguarda_nome'] = True
            return ['Qual é o seu nome?']
        if command == 'checkin':
            try:
                Attendance(self.app).checkin({'codigo': student['codigo']})
                return ['Check-in registrado. Bom treino!']
            except Error:
                return [PLAN]
        if command == 'avaliacao':
            return ['Para avaliação física, fale com a recepção.']
        if command == 'cancelar':
            options = [r for r in self.classes.reservations({'aluno_id': [str(student['id'])]})
                       if r['status'] == 'reservada' and r['inicio'] > now().isoformat(timespec='minutes')]
            if not options:
                return ['Nenhuma reserva futura.']
            lines = [f"{i}) {stamp(o['inicio'])} {o['modalidade']}" for i, o in enumerate(options, 1)]
            return self.flow(state, command, options, lines)
        if command in ('reservar', 'aulas'):
            if command == 'reservar':
                try:
                    self.app.ativa(student['id'], now().date().isoformat())
                except Error:
                    return [PLAN]
            days = self.store.config['reserva_antecedencia_dias'] if command == 'reservar' else 1
            options = [o for o in self.classes.occurrences({'de': [now().date().isoformat()],
                       'ate': [(now().date() + dt.timedelta(days=days)).isoformat()]})
                       if not o['cancelada'] and o['inicio'] > now().isoformat(timespec='minutes')]
            if command == 'reservar':
                options = [o for o in options if o['livres'] > 0][:5]
            if not options:
                return ['Sem aulas disponíveis.']
            lines = [f"{stamp(o['inicio'])} {o['modalidade']} com {o['professor']}" for o in options]
            if command == 'reservar':
                return self.flow(state, command, options, [f'{i}) {line}' for i, line in enumerate(lines, 1)])
            return ['\n'.join(f"{line} — {o['livres']} vagas" for line, o in zip(lines, options))]
        if command == 'plano':
            try:
                enrollment = self.app.ativa(student['id'], now().date().isoformat())
                status = 'ativa'
            except Error:
                enrollments = [m for m in self.store.all('matriculas') if m['aluno_id'] == student['id'] and m['situacao'] != 'cancelada']
                if not enrollments:
                    return [PLAN]
                enrollment = max(enrollments, key=lambda m: (m['fim'], m['id']))
                status = 'trancada' if enrollment['situacao'] == 'trancada' else 'vencida'
            plan = self.app.get('planos', enrollment['plano'])
            return [f"{plan['nome']}: matrícula {status}, vencimento {dt.date.fromisoformat(enrollment['fim']).strftime('%d/%m')}."]
        if command == 'treino':
            return [Training(self.app).today(student['id'])]
        matches = []
        for exercise in Training(self.app).catalog():
            size = max((len(normalize(name)) for name in [exercise['nome']] + exercise['apelidos']
                        if normalize(name) and normalize(name) in t), default=0)
            if size:
                matches.append((size, exercise))
        if matches:
            exercise = max(matches, key=lambda pair: pair[0])[1]
            lines = [exercise['nome']] + [f'{i}. {step}' for i, step in enumerate(exercise['passos'], 1)]
            if exercise['cuidados']:
                lines.append('Cuidado: ' + exercise['cuidados'][0])
            if exercise['svg']:
                lines.append('Veja a animação: ' + os.environ.get('PUBLIC_URL', '').rstrip('/') + '/exercicios/' + exercise['id'])
            return ['\n'.join(lines)]
        best, answer = 0, None
        for faq in self.store.all('faq'):
            for question in faq['perguntas']:
                words = {w for w in normalize(question).split() if len(w) >= 3 and w not in STOPWORDS}
                score = sum(w in t for w in words) / len(words) if words else 0
                if score >= .6 and score > best:
                    best, answer = score, faq['resposta']
        if answer is not None:
            return [answer]
        state['erros'] = previous_errors + 1
        if state['erros'] >= 2:
            self.human(telephone, student, text)
        return ['Não entendi. Posso chamar um atendente.']

    def flow(self, state, kind, options, lines):
        text = '\n'.join(lines)
        state['fluxo'] = dict(tipo=kind, opcoes=options, texto=text)
        return [text]

    def change_human(self, identifier, action, body):
        item = self.app.get('atendimentos', identifier)
        if action == 'encerrar':
            item['status'] = 'encerrado'
            self.store.save('atendimentos', item)
        else:
            require(body, {'texto': str})
            student = next((a for a in self.store.all('alunos') if a['telefone'] == item['telefone']), None)
            self.store.save('saida', dict(id=self.store.next_id('saida'), tipo='humano', telefone=item['telefone'],
                            aluno_id=student['id'] if student else None, texto=body['texto'], referencia_id=identifier,
                            quando=now().isoformat(timespec='minutes'), status='simulado'))
        return {'status': item['status']}
