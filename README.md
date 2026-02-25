# Telegram Auto-Message Bot

A modern, multi-threaded Telegram UserBot with a graphical interface (GUI). It allows you to monitor a source chat and automatically broadcast the latest messages (Text, Photos, Videos, Documents) to multiple target groups using advanced anti-detection techniques.

> ⚠️ **Disclaimer:** This tool is intended for educational purposes only. Automating personal Telegram accounts (UserBots) violates Telegram's Terms of Service. Use this software responsibly and at your own risk. The author is not responsible for any banned accounts or damages caused by the misuse of this tool.

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

![Main UI](https://private-user-images.githubusercontent.com/98192149/554869280-459535a9-4283-42b2-84aa-1cfcc8e64444.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NzIwMzc2MTQsIm5iZiI6MTc3MjAzNzMxNCwicGF0aCI6Ii85ODE5MjE0OS81NTQ4NjkyODAtNDU5NTM1YTktNDI4My00MmIyLTg0YWEtMWNmY2M4ZTY0NDQ0LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNjAyMjUlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjYwMjI1VDE2MzUxNFomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTE1YWU3MTcxNDIxMDFkNzM0MWQ2YWI3ZjM1MGRiOTNlNDU1MTE5MGEzNmJjNTliY2M3NDBmN2ZiYWYwZGYwMWYmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.7LAtDzhyINrXVGYPPqJgny6O5lex9M-Oa9onD0xQ2lk)

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
   ```bash
   python main_gui.py
   ```

## 📦 Compilation to EXE

To generate a standalone Windows executable without a background console:
```powershell
py -m PyInstaller --noconsole --onefile --icon=icon.ico --add-data "locales.json;." --add-data "icon.ico;." --collect-all customtkinter main_gui.py
```
> **Note:** Ensure `locales.json` and `icon.ico` are placed in the same directory as the generated `.exe` for the application to load properly.

## 📜 Credits
Created by [IurySF](https://github.com/iurysf)
