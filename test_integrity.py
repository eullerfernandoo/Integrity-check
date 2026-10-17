import hashlib
from integrity_check import sha256_file
def test_hash_bate_com_hashlib(tmp_path):
    # 1. PREPARAR: cria um arquivo temporario
    arquivo = tmp_path / 'teste.log'
    arquivo.write_text('login ok\n')

    #2 Agir: calcula o hash de duas formas diferentes
    esperado = hashlib.sha256(arquivo.read_bytes()).hexdigest()
    obitido = sha256_file(str(arquivo))

    # 3 VERIFICAR: os dois tem que ser iguais
    assert obitido == esperado