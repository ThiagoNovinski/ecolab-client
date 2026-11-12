import os
import re
import sys
import shutil
import subprocess
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def encontrar_executavel() -> str | None:
    exe = shutil.which("rustdesk.exe" if os.name == "nt" else "rustdesk")
    if exe:
        return exe

    caminhos = [
        Path(r"C:\Program Files\RustDesk\rustdesk.exe"),
        Path(r"C:\Program Files (x86)\RustDesk\rustdesk.exe"),
        Path(r"D:\RustDesk\RustDesk\rustdesk.exe"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/RustDesk/rustdesk.exe",
        Path("/usr/bin/rustdesk"),
    ]
    for p in caminhos:
        if p.is_file():
            return str(p)
    return None


def extrair_id_numerico(texto: str) -> str | None:
    """Aceita exclusivamente sequências numéricas de 8 a 12 dígitos."""
    if not texto:
        return None
    sem_espacos = texto.replace(" ", "").strip()
    match = re.search(r"\b(\d{8,12})\b", sem_espacos)
    return match.group(1) if match else None


def metodo_cli(exe: str) -> str | None:
    print(f"[1] Testando CLI via: {exe}")
    try:
        if os.name == "nt":
            # No Windows, '| more' força o executável GUI a descarregar o texto no stdout
            cmd = f'"{exe}" --get-id | more'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        else:
            res = subprocess.run([exe, "--get-id"], capture_output=True, text=True, timeout=10)

        saida_bruta = res.stdout.strip()
        id_limpo = extrair_id_numerico(saida_bruta)
        print(f"    Saída bruta: {repr(saida_bruta)} -> ID extraído: {id_limpo}")
        return id_limpo
    except Exception as e:
        print(f"    Falha na CLI: {e}")
        return None


def metodo_toml() -> str | None:
    print("[2] Testando leitura direta dos arquivos RustDesk.toml...")
    caminhos = [
        r"C:\Windows\ServiceProfiles\LocalService\AppData\Roaming\RustDesk\config\RustDesk.toml",
        os.path.expandvars(r"%APPDATA%\RustDesk\config\RustDesk.toml"),
        "/root/.config/rustdesk/RustDesk.toml",
        os.path.expanduser("~/.config/rustdesk/RustDesk.toml"),
    ]

    for caminho in caminhos:
        if not os.path.exists(caminho):
            continue
        try:
            with open(caminho, "r", encoding="utf-8-sig") as f:
                dados = tomllib.loads(f.read())
                # Lê apenas 'id' em texto claro; ignora 'enc_id'
                id_bruto = str(dados.get("id") or "")
                id_limpo = extrair_id_numerico(id_bruto)
                print(f"    Arquivo: {caminho}")
                print(f"    Campo 'id': {repr(id_bruto)} -> ID extraído: {id_limpo}")
                if id_limpo:
                    return id_limpo
        except PermissionError:
            print(f"    Sem permissão (execute o terminal como Admin): {caminho}")
        except Exception as e:
            print(f"    Erro ao ler {caminho}: {e}")
    return None


def main():
    print("=== TESTE DE EXTRAÇÃO DE ID DO RUSTDESK ===\n")
    exe = encontrar_executavel()

    id_final = None
    if exe:
        id_final = metodo_cli(exe)
    else:
        print("[1] Executável do RustDesk não encontrado.")

    if not id_final:
        id_final = metodo_toml()

    print("\n" + "=" * 44)
    if id_final:
        print(f"SUCESSO! ID numérico validado: {id_final}")
    else:
        print("FALHA: Nenhum ID numérico válido foi encontrado.")
    print("=" * 44)


if __name__ == "__main__":
    main()