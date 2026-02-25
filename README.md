# Telegram Auto-Message Bot

A modern, multi-threaded Telegram UserBot with a graphical interface (GUI). It allows you to monitor a source chat and automatically broadcast the latest messages (Text, Photos, Videos, Documents) to multiple target groups.

## 🚀 Features

- **Modern UI**: Built with CustomTkinter.
- **Stealth Mode**: Operates from the system tray with notifications.
- **Safe Broadcasting**: Includes anti-ban measures like random jitter and shuffling of target IDs.
- **Smart Login**: Handles SMS codes and 2FA via UI.
- **Portability**: Ready for PyInstaller compilation into a single `.exe`.

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

To generate a standalone Windows executable:
```powershell
py -m PyInstaller --noconsole --onefile --icon=icon.ico --add-data "locales.json;." --add-data "icon.ico;." --collect-all customtkinter main_gui.py
```

## 📜 Credits
Created by [IurySF](https://github.com/iurysf)
