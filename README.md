# Telegram Auto-Message Bot

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg?style=flat&logo=python&logoColor=white" alt="Python Version"/>
  <img src="https://img.shields.io/badge/Telethon-v1.30+-blue.svg?style=flat" alt="Telethon"/>
  <img src="https://img.shields.io/badge/GUI-CustomTkinter-brightgreen.svg?style=flat" alt="CustomTkinter"/>
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg?style=flat" alt="Platform"/>
</div>
<br>

A modern, multi-threaded Telegram UserBot available in two flavors: a beautiful graphical interface (GUI) for Desktop users, and a powerful, lightweight Command Line Interface (CLI) for VPS/Server deployments. It allows you to monitor a source chat and automatically broadcast the latest messages (Text, Photos, Videos, Documents) to multiple target groups using advanced anti-detection techniques.

> ⚠️ **Disclaimer:** This tool is intended for educational purposes only. Automating personal Telegram accounts (UserBots) violates Telegram's Terms of Service. Use this software responsibly and at your own risk. The author is not responsible for any banned accounts or damages caused by the misuse of this tool.

## 🚀 Quick Start (Local Setup)
```bash
git clone https://github.com/iurysf/Telegram-Auto-Msg.git
cd Telegram-Auto-Msg
pip install -r requirements.txt
python main_gui.py
```

## 🚀 Features & Anti-Ban Architecture

- **UI/UX Excellence**: Built with `CustomTkinter` featuring a responsive grid, real-time hacker-style terminal logs, and i18n support (English/Portuguese).
- **Advanced Stealth Architecture**:
  - **Hash Mutation**: Injects zero-width characters to alter message hashes invisibly, bypassing basic spam filters.
  - **Human-like Delays**: Implements randomized jitter delays between sends (not fixed intervals).
  - **Route Shuffling**: Randomizes the order of target groups in each cycle to prevent network pattern detection.
  - **Fresh Sends**: Sends messages as new rather than forwarding, breaking the forward-tree trace.
- **Smart Media Handling**: Caches photos/videos to the 'Saved Messages' cloud first, reusing the `file_id` to broadcast without redownloading/reuploading data.
- **Thread-Safe**: Flawless integration between the `asyncio` event loop and the `tkinter` main thread, ensuring the UI never freezes during network timeouts.

## 📸 Screenshots

![Main UI](https://github.com/iurysf/Telegram-Auto-Msg/blob/main/assets/print.png?raw=true)

## 🔑 Prerequisites

Before using the bot, you need to obtain your Telegram API credentials:
1. Log in to your Telegram core at [my.telegram.org](https://my.telegram.org).
2. Go to **API development tools**.
3. Create a new application to get your `api_id` and `api_hash`.

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/iurysf/Telegram-Auto-Msg.git
   cd Telegram-Auto-Msg
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   - **Desktop GUI**:
     ```bash
     python main_gui.py
     ```
   - **Terminal/Server CLI**:
     ```bash
     python main_cli.py
     ```
     *(Use `python main_cli.py --headless` to automatically start broadcasting in the background using your last saved CLI settings!)*

## 📖 Usage Guide / Guia de Uso

<details>
<summary><b>🇺🇸 Click to view the English Guide</b></summary>

<br>

### 1. First Run & Configuration
1. Open the application (`main_gui.py` or `.exe`).
2. **Select your Language**: Choose English on the first startup.
3. **API Setup**:
   - Paste your `API ID`, `API Hash`, and `Phone Number` (International format: `+123456789`).
   - Click **🔌 Connect Telegram**.
   - Enter the login code sent to your Telegram app.
   - *(Optional)* If you have 2FA enabled, enter your cloud password.

### 2. Selecting Source & Targets
*   **Source Group (Where to copy from):**
    - Click the 🔍 **Search Icon** next to the "Source Group ID" field.
    - Select the chat you want to monitor.
*   **Target Groups (Where to send to):**
    - Click **🔍 Fetch My Groups** on the sidebar.
    - Check ☑️ the boxes for every group you want to broadcast to.

### 3. Broadcasting
1. Set the **Interval** (e.g., `60` seconds).
   - *Note: The bot adds a random delay (jitter) to this interval for safety.*
2. Click **▶️ Start Broadcaster**.
3. **Monitor the Logs**: The black terminal window will show real-time actions.
4. To stop, simply click **⏹️ Stop Broadcaster**.

</details>

<details>
<summary><b>🇧🇷 Clique para ver o Guia em Português</b></summary>

<br>

### 1. Primeira Execução
1. Abra o aplicativo (`main_gui.py` ou `.exe`).
2. **Escolha o Idioma**: Selecione Português na primeira tela.
3. **Configuração da API**:
   - Cole seu `API ID`, `API Hash` e `Telefone` (Formato: `+5511999999999`).
   - Clique em **🔌 Conectar ao Telegram**.
   - Digite o código de login enviado para o seu app do Telegram.

### 2. Selecionando Fonte e Destinos
*   **Grupo Fonte (Origem):**
    - Clique na 🔍 **Lupa** ao lado do campo "ID Grupo Fonte".
    - Selecione o grupo/canal/bot que você deseja monitorar na lista.
*   **Grupos de Destino (Alvos):**
    - Clique em **🔍 Buscar Meus Grupos** na barra lateral.
    - Marque ☑️ as caixas dos grupos para onde as mensagens serão enviadas.

### 3. Iniciando os Disparos
1. Defina o **Intervalo** (ex: `60` segundos).
2. Clique em **▶️ Iniciar Disparos**.
3. Acompanhe o **Terminal**: O bot mostrará em tempo real quais mensagens estão sendo copiadas e para onde estão indo, respeitando os delays de segurança.
4. Para parar, clique em **⏹️ Parar Disparos**.

</details>

<br>

### 💡 Pro Tips for Safety
- **Interval**: We recommend keeping the interval above `60` seconds to avoid flood limits.
- **Targets**: Do not broadcast to more than 50 groups at once with a single account.
- **Content**: Avoid sending spam, as user reports are the #1 cause of bans.

## 📦 Compilation to EXE

To generate a standalone Windows executable without a background console:
```powershell
py -m PyInstaller --noconsole --onefile --icon=icon.ico --add-data "locales.json;." --add-data "icon.ico;." --collect-all customtkinter main_gui.py
```
> **Note:** The compiled code natively uses sys._MEIPASS to unpack resources. Make sure your locales.json and icon.ico (or .png) are passed correctly in the --add-data flags during compilation.

## 📜 License
This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details. 
You are free to use, modify, and distribute this software as you see fit.

Created by [IurySF](https://github.com/iurysf). Feel free to open an Issue or submit a Pull Request!
