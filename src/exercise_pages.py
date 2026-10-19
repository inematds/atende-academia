"""Páginas públicas do catálogo e arquivos restritos às pastas configuradas."""
import os
import re
from html import escape
from pathlib import Path
from string import Template

from .domain import Error
from .store import ROOT
from .training import Training


class Resource:
    def __init__(self, content, content_type):
        self.content = content
        self.content_type = content_type


def file_path(identifier, extension):
    if not re.fullmatch(r'[\w-]+', identifier) or extension not in ('svg', 'mp4'):
        raise Error(404, 'arquivo_inexistente')
    folder = ROOT / 'web' / 'exercicios'
    if extension == 'mp4':
        folder = Path(os.environ.get('EXERCICIOS_MP4_DIR') or folder)
    folder = folder.resolve()
    path = (folder / (identifier + '.' + extension)).resolve()
    if path.parent != folder or not path.is_file():
        raise Error(404, 'arquivo_inexistente')
    return path


def exercise_resource(app, path):
    match = re.fullmatch(r'/exercicios/([\w-]+)(?:\.(svg|mp4))?', path)
    if not match:
        raise Error(404, 'exercicio_inexistente')
    identifier, extension = match.groups()
    if extension:
        try:
            content = file_path(identifier, extension).read_bytes()
        except OSError:
            raise Error(404, 'arquivo_inexistente') from None
        return Resource(content, 'image/svg+xml' if extension == 'svg' else 'video/mp4')
    item = Training(app).exercise(identifier)

    def items(values):
        return ''.join('<li>' + escape(value) + '</li>' for value in values)

    def section(title, values):
        return ('<h2>' + title + '</h2><ul>' + items(values) + '</ul>') if values else ''

    animation = ''
    if item['svg']:
        animation = (f'<figure><img src="/exercicios/{escape(identifier)}.svg" '
                     f'alt="Demonstração de {escape(item["nome"])}" width="400" height="400">'
                     '<figcaption>Observe o movimento e siga as orientações do professor.</figcaption></figure>')
    template = Template((ROOT / 'web' / 'exercicio.html').read_text(encoding='utf-8'))
    html = template.substitute(nome=escape(item['nome']), animacao=animation,
                               classe='' if animation else 'sem-animacao',
                               passos=items(item['passos']),
                               erros=section('Erros comuns', item['erros_comuns']),
                               cuidados=section('Cuidados', item['cuidados']))
    return Resource(html.encode('utf-8'), 'text/html; charset=utf-8')
