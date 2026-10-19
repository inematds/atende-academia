"""Persistência transacional; cada entidade é um documento JSON no SQLite."""
import json
import shutil
import sqlite3
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOGOS = ('modalidades', 'professores', 'salas', 'planos', 'grade', 'exercicios', 'faq')


class Store:
    def __init__(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        config = directory / 'academia.json'
        if not config.exists():
            shutil.copyfile(ROOT / 'exemplos/academia.json', config)
        self.config = json.loads(config.read_text(encoding='utf-8'))
        self.lock = threading.RLock()
        self.db = sqlite3.connect(directory / 'academia.sqlite3', check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS registros (colecao TEXT, id TEXT, documento TEXT NOT NULL, PRIMARY KEY (colecao, id))')
        self.db.execute('CREATE TABLE IF NOT EXISTS metadados (chave TEXT PRIMARY KEY, valor TEXT)')
        with self.db:
            if not self.db.execute("SELECT 1 FROM metadados WHERE chave='semeado'").fetchone():
                for collection in CATALOGOS:
                    for original in self.config.get(collection, []):
                        item = dict(original)
                        if collection in ('professores', 'planos', 'grade', 'exercicios'):
                            item.setdefault('ativo', True)
                        if collection == 'planos':
                            item.setdefault('aulas', None)
                        self.save(collection, item)
                self.db.execute("INSERT INTO metadados VALUES ('semeado', '1')")

    def all(self, collection):
        return [json.loads(row[0]) for row in self.db.execute(
            'SELECT documento FROM registros WHERE colecao=? ORDER BY rowid', (collection,))]

    def get(self, collection, identifier):
        row = self.db.execute('SELECT documento FROM registros WHERE colecao=? AND id=?',
                              (collection, str(identifier))).fetchone()
        return json.loads(row[0]) if row else None

    def save(self, collection, item):
        self.db.execute('INSERT INTO registros VALUES (?, ?, ?) ON CONFLICT(colecao,id) DO UPDATE SET documento=excluded.documento',
                        (collection, str(item['id']), json.dumps(item, ensure_ascii=False)))
        return item

    def delete(self, collection, identifier):
        self.db.execute('DELETE FROM registros WHERE colecao=? AND id=?',
                        (collection, str(identifier)))

    def next_id(self, collection):
        key = 'sequencia:' + collection
        row = self.db.execute('SELECT valor FROM metadados WHERE chave=?', (key,)).fetchone()
        value = int(row[0]) + 1 if row else 1
        self.db.execute('INSERT INTO metadados VALUES (?, ?) ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor', (key, str(value)))
        return value
