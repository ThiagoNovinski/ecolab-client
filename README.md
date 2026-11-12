# Ecolab Client Agent

Agente leve em Python projetado para rodar em segundo plano nas máquinas clientes dos laboratórios. O agente lê as credenciais locais do **RustDesk** (ID e senha dinâmica) e envia pulsos periódicos de *heartbeat* para o servidor central (**Ecolab Hub**).

---

## 📋 Pré-requisitos

- **Python 3.10+** (necessário para compilação local, caso deseje gerar o executável).
- **RustDesk** instalado e configurado na máquina cliente.
- Acesso de rede à URL do servidor central (**Ecolab Hub**).

---

## 📂 Estrutura do Projeto

```text
ecolab-client/
├── agent.py          # Script principal do agente
├── requirements.txt  # Lista de dependências Python
├── .gitignore        # Arquivos ignorados pelo Git
└── README.md         # Documentação de uso e compilação
```

---

## 🛠️ Configuração Inicial (Ambiente de Desenvolvimento)

### 1. Clonar o Repositório
```bash
git clone https://github.com/SeuUsuario/ecolab-client.git
cd ecolab-client
```

### 2. Criar e Ativar o Ambiente Virtual

**No Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**No Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuração da URL do Servidor

No arquivo `agent.py`, ajuste a variável `SERVER_URL` apontando para o endpoint do seu servidor central (URL do Ngrok, Cloudflare Tunnel ou IP local):

```python
SERVER_URL = "https://seu-dominio.ngrok-free.app/api/status"
```

---

## 🖥️ Execução em Modo de Desenvolvimento

Para testar a execução antes de compilar:

**No Windows:**
```powershell
python agent.py
```

**No Linux:**
```bash
python3 agent.py
```

---

## 📦 Compilação com PyInstaller

Você pode compilar o script em um executável/binário único e autônomo, eliminando a necessidade de ter o Python instalado na máquina final.

### 1. Compilando no Windows (`.exe`)

Execute o comando abaixo no terminal da pasta do projeto com o `venv` ativado:

```powershell
pyinstaller --noconfirm --onefile --windowed --name "EcolabAgent" agent.py
```

- `--onefile`: Gera um único arquivo executável (`.exe`).
- `--windowed`: Executa em segundo plano sem abrir a janela preta do prompt de comando.
- `--name "EcolabAgent"`: Define o nome do executável final.

O arquivo gerado estará disponível em: `dist/EcolabAgent.exe`.

---

### 2. Compilando no Linux (Binário ELF)

No terminal do Linux com o ambiente virtual ativado:

```bash
pyinstaller --noconfirm --onefile --name "ecolab-agent" agent.py
```

O binário final estará disponível em: `dist/ecolab-agent`.

Garanta permissão de execução:
```bash
chmod +x dist/ecolab-agent
```

---

## 🚀 Configurando Inicialização Automática no Boot

### 🟦 No Windows

#### Método 1: Pasta de Inicialização (Startup)
1. Pressione `Win + R`, digite `shell:startup` e pressione **Enter**.
2. Copie o executável `EcolabAgent.exe` (ou crie um atalho para ele) dentro dessa pasta.

#### Método 2: Agendador de Tarefas (Task Scheduler)
Para executar como Serviço/Sistema sem depender de um usuário logado:
1. Abra o **Agendador de Tarefas**.
2. Clique em **Criar Tarefa Básica**.
3. Escolha o gatilho: **Ao iniciar o computador**.
4. Ação: **Iniciar um programa** -> selecione o `EcolabAgent.exe`.

---

### 🟩 No Linux (via `systemd`)

Para rodar o agente como um serviço de sistema no Linux:

1. Mova o binário para um diretório do sistema:
   ```bash
   sudo cp dist/ecolab-agent /usr/local/bin/
   ```

2. Crie o arquivo de serviço do `systemd`:
   ```bash
   sudo nano /etc/systemd/system/ecolab-agent.service
   ```

3. Adicione a seguinte configuração ao arquivo:
   ```ini
   [Unit]
   Description=Ecolab Client Agent Service
   After=network.target rustdesk.service

   [Service]
   Type=simple
   ExecStart=/usr/local/bin/ecolab-agent
   Restart=always
   RestartSec=10
   User=root

   [Install]
   WantedBy=multi-user.target
   ```

4. Recarregue os daemons e ative o serviço:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now ecolab-agent.service
   ```

5. Verifique o status do serviço:
   ```bash
   sudo systemctl status ecolab-agent.service
   ```

---

## 🔍 Solução de Problemas

- **Não encontra o arquivo `RustDesk.toml`:**
  - Verifique se o RustDesk foi instalado corretamente como serviço do sistema ou se está rodando no perfil de usuário local.
  - Certifique-se de executar o agente com permissões adequadas de leitura nos caminhos do sistema.
- **Falha de conexão com o servidor:**
  - Verifique se a `SERVER_URL` no `agent.py` está acessível a partir da rede local/externa da máquina cliente.