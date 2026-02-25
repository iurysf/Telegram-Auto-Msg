import customtkinter as ctk
import threading
import time
import logging
from telegram_engine import TelegramEngine
import json
import os
import sys
import pystray
import webbrowser
from PIL import Image, ImageDraw
from dotenv import load_dotenv
import ctypes

# Fix: Force Windows to show the correct icon in the Taskbar
try:
    myappid = 'iurysf.automsg.bot.v1' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

load_dotenv()

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Telegram MSG Bot")
        self.geometry("800x600")
        self.after(200, lambda: self.state('zoomed')) # Delay to avoid CTk displacement bug
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Set window icon
        def set_icon():
            try:
                icon_path = resource_path("icon.ico")
                if os.path.exists(icon_path):
                    self.iconbitmap(icon_path)
            except: pass
        self.after(200, set_icon)

        self.engine = TelegramEngine()
        self.group_vars = {} # {id: (checkbox, frame)}
        self._is_closing = False
        
        # 1. Variable that stores the current language ("en" or "pt")
        self.current_lang = "pt" 
        
        # 2. Load translations from external file
        self.i18n = self.load_locales()

        # 3. Check for first run BEFORE building the UI
        self.check_first_run()
        
        self.setup_ui()
        self.load_config()
        
        # 4. Setup Tray Icon
        self.setup_tray()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Unmap>", self.on_minimize)

    def setup_tray(self):
        """Setup the system tray icon"""
        # Try to load the icon from file, else generate one
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.tray_icon_img = Image.open(icon_path)
        else:
            self.tray_icon_img = self.create_tray_icon()
            
        self.tray_menu = pystray.Menu(
            pystray.MenuItem(self.i18n[self.current_lang]["tray_restore"], lambda: self.after(0, self.on_restore), default=True),
            pystray.MenuItem(self.i18n[self.current_lang]["tray_exit"], lambda: self.after(0, self.on_closing))
        )
        self.icon = pystray.Icon("AutoTelegramBot", self.tray_icon_img, "AutoTelegram Bot", self.tray_menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def create_tray_icon(self):
        """Generate a simple icon via code"""
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color=(31, 83, 141)) # Theme blue
        dc = ImageDraw.Draw(image)
        dc.rectangle((width // 4, height // 4, width * 3 // 4, height * 3 // 4), fill=(255, 255, 255))
        return image

    def on_minimize(self, event):
        """Intercept minimize to hide the window"""
        if self._is_closing: return
        if self.state() == 'iconic':
            self.withdraw()
            if hasattr(self, 'icon'):
                self.icon.notify(
                    self.i18n[self.current_lang]["tray_notify_msg"],
                    self.i18n[self.current_lang]["tray_notify_title"]
                )

    def on_restore(self):
        """Restore the window from tray"""
        self.deiconify()
        self.state('zoomed')
        self.lift()
        self.focus_force()

    def load_locales(self):
        """Load language dictionary from locales.json"""
        loc_path = resource_path("locales.json")
        if os.path.exists(loc_path):
            try:
                with open(loc_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading locales.json: {e}")
        
        # Basic fallback if the file is missing
        return {
            "en": {"log_ready": "Ready.", "sidebar_title": "Bot"},
            "pt": {"log_ready": "Pronto.", "sidebar_title": "Robô"}
        }

    def check_first_run(self):
        """Check if language is already configured. If not, open selection screen."""
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    conf = json.load(f)
                    if "language" in conf:
                        self.current_lang = conf["language"]
                        return
            except Exception:
                pass
        
        # If it reached here, language needs to be chosen
        self.withdraw() 
        self.show_language_selector()

    def show_language_selector(self):
        """Create a modal window for language selection"""
        popup = ctk.CTkToplevel(self)
        popup.title("Select Language / Selecione o Idioma")
        popup.geometry("400x250")
        popup.resizable(False, False)
        
        popup.attributes("-topmost", True)
        popup.grab_set() 

        # Centering
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (400 // 2)
        y = (popup.winfo_screenheight() // 2) - (250 // 2)
        popup.geometry(f"+{x}+{y}")

        ctk.CTkLabel(popup, text="Welcome! Choose your language:\nBem-vindo! Escolha seu idioma:", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(30, 20))

        lang_var = ctk.StringVar(value="Português (Brasil)")
        combo = ctk.CTkOptionMenu(popup, variable=lang_var, values=["English", "Português (Brasil)"], width=250, height=35)
        combo.pack(pady=10)

        def save_and_continue():
            choice = lang_var.get()
            self.current_lang = "en" if choice == "English" else "pt"
            popup.grab_release()
            popup.destroy()
            self.deiconify() 
            self.after(200, lambda: self.state('zoomed'))

        btn = ctk.CTkButton(popup, text="Continue / Continuar", command=save_and_continue, height=40)
        btn.pack(pady=(20, 0))
        popup.protocol("WM_DELETE_WINDOW", lambda: None)
        self.wait_window(popup)

    def setup_ui(self):
        # Main Grid Config
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ================= SIDEBAR =================
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#1e1e21")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1) # Push bottom logo to footer
        
        # Sidebar Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar, text=self.i18n[self.current_lang]["sidebar_title"], 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 10))

        # Sidebar Button
        self.fetch_chats_btn = ctk.CTkButton(
            self.sidebar, text=self.i18n[self.current_lang]["btn_fetch"], 
            height=40, font=ctk.CTkFont(weight="bold"),
            command=self.handle_fetch_chats
        )
        self.fetch_chats_btn.grid(row=1, column=0, padx=20, pady=20)
        
        # Sidebar Footer Credits
        self.credits_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.credits_frame.grid(row=4, column=0, pady=20, sticky="s")

        self.version_label = ctk.CTkLabel(self.credits_frame, text="v1.0\nBy IurySF", text_color="gray")
        self.version_label.pack()

        self.github_link = ctk.CTkLabel(
            self.credits_frame, 
            text="github.com/iurysf", 
            text_color="#1864ab", 
            cursor="hand2",
            font=ctk.CTkFont(size=12, underline=True)
        )
        self.github_link.pack()
        self.github_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/iurysf"))


        # ================= MAIN PANEL (Centered and Responsive) =================
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew")
        
        # Horizontal centering: columns 0 and 2 expand
        self.main_container.grid_columnconfigure((0, 2), weight=1)
        # Allow content to grow vertically (row 0)
        self.main_container.grid_rowconfigure(0, weight=1) 

        # Content frame with maximum suggested width
        self.main_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=30)
        
        # Ensure main_frame internal columns expand
        self.main_frame.grid_columnconfigure(0, weight=1)


        # --- HEADER (Cards side by side) ---
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.header_frame.grid_columnconfigure((0, 1), weight=1)

        # Card 1: API Credentials
        self.api_card = ctk.CTkFrame(self.header_frame, corner_radius=15)
        self.api_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(self.api_card, text=self.i18n[self.current_lang]["card_api"], font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))
        self.api_id_entry = self.add_input(self.api_card, self.i18n[self.current_lang]["api_id"], self.i18n[self.current_lang]["placeholder_id"])
        self.api_hash_entry = self.add_input(self.api_card, self.i18n[self.current_lang]["api_hash"], self.i18n[self.current_lang]["placeholder_hash"])
        self.phone_entry = self.add_input(self.api_card, self.i18n[self.current_lang]["phone"], "+55 11 99999-9999")

        # Card 2: Bot Settings
        self.settings_card = ctk.CTkFrame(self.header_frame, corner_radius=15)
        self.settings_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        ctk.CTkLabel(self.settings_card, text=self.i18n[self.current_lang]["card_bot"], font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))
        # --- CUSTOM SOURCE ENTRY COM BOTÃO DE PESQUISA ---
        source_frame = ctk.CTkFrame(self.settings_card, fg_color="transparent")
        source_frame.pack(fill="x", padx=20, pady=8)
        
        ctk.CTkLabel(source_frame, text=self.i18n[self.current_lang]["source"], width=110, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        self.source_entry = ctk.CTkEntry(source_frame, placeholder_text=self.i18n[self.current_lang]["placeholder_source"], border_width=1)
        self.source_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.search_src_btn = ctk.CTkButton(source_frame, text="🔍", width=35, fg_color="#4b4b4b", hover_color="#333333", command=self.open_source_search)
        self.search_src_btn.pack(side="right")
        # -------------------------------------------------
        self.interval_entry = self.add_input(self.settings_card, self.i18n[self.current_lang]["interval"], self.i18n[self.current_lang]["placeholder_interval"], width=80)


        # --- TARGET GROUPS SECTION ---
        self.targets_card = ctk.CTkFrame(self.main_frame, corner_radius=15)
        self.targets_card.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        
        ctk.CTkLabel(self.targets_card, text=self.i18n[self.current_lang]["card_targets"], font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(fill="x", padx=20, pady=(15, 0))
        self.targets_scroll_frame = ctk.CTkScrollableFrame(self.targets_card, height=160, fg_color="transparent")
        self.targets_scroll_frame.pack(fill="x", padx=10, pady=10)


        # --- ACTION BUTTONS ---
        self.btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_frame.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        
        self.connect_btn = ctk.CTkButton(
            self.btn_frame, text=self.i18n[self.current_lang]["btn_connect"], 
            height=45, fg_color="#1864ab", hover_color="#124c82", 
            font=ctk.CTkFont(size=14, weight="bold"), command=self.handle_connect
        )
        self.connect_btn.pack(side="left", padx=(0, 10), expand=True, fill="x")

        self.start_btn = ctk.CTkButton(
            self.btn_frame, text=self.i18n[self.current_lang]["btn_start"], 
            height=45, state="disabled", fg_color="#2b8a3e", hover_color="#206a2f",
            font=ctk.CTkFont(size=14, weight="bold"), command=self.toggle_bot
        )
        self.start_btn.pack(side="right", padx=(10, 0), expand=True, fill="x")


        # --- CONSOLE TERMINAL ---
        self.console_card = ctk.CTkFrame(self.main_frame, corner_radius=15, fg_color="#121212")
        self.console_card.grid(row=3, column=0, sticky="nsew")
        
        # Force row 3 (console) to expand and take rest of screen
        self.main_frame.grid_rowconfigure(3, weight=1) 
        
        self.console = ctk.CTkTextbox(
            self.console_card, fg_color="transparent", 
            text_color="#4AF626", # Terminal green
            font=ctk.CTkFont(family="Consolas", size=13)
        )
        self.console.pack(fill="both", expand=True, padx=15, pady=15)
        self.log(self.i18n[self.current_lang]["log_ready"])

    def add_input(self, parent, label_text, placeholder, width=None):
        """Helper function to create standardized inputs"""
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=8)
        
        l = ctk.CTkLabel(f, text=label_text, width=110, anchor="w", font=ctk.CTkFont(weight="bold"))
        l.pack(side="left")
        
        if width:
            e = ctk.CTkEntry(f, placeholder_text=placeholder, width=width, border_width=1)
            e.pack(side="left")
        else:
            e = ctk.CTkEntry(f, placeholder_text=placeholder, border_width=1)
            e.pack(side="right", fill="x", expand=True)
            
        return e

    def add_group_row(self, group_id, group_name, is_checked=False):
        if str(group_id) in self.group_vars:
            return

        row_frame = ctk.CTkFrame(self.targets_scroll_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)
        row_frame.grid_columnconfigure(0, weight=1) # Checkbox expands

        chk = ctk.CTkCheckBox(row_frame, text=f"{group_name} ({group_id})")
        if is_checked:
            chk.select()
        chk.grid(row=0, column=0, sticky="w", padx=5)
        
        self.group_vars[str(group_id)] = (chk, row_frame)

        btn_del = ctk.CTkButton(
            row_frame, text="X", width=30, height=25,
            fg_color="#c0392b", hover_color="#962d22",
            command=lambda i=group_id: self.delete_row(i)
        )
        btn_del.grid(row=0, column=1, padx=5, sticky="e")

    def delete_row(self, group_id):
        gid = str(group_id)
        if gid in self.group_vars:
            chk, frame = self.group_vars[gid]
            frame.destroy()
            del self.group_vars[gid]

    def log(self, msg):
        """Visual logging system with timestamp"""
        # Ensure UI update happens on the Main Thread (Safe)
        def _insert_log():
            timestamp = time.strftime('%H:%M:%S')
            self.console.insert("end", f"[{timestamp}] {msg}\n")
            self.console.see("end")
        
        self.after(0, _insert_log)

    def handle_connect(self):
        self.save_config()
        api_id = self.api_id_entry.get()
        api_hash = self.api_hash_entry.get()
        phone = self.phone_entry.get()
        
        if not api_id or not api_hash or not phone:
            self.log("Error: API ID, Hash and Phone are required.")
            return

        self.log("Connecting...")
        future = self.engine.run_coro(self.engine.connect(api_id, api_hash, phone))
        
        def check():
            try:
                res = future.result(timeout=30)
                if res == "NEED_CODE":
                    self.after(100, self.ask_code)
                elif res == "CONNECTED":
                    self.log(self.i18n[self.current_lang]["log_connected"])
                    self.after(10, lambda: self.connect_btn.configure(
                        text=self.i18n[self.current_lang]["btn_disconnect"], 
                        state="normal", # Allow clicking to disconnect
                        fg_color="#c0392b",
                        command=self.handle_disconnect
                    ))
                    self.after(10, lambda: self.start_btn.configure(state="normal", text=self.i18n[self.current_lang]["btn_start"]))
            except Exception as e:
                self.log(self.i18n[self.current_lang]["log_error"].format(e=e))
        
        threading.Thread(target=check, daemon=True).start()

    def handle_fetch_chats(self):
        if not self.engine.is_connected:
            self.log("Error: Connect to Telegram first!")
            return
            
        self.log("Fetching groups and channels...")
        future = self.engine.run_coro(self.engine.get_dialogs())
        
        def check():
            try:
                # Timeout is now handled inside the engine via asyncio.wait_for
                dialogs = future.result() 
                if not dialogs:
                    self.log("Nenhum grupo encontrado ou timeout na conexão.")
                    return
                    
                self.log(f"Found {len(dialogs)} chats. Adding to selector...")
                for d in dialogs:
                    # Use after to update UI safely from thread
                    self.after(10, lambda name=d['name'], id=d['id']: self.add_group_row(id, name))
            except Exception as e:
                self.log(f"Fetch chats error: {e}")
            
        threading.Thread(target=check, daemon=True).start()

    def handle_disconnect(self):
        """Logout and clear session"""
        if self.engine.is_running:
            self.toggle_bot() # Stop bot before disconnect
            
        future = self.engine.run_coro(self.engine.logout())
        try:
            if future.result():
                self.log(self.i18n[self.current_lang]["log_disconnected"])
                # Reset UI
                self.connect_btn.configure(
                    text=self.i18n[self.current_lang]["btn_connect"],
                    state="normal",
                    fg_color=("#3a7ebf", "#1f538d"), # Original colors
                    command=self.handle_connect
                )
                self.start_btn.configure(state="disabled")
        except Exception as e:
            self.log(f"Disconnect error: {e}")

    def ask_code(self):
        dialog = ctk.CTkInputDialog(text=self.i18n[self.current_lang]["dialog_sms"], title="Verification")
        code = dialog.get_input()
        if code:
            self.log(self.i18n[self.current_lang]["log_verifying_code"])
            future = self.engine.run_coro(self.engine.login(code))
            
            def check_login():
                try:
                    res = future.result(timeout=30)
                    if res == "SUCCESS":
                        self.log(self.i18n[self.current_lang]["log_connected"])
                        # Configure as Disconnect button
                        self.after(10, lambda: self.connect_btn.configure(
                            text=self.i18n[self.current_lang]["btn_disconnect"], 
                            state="normal", 
                            fg_color="#c0392b",
                            command=self.handle_disconnect
                        ))
                        self.after(10, lambda: self.start_btn.configure(state="normal", text=self.i18n[self.current_lang]["btn_start"]))
                    elif res == "NEED_2FA":
                        self.after(10, self.ask_2fa)
                    else:
                        self.log(self.i18n[self.current_lang]["log_error"].format(e=res))
                except Exception as e:
                    self.log(self.i18n[self.current_lang]["log_error"].format(e=str(e)))

            threading.Thread(target=check_login, daemon=True).start()

    def ask_2fa(self):
        dialog = ctk.CTkInputDialog(text=self.i18n[self.current_lang]["dialog_2fa"], title="Two-Step Verification")
        pw = dialog.get_input()
        if pw:
            self.log(self.i18n[self.current_lang]["log_verifying_2fa"])
            future = self.engine.run_coro(self.engine.login(None, password=pw))
            
            def check_2fa():
                try:
                    res = future.result(timeout=30)
                    if res == "SUCCESS":
                        self.log(self.i18n[self.current_lang]["log_connected"])
                        # Configure as Disconnect button
                        self.after(10, lambda: self.connect_btn.configure(
                            text=self.i18n[self.current_lang]["btn_disconnect"], 
                            state="normal", 
                            fg_color="#c0392b",
                            command=self.handle_disconnect
                        ))
                        self.after(10, lambda: self.start_btn.configure(state="normal", text=self.i18n[self.current_lang]["btn_start"]))
                    else:
                        self.log(self.i18n[self.current_lang]["log_error"].format(e=res))
                except Exception as e:
                    self.log(self.i18n[self.current_lang]["log_error"].format(e=str(e)))

            threading.Thread(target=check_2fa, daemon=True).start()

    def open_source_search(self):
        """Abre uma janela modal para pesquisar e selecionar o chat fonte."""
        if not self.engine.is_connected:
            self.log("Erro: Conecte ao Telegram primeiro para buscar conversas.")
            return

        # Criação da janela secundária bloqueante
        popup = ctk.CTkToplevel(self)
        popup.title(self.i18n[self.current_lang].get("search_source_title", "Buscar Fonte"))
        popup.geometry("450x550")
        popup.resizable(False, False)
        popup.attributes("-topmost", True)
        popup.grab_set()

        # Centralizar na tela
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (450 // 2)
        y = (popup.winfo_screenheight() // 2) - (550 // 2)
        popup.geometry(f"+{x}+{y}")

        # Barra de Pesquisa
        search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            popup, 
            placeholder_text=self.i18n[self.current_lang].get("search_placeholder", "Digite nome ou ID..."), 
            textvariable=search_var,
            height=35
        )
        search_entry.pack(fill="x", padx=20, pady=15)

        # Área de Resultados com Rolagem
        results_frame = ctk.CTkScrollableFrame(popup)
        results_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Feedback de carregamento
        loading_lbl = ctk.CTkLabel(results_frame, text=self.i18n[self.current_lang].get("loading_chats", "Buscando..."))
        loading_lbl.pack(pady=20)

        all_dialogs = []

        def select_chat(chat_id):
            """Quando o usuário clica em 'Selecionar', joga o ID na caixa e fecha o popup"""
            self.source_entry.delete(0, "end")
            self.source_entry.insert(0, str(chat_id))
            popup.grab_release()
            popup.destroy()

        def update_list(*args):
            """Filtra a lista em tempo real toda vez que o usuário digita uma letra"""
            query = search_var.get().lower()
            
            # Limpa os resultados antigos da tela
            for widget in results_frame.winfo_children():
                widget.destroy()
            
            count = 0
            for d in all_dialogs:
                if query in d['name'].lower() or query in str(d['id']):
                    if count > 50:  # Limita a 50 resultados para a UI não travar se o cara tiver 5 mil grupos
                        break
                    
                    row = ctk.CTkFrame(results_frame, fg_color="transparent")
                    row.pack(fill="x", pady=2)
                    
                    btn = ctk.CTkButton(
                        row, 
                        text=self.i18n[self.current_lang].get("btn_select", "Selecionar"), 
                        width=70, 
                        command=lambda cid=d['id']: select_chat(cid)
                    )
                    btn.pack(side="right", padx=5)

                    lbl = ctk.CTkLabel(row, text=f"{d['name']} ({d['id']})", anchor="w")
                    lbl.pack(side="left", fill="x", expand=True, padx=5)
                    
                    count += 1

        def fetch_data():
            """Busca os diálogos no Telegram em uma thread separada para não congelar a UI"""
            try:
                future = self.engine.run_coro(self.engine.get_dialogs(timeout_sec=20))
                nonlocal all_dialogs
                all_dialogs = future.result()
                
                # Apaga o texto de "Carregando" e mostra a lista
                self.after(0, lambda: loading_lbl.destroy() if loading_lbl.winfo_exists() else None)
                self.after(0, update_list)
            except Exception as e:
                self.after(0, lambda: loading_lbl.configure(text=f"Erro: {e}"))

        # Inicia a busca invisível no fundo
        threading.Thread(target=fetch_data, daemon=True).start()
        
        # Liga a barra de pesquisa à função de filtrar a lista
        search_var.trace_add("write", update_list)

    def toggle_bot(self):
        if not self.engine.is_running:
            self.save_config()
            self.engine.is_running = True
            self.start_btn.configure(text=self.i18n[self.current_lang]["btn_stop"], fg_color="#c0392b", hover_color="#962d22")
            threading.Thread(target=self.bot_loop, daemon=True).start()
        else:
            self.engine.is_running = False
            self.start_btn.configure(text=self.i18n[self.current_lang]["btn_start"], fg_color="#2b8a3e", hover_color="#206a2f")

    def bot_loop(self):
        source_raw = self.source_entry.get().strip()
        
        # Get selected targets from checkboxes
        targets = []
        for gid, (chk, _) in self.group_vars.items():
            if chk.get() == 1:
                try:
                    targets.append(int(gid))
                except:
                    targets.append(gid)

        if not targets:
            self.log("Error: No target groups selected!")
            self.toggle_bot() # Stop
            return

        # Convert Source ID to int if numeric
        def parse_id(id_str):
            try:
                if id_str.startswith('-100') or id_str.isdigit() or (id_str.startswith('-') and id_str[1:].isdigit()):
                    return int(id_str)
            except: pass
            return id_str

        source = parse_id(source_raw)
        
        try:
            interval = int(self.interval_entry.get())
        except:
            interval = 60

        self.log(f"Bot Started. Polling {source} every {interval}s")
        while self.engine.is_running:
            try:
                # Fetch message (Timeout handled in Engine)
                future_msg = self.engine.run_coro(self.engine.get_last_message(source))
                msg = future_msg.result() 
                
                if msg:
                    # Shuffle targets for this cycle (Anti-ban)
                    current_targets = list(targets)
                    import random
                    random.shuffle(current_targets)
                    
                    self.log(f"Shuffled cycle: Cloning msg ID {msg.id} to {len(current_targets)} targets...")
                    
                    # Broadcast (No fixed timeout, it takes what it needs due to delays)
                    # We can use a very loose internal timeout if desired, but result() is safe here
                    future_send = self.engine.run_coro(self.engine.send_broadcast(msg, current_targets))
                    future_send.result() 
                else:
                    self.log(f"No messages found in {source} (or timeout occurred).")
            except Exception as e:
                self.log(f"Loop Error: {e}")
                # Wait a bit longer on error to prevent rapid-fire errors
                time.sleep(5)
            
            for _ in range(interval):
                if not self.engine.is_running: break
                time.sleep(1)

    def save_config(self):
        # Get all groups (name and selection state)
        saved_groups = {}
        for gid, (chk, _) in self.group_vars.items():
            raw_text = chk.cget("text")
            clean_name = raw_text.split(" (")[0]
            saved_groups[gid] = {
                "name": clean_name,
                "selected": True if chk.get() == 1 else False
            }

        conf = {
            "language": self.current_lang,
            "api_id": self.api_id_entry.get(),
            "api_hash": self.api_hash_entry.get(),
            "phone": self.phone_entry.get(),
            "source": self.source_entry.get(),
            "interval": self.interval_entry.get(),
            "groups": saved_groups
        }
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(conf, f, indent=4, ensure_ascii=False)

    def load_config(self):
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    conf = json.load(f)
                    
                    # API Fields
                    api_id = conf.get("api_id")
                    api_hash = conf.get("api_hash")
                    phone = conf.get("phone")

                    if api_id:
                        self.api_id_entry.delete(0, "end")
                        self.api_id_entry.insert(0, api_id)
                    if api_hash:
                        self.api_hash_entry.delete(0, "end")
                        self.api_hash_entry.insert(0, api_hash)
                    if phone:
                        self.phone_entry.delete(0, "end")
                        self.phone_entry.insert(0, phone)
                    
                    # Bot Settings
                    self.source_entry.delete(0, "end")
                    self.source_entry.insert(0, conf.get("source", ""))
                    self.interval_entry.delete(0, "end")
                    self.interval_entry.insert(0, conf.get("interval", "60"))

                    # Complex groups
                    groups = conf.get("groups", {})
                    for gid, data in groups.items():
                        self.add_group_row(gid, data['name'], is_checked=data.get('selected', False))

                    # Try auto-connect if credentials exist
                    if api_id and api_hash:
                        self.try_auto_connect(api_id, api_hash)
            except Exception as e:
                print(f"Load config error: {e}")

    def try_auto_connect(self, api_id, api_hash):
        """Verify in background if .session is still valid"""
        def check():
            try:
                future = self.engine.run_coro(self.engine.check_session(api_id, api_hash))
                # Wait for background result (safe behavior)
                if future.result():
                    self.log(self.i18n[self.current_lang]["log_connected"])
                    # Use after to update UI safely from thread
                    self.after(0, lambda: self.connect_btn.configure(
                        text=self.i18n[self.current_lang]["btn_disconnect"], 
                        state="normal",
                        fg_color="#c0392b",
                        command=self.handle_disconnect
                    ))
                    self.after(0, lambda: self.start_btn.configure(
                        state="normal", 
                        text=self.i18n[self.current_lang]["btn_start"]
                    ))
            except Exception as e:
                self.log(f"Auto-connect failed: {e}")
        
        threading.Thread(target=check, daemon=True).start()

    def on_closing(self):
        if self._is_closing: return
        self._is_closing = True
        
        self.save_config()
        self.unbind("<Unmap>") # Remove bind to avoid errors during destroy
        
        if hasattr(self, 'icon'):
            self.icon.stop()
        
        # Stop all engine processes
        self.engine.is_running = False
        self.destroy()
        os._exit(0)


if __name__ == "__main__":
    app = App()
    app.mainloop()
