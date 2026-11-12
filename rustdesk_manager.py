import os
import re
import sys
import ctypes
import secrets
import string
import shutil
import subprocess
import argparse
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def verificar_admin() -> bool:
    """Verifica se o processo possui privilégios de Administrador (Windows) ou root (Linux)."""
    if os.name == "nt":
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    return os.geteuid() == 0


def find_rustdesk() -> str | None:
    """Localiza o executável do RustDesk no Windows ou Linux."""
    bin_name = "rustdesk.exe" if os.name == "nt" else "rustdesk"
    executable = shutil.which(bin_name)
    if executable:
        return executable

    if os.name == "nt":
        paths = [
            Path(r"D:\RustDesk\RustDesk\rustdesk.exe"),
            Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "RustDesk/rustdesk.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "RustDesk/rustdesk.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/RustDesk/rustdesk.exe",
        ]
    else:
        paths = [
            Path("/usr/bin/rustdesk"),
            Path("/usr/local/bin/rustdesk"),
            Path("/opt/rustdesk/rustdesk"),
        ]

    for path in paths:
        if path.is_file():
            return str(path)

    return None


def extrair_id_numerico(texto: str) -> str | None:
    """Aceita exclusivamente sequências numéricas válidas de 8 a 12 dígitos."""
    if not texto:
        return None
    sem_espacos = texto.replace(" ", "").strip()
    match = re.search(r"\b(\d{8,12})\b", sem_espacos)
    return match.group(1) if match else None


def obter_caminhos_config() -> list[str]:
    """Retorna os caminhos possíveis do arquivo RustDesk.toml."""
    if os.name == "nt":
        return [
            r"C:\Windows\ServiceProfiles\LocalService\AppData\Roaming\RustDesk\config\RustDesk.toml",
            r"C:\Windows\ServiceProfiles\LocalService\AppData\Roaming\RustDesk\config\RustDesk2.toml",
            os.path.expandvars(r"%APPDATA%\RustDesk\config\RustDesk.toml"),
            os.path.expandvars(r"%APPDATA%\RustDesk\config\RustDesk2.toml"),
        ]

    caminhos = [
        "/root/.config/rustdesk/RustDesk.toml",
        "/root/.config/rustdesk/RustDesk2.toml",
        os.path.expanduser("~/.config/rustdesk/RustDesk.toml"),
        os.path.expanduser("~/.config/rustdesk/RustDesk2.toml"),
    ]
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        caminhos.extend([
            f"/home/{sudo_user}/.config/rustdesk/RustDesk.toml",
            f"/home/{sudo_user}/.config/rustdesk/RustDesk2.toml",
        ])
    return caminhos


def obter_rustdesk_id(custom_exe: str | None = None) -> str | None:
    """Obtém o ID numérico real via CLI (--get-id) ou fallback seguro no TOML."""
    executable = custom_exe or find_rustdesk()
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    # 1. Método principal: CLI --get-id
    if executable and Path(executable).is_file():
        try:
            if os.name == "nt":
                cmd = f'"{executable}" --get-id | more'
                res = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=creation_flags,
                )
            else:
                res = subprocess.run(
                    [executable, "--get-id"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

            id_cli = extrair_id_numerico(res.stdout) or extrair_id_numerico(res.stderr)
            if id_cli:
                return id_cli
        except Exception as e:
            print(f"[AVISO] Falha ao consultar ID via CLI: {e}")

    # 2. Fallback: leitura do campo 'id' em texto claro no TOML (ignora 'enc_id')
    for caminho in obter_caminhos_config():
        if not os.path.exists(caminho):
            continue
        try:
            with open(caminho, "r", encoding="utf-8-sig") as f:
                dados = tomllib.loads(f.read())
                id_toml = extrair_id_numerico(str(dados.get("id") or ""))
                if id_toml:
                    return id_toml
        except PermissionError:
            print(f"[AVISO] Sem permissão para ler {caminho}.")
        except Exception as e:
            print(f"[ERRO] Falha ao ler {caminho}: {e}")

    return None


def generate_password(length: int = 24) -> str:
    """Gera uma senha aleatória criptograficamente segura."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def execute_command(executable: str, arguments: list[str]) -> subprocess.CompletedProcess:
    """Executa um comando CLI do RustDesk sem abrir janela de terminal."""
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    result = subprocess.run(
        [executable] + arguments,
        capture_output=True,
        text=True,
        timeout=30,
        creationflags=creation_flags,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
            or result.stdout.strip()
            or f"RustDesk retornou código {result.returncode}"
        )

    return result


def configure_rustdesk(executable: str, length: int = 24) -> str:
    """Define nova senha permanente e desabilita a senha temporária."""
    password = generate_password(length)

    execute_command(executable, ["--password", password])
    execute_command(
        executable,
        ["--option", "verification-method", "use-permanent-password"],
    )

    return password


def rotacionar_senha(custom_exe: str | None = None, length: int = 24) -> str | None:
    """Gera e aplica uma nova senha permanente no RustDesk, retornando a senha gerada."""
    if not verificar_admin():
        print("[AVISO] Agente sem privilégios de Administrador/root. A alteração pode falhar.")

    executable = custom_exe or find_rustdesk()
    if not executable or not Path(executable).is_file():
        print("[ERRO] Executável do RustDesk não encontrado.")
        return None

    try:
        nova_senha = configure_rustdesk(executable, length=length)
        print("[OK] Senha permanente do RustDesk atualizada via CLI.")
        return nova_senha
    except Exception as error:
        print(f"[ERRO] Falha ao configurar RustDesk: {error}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerenciador CLI do RustDesk")
    parser.add_argument("--exe", help="Caminho personalizado do executável RustDesk")
    args = parser.parse_args()

    id_atual = obter_rustdesk_id(custom_exe=args.exe)
    print(f"ID detectado: {id_atual}")

    senha = rotacionar_senha(custom_exe=args.exe)
    if senha:
        print(f"Nova senha permanente: {senha}")
    else:
        sys.exit(1)