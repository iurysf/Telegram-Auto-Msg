import sys
import os
import json
import time
import asyncio
import argparse
import logging
from datetime import datetime

# Libs for visual quality
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.live import Live
    from rich.logging import RichHandler
except ImportError:
    print("Erro: A biblioteca 'rich' é necessária. Instale com: pip install rich")
    sys.exit(1)

# Project imports
from telegram_engine import TelegramEngine

# Global objects
console = Console()
engine = TelegramEngine()
CONFIG_FILE = "config.json"

# --- Localization Infrastructure ---
current_lang = "pt"
i18n = {}

def resource_path(relative_path):
    """ Returns the absolute path of the file, whether running in Python or the compiled .exe """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_locales():
    """Load language dictionary from locales.json"""
    loc_path = resource_path("locales.json")
    if os.path.exists(loc_path):
        try:
            with open(loc_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading locales.json: {e}")
    
    # Basic fallback
    return {
        "en": {"log_ready": "Ready.", "cli_header_sub": "Premium Interface"},
        "pt": {"log_ready": "Pronto.", "cli_header_sub": "Interface Premium"}
    }

async def choose_language_wizard():
    global current_lang
    clear_screen()
    console.print(Panel.fit(
        "[bold cyan]Select your language / Escolha seu idioma[/bold cyan]",
        border_style="cyan"
    ))
    console.print("\n1. English")
    console.print("2. Português (Brasil)\n")
    
    choice = Prompt.ask("Choice / Escolha", choices=["1", "2"])
    current_lang = "en" if choice == "1" else "pt"
    
    config = load_config()
    config["language"] = current_lang
    save_config(config)
    
    console.print(f"\n[green]Ready! / Pronto! ({current_lang})[/green]")
    time.sleep(1)

# Initialize I18N
i18n = load_locales()

class CliLoggerHandler(logging.Handler):
    """Custom handler to suppress/show logs depending on the current screen."""
    def __init__(self):
        super().__init__()
        self.show_logs = False
        self.log_buffer = []

    def emit(self, record):
        try:
            msg = self.format(record)
            if self.show_logs:
                console.print(f"[dim]{datetime.now().strftime('%H:%M:%S')}[/dim] {msg}")
            else:
                self.log_buffer.append(msg)
                if len(self.log_buffer) > 50:
                    self.log_buffer.pop(0)
        except Exception:
            pass

# Setup Logging
cli_handler = CliLoggerHandler()
cli_handler.setFormatter(logging.Formatter('%(message)s'))
engine.logger.addHandler(cli_handler)
engine.logger.setLevel(logging.INFO)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        console.print(f"[red]Erro ao salvar config: {e}[/red]")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_header():
    clear_screen()
    console.print(Panel.fit(
        "[bold green]Auto-Telegram Bot CLI[/bold green]\n"
        f"[dim]{i18n[current_lang]['cli_header_sub']}[/dim]",
        border_style="green"
    ))

async def setup_wizard():
    show_header()
    console.print(f"[yellow]{i18n[current_lang]['cli_wizard_start']}[/yellow]\n")
    
    api_id = Prompt.ask(i18n[current_lang]["cli_api_id_prompt"])
    api_hash = Prompt.ask(i18n[current_lang]["cli_api_hash_prompt"])
    phone = Prompt.ask(i18n[current_lang]["cli_phone_prompt"])

    console.print(f"\n[cyan]{i18n[current_lang]['cli_connecting']}[/cyan]")
    # We run this coro in the engine loop
    future = engine.run_coro(engine.connect(api_id, api_hash, phone))
    result = await asyncio.wrap_future(future)
    
    if result == "NEED_CODE":
        code = Prompt.ask(f"[bold yellow]{i18n[current_lang]['cli_sms_prompt']}[/bold yellow]")
        # Login
        future = engine.run_coro(engine.login(code))
        login_result = await asyncio.wrap_future(future)
        
        if login_result == "NEED_2FA":
            password = Prompt.ask(i18n[current_lang]["cli_2fa_prompt"], password=True)
            future = engine.run_coro(engine.login(code, password))
            login_result = await asyncio.wrap_future(future)
        
        if login_result != "SUCCESS":
            console.print(f"[bold red]{i18n[current_lang]['cli_login_error'].format(res=login_result)}[/bold red]")
            Prompt.ask(f"\n{i18n[current_lang]['cli_login_retry']}")
            return False

    # Save to config
    config = load_config()
    config.update({
        "api_id": api_id,
        "api_hash": api_hash,
        "phone": phone
    })
    save_config(config)
    console.print(f"\n[bold green]{i18n[current_lang]['cli_config_saved']}[/bold green]")
    time.sleep(2)
    return True

async def list_groups():
    show_header()
    console.print(f"[yellow]{i18n[current_lang]['cli_fetching_chats']}[/yellow]")
    
    future = engine.run_coro(engine.get_dialogs())
    dialogs = await asyncio.wrap_future(future)
    
    table = Table(title=i18n[current_lang]["cli_table_chats_title"])
    table.add_column(i18n[current_lang]["cli_table_col_name"], style="cyan")
    table.add_column(i18n[current_lang]["cli_table_col_id"], style="magenta")
    
    for d in dialogs:
        table.add_row(d["name"], str(d["id"]))
    
    console.print(table)
    Prompt.ask(f"\n{i18n[current_lang]['cli_press_enter_back']}")

async def save_new_groups():
    show_header()
    console.print(f"[yellow]{i18n[current_lang]['cli_fetching_top_100']}[/yellow]")
    
    future = engine.run_coro(engine.get_dialogs(limit=100))
    dialogs = await asyncio.wrap_future(future)
    
    if not dialogs:
        console.print(f"[red]{i18n[current_lang]['cli_no_chats']}[/red]")
        Prompt.ask(f"\n{i18n[current_lang]['cli_press_enter_back']}")
        return

    table = Table(title=i18n[current_lang]["cli_table_top_100_title"])
    table.add_column("#", style="bold yellow")
    table.add_column(i18n[current_lang]["cli_table_col_name"], style="cyan")
    table.add_column(i18n[current_lang]["cli_table_col_id"], style="magenta")
    
    for i, d in enumerate(dialogs, 1):
        table.add_row(str(i), d["name"], str(d["id"]))
    
    console.print(table)
    
    indices_str = Prompt.ask(f"\n{i18n[current_lang]['cli_prompt_select_indices']}")
    try:
        selected_indices = [int(idx.strip()) for idx in indices_str.split(",") if idx.strip()]
        
        config = load_config()
        if "groups" not in config:
            config["groups"] = {}
            
        count = 0
        for idx in selected_indices:
            if 1 <= idx <= len(dialogs):
                d = dialogs[idx-1]
                config["groups"][str(d["id"])] = {
                    "name": d["name"],
                    "selected": True
                }
                count += 1
        
        save_config(config)
        console.print(f"\n[bold green]{i18n[current_lang]['cli_save_success'].format(n=count)}[/bold green]")
        time.sleep(2)
    except ValueError:
        console.print(f"[red]{i18n[current_lang]['cli_error_numbers_only']}[/red]")
        time.sleep(2)

async def view_saved_groups():
    show_header()
    config = load_config()
    saved_groups = config.get("groups", {})
    
    if not saved_groups:
        console.print(f"[yellow]{i18n[current_lang]['cli_no_saved_groups']}[/yellow]")
        Prompt.ask(f"\n{i18n[current_lang]['cli_press_enter_back']}")
        return

    table = Table(title=i18n[current_lang]["cli_table_saved_title"])
    table.add_column(i18n[current_lang]["cli_table_col_name"], style="cyan")
    table.add_column(i18n[current_lang]["cli_table_col_id"], style="magenta")
    
    for gid, info in saved_groups.items():
        table.add_row(info.get("name", i18n[current_lang]["cli_unknown"]), gid)
    
    console.print(table)
    Prompt.ask("\nPressione ENTER para voltar")

async def manage_groups():
    while True:
        show_header()
        console.print(f"[bold yellow]{i18n[current_lang]['cli_manage_title']}[/bold yellow]\n")
        
        table = Table(show_header=False, box=None)
        table.add_column("Opção", style="bold cyan")
        table.add_column("Descrição")
        
        table.add_row("1", i18n[current_lang]["cli_menu_save_new"])
        table.add_row("2", i18n[current_lang]["cli_menu_view_saved"])
        table.add_row("3", i18n[current_lang]["cli_menu_back"])
        
        console.print(table)
        
        choice = Prompt.ask(f"\n{i18n[current_lang]['cli_choice_prompt']}", choices=["1", "2", "3"])
        
        if choice == "1":
            await save_new_groups()
        elif choice == "2":
            await view_saved_groups()
        elif choice == "3":
            break

async def run_broadcaster(headless=False):
    config = load_config()
    cli_defaults = config.get("cli_defaults", {})
    
    if headless:
        source_id = cli_defaults.get("source_id")
        dest_ids_str = cli_defaults.get("destination_ids", "")
        interval_val = int(cli_defaults.get("interval", 60))
        
        if not source_id or not dest_ids_str:
            console.print(f"[red]{i18n[current_lang]['cli_headless_error']}[/red]")
            sys.exit(1)
    else:
        show_header()
        
        # Automatically use saved groups from config.json
        saved_groups = config.get("groups", {})
        
        if not saved_groups:
            console.print(f"[yellow]{i18n[current_lang]['cli_warning_no_groups']}[/yellow]")
            console.print(f"[cyan]{i18n[current_lang]['cli_instruction_manage']}[/cyan]")
            dest_ids_str = Prompt.ask(f"\n{i18n[current_lang]['cli_manual_dest_prompt']}", default=cli_defaults.get("destination_ids", ""))
        else:
            dest_ids_str = ",".join(saved_groups.keys())
            console.print(f"[green]{i18n[current_lang]['cli_auto_dest_msg'].format(n=len(saved_groups))}[/green]")

        source_id = Prompt.ask(i18n[current_lang]["cli_source_id_prompt"], default=str(cli_defaults.get("source_id", "")))
        interval_val = int(Prompt.ask(i18n[current_lang]["cli_interval_prompt"], default=str(cli_defaults.get("interval", 60))))
        
        # Save defaults
        config["cli_defaults"] = {
            "source_id": source_id,
            "destination_ids": dest_ids_str,
            "interval": interval_val
        }
        save_config(config)

    dest_ids = [did.strip() for did in dest_ids_str.split(",") if did.strip()]
    if not dest_ids:
        console.print(f"[red]{i18n[current_lang]['cli_error_no_dest']}[/red]")
        time.sleep(2)
        return
    
    if not headless:
        show_header()
        console.print(f"[bold green]{i18n[current_lang]['cli_bot_started_status']}[/bold green]")
        console.print(i18n[current_lang]["cli_status_bar"].format(src=source_id, dst=len(dest_ids), int=interval_val))
        console.print(f"[dim]{i18n[current_lang]['cli_stop_hint']}[/dim]\n")
        console.print("-" * 50)

    cli_handler.show_logs = True
    engine.is_running = True
    
    try:
        while engine.is_running:
            try:
                # Capture message
                future = engine.run_coro(engine.get_last_message(source_id))
                msg = await asyncio.wrap_future(future)
                
                if msg:
                    engine.logger.info(f"Nova mensagem capturada de {source_id}. Enviando...")
                    future = engine.run_coro(engine.send_broadcast(msg, dest_ids))
                    await asyncio.wrap_future(future)
                else:
                    engine.logger.info("Nenhuma mensagem nova encontrada ou erro ao acessar fonte.")
                
                engine.logger.info(f"Aguardando {interval_val}s para a próxima verificação...")
                await asyncio.sleep(interval_val)
            except Exception as e:
                engine.logger.error(f"Erro no loop do Broadcaster: {e}")
                await asyncio.sleep(10)
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        engine.is_running = False
        cli_handler.show_logs = False
        if not headless:
            console.print(f"\n[yellow]{i18n[current_lang]['cli_broadcaster_stopped']}[/yellow]")
            time.sleep(2)

async def reset_settings():
    show_header()
    if not Confirm.ask(f"[bold red]{i18n[current_lang]['cli_reset_warning']}[/bold red]"):
        return
    
    try:
        # RELEASE LOCK FIRST
        console.print(f"[cyan]{i18n[current_lang]['cli_reset_disconnecting']}[/cyan]")
        future = engine.run_coro(engine.disconnect())
        await asyncio.wrap_future(future)
        
        # Delay para o Windows 
        await asyncio.sleep(1)
        
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
            
        for f in os.listdir("."):
            if f.endswith(".session") or f.endswith(".session-journal"):
                for _ in range(3): # Tentativas para lock do Windows
                    try:
                        os.remove(f)
                        break
                    except Exception:
                        time.sleep(1)
        
        console.print(f"[bold green]{i18n[current_lang]['cli_reset_success']}[/bold green]")
        
        if os.name == 'nt':
            console.print(f"\n[cyan]{i18n[current_lang]['cli_reset_windows_hint']}[/cyan]")
            console.print(f"[bold yellow]{i18n[current_lang]['cli_reset_run_cmd']}[/bold yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]{i18n[current_lang]['cli_reset_error'].format(e=e)}[/red]")
        return

async def main_menu():
    while True:
        show_header()
        
        table = Table(show_header=False, box=None)
        table.add_column("Opção", style="bold cyan")
        table.add_column("Descrição")
        
        table.add_row("1", i18n[current_lang]["cli_main_menu_start"])
        table.add_row("2", i18n[current_lang]["cli_main_menu_manage"])
        table.add_row("3", i18n[current_lang]["cli_main_menu_reset"])
        table.add_row("4", i18n[current_lang]["cli_main_menu_exit"])
        
        console.print(table)
        
        choice = Prompt.ask(f"\n{i18n[current_lang]['cli_choice_prompt']}", choices=["1", "2", "3", "4"])
        
        if choice == "1":
            await run_broadcaster(headless=False)
        elif choice == "2":
            await manage_groups()
        elif choice == "3":
            await reset_settings()
        elif choice == "4":
            console.print(f"[yellow]{i18n[current_lang]['cli_exiting']}[/yellow]")
            break

async def run_headless():
    config = load_config()
    
    if not config.get("api_id") or not config.get("api_hash") or not config.get("phone"):
        console.print(f"[bold red]{i18n[current_lang]['cli_headless_error_missing']}[/bold red]")
        console.print(f"[cyan]{i18n[current_lang]['cli_headless_hint']}[/cyan]")
        sys.exit(1)
    
    console.print(f"[cyan]{i18n[current_lang]['cli_silent_connect']}[/cyan]")
    try:
        future = engine.run_coro(engine.check_session(config.get("api_id"), config.get("api_hash")))
        session_valid = await asyncio.wrap_future(future)

        if not session_valid:
            console.print(f"[bold red]{i18n[current_lang]['cli_headless_error_session']}[/bold red]")
            console.print(f"[cyan]{i18n[current_lang]['cli_headless_hint_login']}[/cyan]")
            sys.exit(1)
        
        console.print(f"[green]{i18n[current_lang]['cli_session_valid']}[/green]")
        
        # Start broadcaster background task
        await run_broadcaster(headless=True)
        
    except KeyboardInterrupt:
        console.print(f"\n[yellow]{i18n[current_lang]['cli_interrupt_msg']}[/yellow]")
    except Exception as e:
        console.print(f"[bold red]{i18n[current_lang]['cli_fatal_boot'].format(e=e)}[/bold red]")
    finally:
        sys.exit(0)

async def boot():
    global current_lang
    parser = argparse.ArgumentParser(description="Auto-Telegram CLI")
    parser.add_argument("--headless", action="store_true", help="Start the bot directly in background mode")
    args = parser.parse_args()

    config = load_config()
    
    # --- LANGUAGE SELECTION (First boot) ---
    if "language" not in config:
        await choose_language_wizard()
        config = load_config() # Reload with lang
    else:
        current_lang = config["language"]

    if args.headless:
        await run_headless()
        return

    # Check if configured
    if not config.get("api_id") or not config.get("api_hash"):
        success = await setup_wizard()
        if not success:
            sys.exit(1)
    else:
        # Silent connect check
        show_header()
        console.print(f"[cyan]{i18n[current_lang]['cli_verifying_session']}[/cyan]")
        future = engine.run_coro(engine.check_session(config["api_id"], config["api_hash"]))
        try:
            is_logged = await asyncio.wrap_future(future)
        except Exception:
            is_logged = False
        
        if not is_logged:
            console.print(f"[red]{i18n[current_lang]['cli_session_expired']}[/red]")
            time.sleep(2)
            await setup_wizard()
        else:
            console.print(f"[green]{i18n[current_lang]['cli_session_valid']}[/green]")
            time.sleep(1)

    await main_menu()

if __name__ == "__main__":
    try:
        asyncio.run(boot())
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    except Exception as e:
        console.print(f"[bold red]Erro fatal na inicialização: {e}[/bold red]")
