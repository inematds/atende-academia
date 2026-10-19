"""Campanhas consentidas e exportação/anonimização dos dados do aluno."""
from .classes import Classes
from .domain import norm, require


class Privacy:
    def __init__(self, app):
        self.app, self.store = app, app.store

    def campaign(self, body):
        require(body, {'texto': str})
        text = norm(body['texto'])
        violations = []
        if any(word in text for word in ('garantido', 'garantia de resultado', 'resultado garantido', '100%')):
            violations.append('promessa_resultado')
        if 'antes e depois' in text:
            violations.append('antes_depois')
        if violations:
            return 422, {'violacoes': violations}
        count = 0
        for student in self.store.all('alunos'):
            if student['consentimento_marketing'] and not student['nao_contatar']:
                count += Classes(self.app).message(student['id'], 'campanha', body['texto'], None) is not None
        return 200, {'enviadas': count}

    def related(self, collection, identifier):
        return [x for x in self.store.all(collection) if x.get('aluno_id') == identifier]

    def export(self, identifier):
        student = self.app.get('alunos', identifier)
        result = {'aluno': student}
        for collection in ('matriculas', 'reservas', 'checkins', 'avaliacoes'):
            result[collection] = self.related(collection, identifier)
        result['matriculas'] = [self.app.matricula_view(x) for x in result['matriculas']]
        result['ficha'] = self.store.get('fichas', identifier)
        messages = [x for x in self.store.all('mensagens')
                    if x.get('aluno_id') == identifier or
                    (student['telefone'] and x.get('aluno_id') is None and x.get('telefone') == student['telefone'])]
        messages += [dict(x, direcao='saida') for x in self.related('saida', identifier)]
        result['mensagens'] = [{k: x[k] for k in ('direcao', 'texto', 'quando')}
                               for x in sorted(messages, key=lambda x: x['quando'])]
        return result

    def anonymize(self, identifier):
        student = self.app.get('alunos', identifier)
        telephone = student['telefone']
        for reservation in self.related('reservas', identifier):
            if reservation['status'] == 'reservada':
                reservation['status'] = 'cancelada'
                Classes(self.app).refund(reservation)
                self.store.save('reservas', reservation)
        for evaluation in self.related('avaliacoes', identifier):
            if evaluation['status'] == 'agendada':
                evaluation['status'] = 'cancelada'
            evaluation['resultado'] = None
            self.store.save('avaliacoes', evaluation)
        for request in self.related('espera', identifier):
            if request['status'] in ('pendente', 'ofertado'):
                request['status'] = 'cancelada'
                self.store.save('espera', request)
        self.store.delete('fichas', identifier)
        # Remove também identificadores e textos das cópias operacionais.
        for collection in ('mensagens', 'saida'):
            for message in self.store.all(collection):
                if message.get('aluno_id') == identifier or (telephone and message.get('telefone') == telephone):
                    message.update(aluno_id=identifier, telefone=None, texto='')
                    self.store.save(collection, message)
        if telephone:
            self.store.delete('conversas', telephone)
            for ticket in self.store.all('atendimentos'):
                if ticket['telefone'] == telephone:
                    ticket.update(telefone=None, nome='removido', motivo='', ultima_mensagem='', status='encerrado')
                    self.store.save('atendimentos', ticket)
        student.update(nome='removido', telefone=None, codigo=None, email=None, nascimento=None,
                       consentimento_marketing=False, nao_contatar=True)
        self.store.save('alunos', student)
