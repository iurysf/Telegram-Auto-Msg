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
        "[dim]Premium Interface[/dim]",
        border_style="green"
    ))

async def setup_wizard():
    show_header()
    console.print("[yellow]Iniciando Assistente de Configuração...[/yellow]\n")
    
    api_id = Prompt.ask("Digite seu API ID")
    api_hash = Prompt.ask("Digite seu API Hash")
    phone = Prompt.ask("Digite seu Telefone (ex: 5522999999999)")

    console.print("\n[cyan]Conectando ao Telegram...[/cyan]")
    # We run this coro in the engine loop
    future = engine.run_coro(engine.connect(api_id, api_hash, phone))
    result = await asyncio.wrap_future(future)
    
    if result == "NEED_CODE":
        code = Prompt.ask("[bold yellow]Digite o código SMS recebido[/bold yellow]")
        # Login
        future = engine.run_coro(engine.login(code))
        login_result = await asyncio.wrap_future(future)
        
        if login_result == "NEED_2FA":
            password = Prompt.ask("Digite sua senha de Verificação em 2 Etapas", password=True)
            future = engine.run_coro(engine.login(code, password))
            login_result = await asyncio.wrap_future(future)
        
        if login_result != "SUCCESS":
            console.print(f"[bold red]Erro no login: {login_result}[/bold red]")
            Prompt.ask("\nPressione ENTER para tentar novamente")
            return False

    # Save to config
    config = load_config()
    config.update({
        "api_id": api_id,
        "api_hash": api_hash,
        "phone": phone
    })
    save_config(config)
    console.print("\n[bold green]Configuração salva com sucesso![/bold green]")
    time.sleep(2)
    return True

async def list_groups():
    show_header()
    console.print("[yellow]Buscando grupos e chats...[/yellow]")
    
    future = engine.run_coro(engine.get_dialogs())
    dialogs = await asyncio.wrap_future(future)
    
    table = Table(title="Seus Grupos e IDs")
    table.add_column("Nome", style="cyan")
    table.add_column("ID", style="magenta")
    
    for d in dialogs:
        table.add_row(d["name"], str(d["id"]))
    
    console.print(table)
    Prompt.ask("\nPressione ENTER para voltar ao menu")

async def save_new_groups():
    show_header()
    console.print("[yellow]Buscando seus Top 100 Diálogos...[/yellow]")
    
    future = engine.run_coro(engine.get_dialogs(limit=100))
    dialogs = await asyncio.wrap_future(future)
    
    if not dialogs:
        console.print("[red]Nenhum grupo encontrado ou erro na conexão.[/red]")
        Prompt.ask("\nPressione ENTER para voltar")
        return

    table = Table(title="Top 100 Diálogos")
    table.add_column("#", style="bold yellow")
    table.add_column("Nome", style="cyan")
    table.add_column("ID", style="magenta")
    
    for i, d in enumerate(dialogs, 1):
        table.add_row(str(i), d["name"], str(d["id"]))
    
    console.print(table)
    
    indices_str = Prompt.ask("\nDigite os números dos grupos que deseja salvar (separados por vírgula)")
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
        console.print(f"\n[bold green]Sucesso! {count} grupos foram salvos vinculados à sua conta.[/bold green]")
        time.sleep(2)
    except ValueError:
        console.print("[red]Erro: Digite apenas números separados por vírgula.[/red]")
        time.sleep(2)

async def view_saved_groups():
    show_header()
    config = load_config()
    saved_groups = config.get("groups", {})
    
    if not saved_groups:
        console.print("[yellow]Você ainda não salvou nenhum grupo.[/yellow]")
        Prompt.ask("\nPressione ENTER para voltar")
        return

    table = Table(title="Grupos Salvos no config.json")
    table.add_column("Nome", style="cyan")
    table.add_column("ID", style="magenta")
    
    for gid, info in saved_groups.items():
        table.add_row(info.get("name", "Unknown"), gid)
    
    console.print(table)
    Prompt.ask("\nPressione ENTER para voltar")

async def manage_groups():
    while True:
        show_header()
        console.print("[bold yellow]📂 Gerenciar Grupos Alvo[/bold yellow]\n")
        
        table = Table(show_header=False, box=None)
        table.add_column("Opção", style="bold cyan")
        table.add_column("Descrição")
        
        table.add_row("1", "📥 Salvar novos grupos (Top 100)")
        table.add_row("2", "📋 Ver grupos salvos")
        table.add_row("3", "⬅️ Voltar")
        
        console.print(table)
        
        choice = Prompt.ask("\nEscolha uma opção", choices=["1", "2", "3"])
        
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
            console.print("[red]Erro: Configurações de CLI ausentes no config.json para modo headless.[/red]")
            sys.exit(1)
    else:
        show_header()
        
        # Automatically use saved groups from config.json
        saved_groups = config.get("groups", {})
        
        if not saved_groups:
            console.print("[yellow]Aviso: Nenhum grupo salvo encontrado no config.json.[/yellow]")
            console.print("[cyan]Vá em 'Gerenciar Grupos Alvo' para salvar os grupos primeiro.[/cyan]")
            dest_ids_str = Prompt.ask("\nOu digite os IDs de Destino manualmente agora (separados por vírgula)", default=cli_defaults.get("destination_ids", ""))
        else:
            dest_ids_str = ",".join(saved_groups.keys())
            console.print(f"[green]Utilizando {len(saved_groups)} grupos salvos automaticamente.[/green]")

        source_id = Prompt.ask("ID do Grupo Fonte", default=str(cli_defaults.get("source_id", "")))
        interval_val = int(Prompt.ask("Intervalo (segundos)", default=str(cli_defaults.get("interval", 60))))
        
        # Save defaults
        config["cli_defaults"] = {
            "source_id": source_id,
            "destination_ids": dest_ids_str,
            "interval": interval_val
        }
        save_config(config)

    dest_ids = [did.strip() for did in dest_ids_str.split(",") if did.strip()]
    if not dest_ids:
        console.print("[red]Erro: Nenhum grupo de destino configurado.[/red]")
        time.sleep(2)
        return
    
    if not headless:
        show_header()
        console.print(f"[bold green]Bot Iniciado![/bold green]")
        console.print(f"Fonte: [cyan]{source_id}[/cyan] | Destinos: [cyan]{len(dest_ids)} grupos[/cyan] | Intervalo: [cyan]{interval_val}s[/cyan]")
        console.print("[dim]Pressione Ctrl+C para parar e voltar ao menu[/dim]\n")
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
            console.print("\n[yellow]Broadcaster parado.[/yellow]")
            time.sleep(2)

async def reset_app():
    show_header()
    if Confirm.ask("[bold red]ATENÇÃO: Isso apagará todas as configurações e a sessão. Continuar?[/bold red]"):
        try:
            # RELEASE LOCK FIRST
            console.print("[cyan]Desconectando e liberando arquivos...[/cyan]")
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
            
            console.print("[green]Reset concluído com sucesso![/green]")
            console.print("\n[bold yellow]IMPORTANTE: No Windows, recomendamos reiniciar o script manualmente.[/bold yellow]")
            console.print("[bold cyan]Por favor, execute: py main_cli.py[/bold cyan]")
            sys.exit(0)
        except Exception as e:
            console.print(f"[red]Erro ao resetar: {e}[/red]")
            Prompt.ask("Pressione ENTER para voltar")

async def main_menu():
    while True:
        show_header()
        table = Table(show_header=False, box=None)
        table.add_column("Opção", style="bold cyan")
        table.add_column("Descrição")
        
        table.add_row("1", "🚀 Iniciar Broadcaster (Clonagem)")
        table.add_row("2", "📂 Gerenciar Grupos Alvo")
        table.add_row("3", "🔄 Resetar Configurações")
        table.add_row("4", "❌ Sair")
        
        console.print(table)
        
        choice = Prompt.ask("\nEscolha uma opção", choices=["1", "2", "3", "4"])
        
        if choice == "1":
            await run_broadcaster()
        elif choice == "2":
            await manage_groups()
        elif choice == "3":
            await reset_app()
        elif choice == "4":
            console.print("[yellow]Saindo elegantemente...[/yellow]")
            sys.exit(0)

async def run_headless():
    config = load_config()
    api_id = config.get("api_id")
    api_hash = config.get("api_hash")
    
    if not api_id or not api_hash:
        console.print("[bold red]ERRO FATAL: Credenciais ausentes no config.json.[/bold red]")
        console.print("Rode o CLI sem --headless uma vez para configurar.")
        sys.exit(1)

    console.print("[cyan]Conectando silenciosamente...[/cyan]")
    try:
        future = engine.run_coro(engine.check_session(api_id, api_hash))
        is_logged = await asyncio.wrap_future(future)
        
        if not is_logged:
            console.print("[bold red]ERRO FATAL: Sessão expirada ou inválida.[/bold red]")
            console.print("Rode o CLI sem --headless para refazer o login.")
            sys.exit(1)
            
        console.print("[bold green]Sessão válida encontrada![/bold green]")
        
        # Start broadcaster background task
        broadcaster_task = asyncio.create_task(run_broadcaster(headless=True))
        
        console.print("[green]Bot rodando em background (VPS Mode). Ctrl+C para sair.[/green]")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Encerrando por interrupção do usuário...[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Erro inesperado no modo headless: {e}[/bold red]")
    finally:
        sys.exit(0)

async def boot():
    parser = argparse.ArgumentParser(description="Auto-Telegram CLI")
    parser.add_argument("--headless", action="store_true", help="Inicia o bot direto em modo background")
    args = parser.parse_args()

    config = load_config()
    
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
        console.print("[cyan]Verificando sessão...[/cyan]")
        future = engine.run_coro(engine.check_session(config["api_id"], config["api_hash"]))
        try:
            is_logged = await asyncio.wrap_future(future)
        except Exception:
            is_logged = False
        
        if not is_logged:
            console.print("[yellow]Sessão expirada. Redirecionando para login...[/yellow]")
            time.sleep(2)
            await setup_wizard()

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
