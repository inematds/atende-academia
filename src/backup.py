"""Arquivo de backup autocontido, sem copiar um SQLite em escrita."""
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import zipfile


def snapshot(source, target):
    with sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True) as origin:
        with sqlite3.connect(target) as destination:
            origin.backup(destination)
    origin.close()
    destination.close()


def backup(directory, output):
    directory, output = Path(directory), Path(output)
    if output.resolve() in { (directory / name).resolve() for name in ('academia.json', 'academia.sqlite3') }:
        raise ValueError('o backup deve usar outro arquivo')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        temporary = Path(temporary)
        snapshot(directory / 'academia.sqlite3', temporary / 'academia.sqlite3')
        archive = temporary / 'backup.zip'
        with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
            bundle.write(temporary / 'academia.sqlite3', 'academia.sqlite3')
            bundle.write(directory / 'academia.json', 'academia.json')
        os.replace(archive, output)


def restore(directory, archive):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    # Ler somente nomes conhecidos: nunca extrair caminhos fornecidos pelo arquivo.
    with tempfile.TemporaryDirectory(dir=directory) as temporary:
        temporary = Path(temporary)
        with zipfile.ZipFile(archive) as bundle:
            config = bundle.read('academia.json')
            if not isinstance(json.loads(config), dict):
                raise ValueError('configuração inválida')
            (temporary / 'academia.json').write_bytes(config)
            database = temporary / 'academia.sqlite3'
            database.write_bytes(bundle.read('academia.sqlite3'))
        with sqlite3.connect(database) as check:
            if check.execute('PRAGMA integrity_check').fetchone() != ('ok',):
                raise ValueError('banco inválido')
            check.execute('SELECT colecao, id, documento FROM registros LIMIT 1')
            check.execute('SELECT chave, valor FROM metadados LIMIT 1')
        check.close()
        # Pré-condição da CLI: servidor parado. Não conservar WAL do estado antigo.
        for suffix in ('-wal', '-shm'):
            (directory / ('academia.sqlite3' + suffix)).unlink(missing_ok=True)
        os.replace(database, directory / 'academia.sqlite3')
        os.replace(temporary / 'academia.json', directory / 'academia.json')
