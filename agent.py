import time
import socket
import requests
from rustdesk_manager import obter_rustdesk_id, rotacionar_senha

# ---------------------------------------------------------------------------
# CONFIGURAÇÕES DO AGENTE
# ---------------------------------------------------------------------------
SERVER_URL = "https://say-drizzle-credit.ngrok-free.dev/status"
API_SECRET_TOKEN = "chave_secreta_do_laboratorio_ecolab"
INTERVALO_HEARTBEAT = 15

IDENTIFICACAO_MAQUINA = socket.gethostname().upper()

HEADERS = {
    "X-API-Key": API_SECRET_TOKEN,
    "Content-Type": "application/json",
}

senha_atual_local: str | None = None


def enviar_payload(rustdesk_id: str, senha: str) -> dict | None:
    """Envia o heartbeat para a API central e retorna o JSON de resposta."""
    payload = {
        "identificacao": IDENTIFICACAO_MAQUINA,
        "rustdesk_id": rustdesk_id,
        "senha": senha,
    }

    try:
        response = requests.post(SERVER_URL, json=payload, headers=HEADERS, timeout=5)
        if response.status_code in (200, 201):
            print(f"[{time.strftime('%H:%M:%S')}] Heartbeat OK ({IDENTIFICACAO_MAQUINA} - ID: {rustdesk_id}).")
            return response.json()

        print(f"[AVISO] Servidor respondeu {response.status_code}: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha de comunicação com o servidor: {e}")
        return None


def ciclo_heartbeat():
    global senha_atual_local

    rustdesk_id = obter_rustdesk_id()
    if not rustdesk_id:
        print("[AVISO] ID numérico do RustDesk não encontrado. Pulando ciclo.")
        return

    # 1. Inicializa a senha no primeiro ciclo após o boot
    if not senha_atual_local:
        senha_atual_local = rotacionar_senha(length=24)
        if not senha_atual_local:
            return

    # 2. Envia o status atual para a API
    resposta = enviar_payload(rustdesk_id, senha_atual_local)

    # 3. Se a sessão foi encerrada no painel, rotaciona a senha e sincroniza imediatamente
    if resposta and resposta.get("rotacionar_senha"):
        print("[SEGURANÇA] Sessão encerrada no painel. Gerando nova senha...")
        nova_senha = rotacionar_senha(length=24)
        if nova_senha:
            senha_atual_local = nova_senha
            enviar_payload(rustdesk_id, senha_atual_local)


def main():
    print("=" * 60)
    print(" Agente Ecolab Client em Execução")
    print(f" Máquina: {IDENTIFICACAO_MAQUINA}")
    print(f" Destino: {SERVER_URL}")
    print("=" * 60)

    while True:
        ciclo_heartbeat()
        time.sleep(INTERVALO_HEARTBEAT)


if __name__ == "__main__":
    main()