#!/usr/bin/env python3
"""Verificador de integridade de arquivos de log (SHA-256)."""
import argparse
import hashlib
import hmac
import json
import os
import sys

DEFAULT_DB = os.environ.get(
    "INTEGRITY_DB", os.path.expanduser("~/.integrity-check/hashes.json")
)
KEY = os.environ.get("INTEGRITY_KEY", "").encode()  # opcional: protege o próprio banco


# ---------- hash ----------
def sha256_file(path, bloco=65536):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(bloco):
            h.update(chunk)
    return h.hexdigest()


def listar_arquivos(alvo):
    alvo = os.path.realpath(alvo)
    if os.path.isfile(alvo):
        return [alvo]
    if os.path.isdir(alvo):
        achados = []
        for raiz, _, arquivos in os.walk(alvo):
            for nome in arquivos:
                p = os.path.join(raiz, nome)
                if os.path.isfile(p) and not os.path.islink(p):
                    achados.append(p)
        return sorted(achados)
    sys.exit(f"Erro: '{alvo}' não existe.")


# ---------- banco de hashes ----------
def _assinar(arquivos):
    payload = json.dumps(arquivos, sort_keys=True).encode()
    return hmac.new(KEY, payload, hashlib.sha256).hexdigest()


def carregar_db(db_path):
    if not os.path.exists(db_path):
        return {}
    with open(db_path) as f:
        dados = json.load(f)
    if KEY and not hmac.compare_digest(dados.get("hmac", ""), _assinar(dados["files"])):
        sys.exit("ALERTA: o próprio banco de hashes foi adulterado (HMAC inválido)!")
    return dados["files"]


def salvar_db(db_path, arquivos):
    os.makedirs(os.path.dirname(db_path), mode=0o700, exist_ok=True)
    dados = {"files": arquivos}
    if KEY:
        dados["hmac"] = _assinar(arquivos)
    tmp = db_path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(dados, f, indent=2)
    os.replace(tmp, db_path)  # troca atômica


# ---------- comandos ----------
def cmd_init(args):
    db = carregar_db(args.db)
    n = 0
    for p in listar_arquivos(args.alvo):
        try:
            db[p] = sha256_file(p)
            n += 1
        except OSError as e:
            print(f"Aviso: não foi possível ler {p}: {e}", file=sys.stderr)
    salvar_db(args.db, db)
    print(f"Hashes stored successfully. ({n} arquivo(s))")


def cmd_check(args):
    db = carregar_db(args.db)
    if not db:
        sys.exit("Banco vazio. Rode 'init' primeiro.")
    arquivos = listar_arquivos(args.alvo)
    problemas = 0

    for p in arquivos:
        if p not in db:
            print(f"{p}: Status: Not registered (arquivo novo)")
            problemas += 1
            continue
        try:
            atual = sha256_file(p)
        except OSError as e:
            print(f"{p}: erro de leitura ({e})")
            problemas += 1
            continue
        if atual == db[p]:
            print(f"{p}: Status: Unmodified")
        else:
            print(f"{p}: Status: Modified (Hash mismatch)")
            problemas += 1

    # arquivos registrados que sumiram (se o alvo for um diretório)
    alvo = os.path.realpath(args.alvo)
    if os.path.isdir(alvo):
        for p in db:
            if p.startswith(alvo + os.sep) and not os.path.exists(p):
                print(f"{p}: Status: Missing (arquivo removido)")
                problemas += 1

    sys.exit(1 if problemas else 0)  # útil em cron/CI


def cmd_update(args):
    db = carregar_db(args.db)
    for p in listar_arquivos(args.alvo):
        db[p] = sha256_file(p)
    salvar_db(args.db, db)
    print("Hash updated successfully.")


def main():
    ap = argparse.ArgumentParser(description="Verificador de integridade de logs")
    ap.add_argument("--db", default=DEFAULT_DB, help="caminho do banco de hashes")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nome, fn in (("init", cmd_init), ("check", cmd_check), ("update", cmd_update)):
        sp = sub.add_parser(nome)
        sp.add_argument("alvo", help="arquivo ou diretório de log")
        sp.set_defaults(func=fn)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()