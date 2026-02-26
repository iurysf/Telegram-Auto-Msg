import asyncio
import threading
import logging
from telethon import TelegramClient, events, errors
from telethon.tl.types import MessageMediaWebPage

import time

import random

class TelegramEngine:
    def __init__(self):
        # ... existing init code ...
        self.client = None
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()
        
        self.is_connected = False
        self.is_running = False
        self.logger = logging.getLogger("TelegramEngine")
        
    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def connect(self, api_id, api_hash, phone):
        self.client = TelegramClient('session_user', api_id, api_hash, loop=self.loop)
        await self.client.connect()
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(phone)
            return "NEED_CODE"
        self.is_connected = True
        return "CONNECTED"

    async def check_session(self, api_id, api_hash):
        """Check if a valid active session already exists in the .session file"""
        try:
            self.client = TelegramClient('session_user', api_id, api_hash, loop=self.loop)
            await self.client.connect()
            if await self.client.is_user_authorized():
                self.is_connected = True
                return True
        except Exception:
            pass
        return False

    async def login(self, code, password=None):
        try:
            await self.client.sign_in(code=code, password=password)
            self.is_connected = True
            return "SUCCESS"
        except errors.SessionPasswordNeededError:
            return "NEED_2FA"
        except Exception as e:
            self.logger.error(f"❌ Erro de login: {e}")
            return str(e)

    def _resolve_id(self, entity_id):
        """Standardize ID resolution for both Source and Targets"""
        try:
            if isinstance(entity_id, str):
                # Handle numeric string IDs (including -100 prefixes for channels)
                if entity_id.startswith('-') or entity_id.isdigit():
                    return int(entity_id)
            return entity_id
        except ValueError:
            return entity_id

    async def get_last_message(self, source_id, timeout_sec=45):
        # Enforce timeout inside the task, not the thread future
        source_id = self._resolve_id(source_id)
        try:
            return await asyncio.wait_for(self._get_last_message_internal(source_id), timeout=timeout_sec)
        except asyncio.TimeoutError:
            self.logger.warning(f"⏳ Tempo esgotado ao buscar mensagem da fonte {source_id}.")
            return None

    async def _get_last_message_internal(self, source_id):
        try:
            messages = await self.client.get_messages(source_id, limit=1)
            if messages:
                return messages[0]
        except Exception as e:
            self.logger.error(f"❌ Erro ao buscar mensagem de {source_id}: {e}")
        return None

    async def _mutate_message(self, text):
        if not text:
            return ""
        
        # 1. Invisible chars variation: Add 1-2 chars at the end (Safe for entities)
        # Adding chars at the end keeps all existing entity offsets valid.
        zw_chars = ['\u200b', '\u200c', '\u200d', '\uFEFF']
        suffix = "".join(random.choice(zw_chars) for _ in range(random.randint(1, 2)))
        
        # 2. Trailing space variation (subtle)
        trailing_spaces = " " * random.randint(0, 1)
        
        return f"{text}{trailing_spaces}{suffix}"

    async def send_broadcast(self, message, target_ids):
        # 1. Secure media caching
        reusable_media = None
        if message.media and not isinstance(message.media, MessageMediaWebPage):
            try:
                # Send to 'me' (Saved Messages) first to get a stable cloud reference
                sent_to_me = await self.client.send_message('me', file=message.media)
                reusable_media = sent_to_me.media
                self.logger.info("✅ Mídia armazenada no cache (Mensagens Salvas) com sucesso.")
            except Exception as e:
                self.logger.error(f"⚠️ Erro ao fazer cache da mídia: {e}")
                # Fallback: try to use the original media if caching fails
                reusable_media = message.media

        text = message.text or ""

        # 2. Isolated logic for each target (Task)
        async def send_to_single_target(target):
            try:
                # ISOLATED MUTATION: Ensures unique hash for each group
                mutated_text = await self._mutate_message(text)
                
                # INDEPENDENT DELAY: Bot mimicry at different times
                delay = random.uniform(2, 12)
                await asyncio.sleep(delay)
                
                # SENDING
                if reusable_media:
                    await self.client.send_message(
                        target, 
                        mutated_text, 
                        file=reusable_media,
                        formatting_entities=message.entities
                    )
                else:
                    await self.client.send_message(
                        target, 
                        mutated_text,
                        formatting_entities=message.entities
                    )
                
                self.logger.info(f"🚀 Mensagem enviada com sucesso para {target}.")
                
            except errors.FloodWaitError as e:
                # Trata o erro: "A wait of 3306 seconds is required..."
                if e.seconds > 120:
                    self.logger.warning(f"⏳ [Modo Lento] O grupo {target} exige espera de {e.seconds}s. Mensagem ignorada neste ciclo.")
                else:
                    self.logger.warning(f"🛑 [Anti-Spam] O Telegram pediu uma pausa rápida de {e.seconds}s no grupo {target}.")
                    
            except (errors.ChatWriteForbiddenError, errors.ChatAdminRequiredError):
                # Trata o erro: "You can't write in this chat"
                self.logger.error(f"🔇 [Mutado/Restrito] Sem permissão no grupo {target} (Apenas Admins podem postar ou você levou mute).")
                
            except ValueError:
                # Trata o erro: "An invalid Peer was used..."
                self.logger.error(f"❌ [ID Inválido] O destino {target} não é reconhecido. (Pode ser um chat privado ou bot).")
                
            except Exception as e:
                # Filtro de segurança (Fallback) caso o Telethon retorne o erro em formato de string genérica
                error_msg = str(e).lower()
                
                if "restricted" in error_msg or "can't write" in error_msg:
                    self.logger.error(f"🔇 [Mutado/Restrito] O grupo {target} está fechado para envios no momento.")
                elif "invalid peer" in error_msg:
                    self.logger.error(f"❌ [ID Inválido] O destino {target} não é um grupo/canal reconhecido pela sua conta.")
                else:
                    self.logger.error(f"⚠️ [Erro Desconhecido] Falha ao enviar para {target}: {str(e)}")

        # 3. Concurrent Dispatch (Fan-out)
        tasks = []
        for raw_target in target_ids:
            target = self._resolve_id(raw_target)
            tasks.append(asyncio.create_task(send_to_single_target(target)))
            
        # 4. Wait for all sends to complete the lifecycle
        await asyncio.gather(*tasks, return_exceptions=True)

    async def logout(self):
        """Disconnect and delete the session file on server side"""
        if self.client:
            await self.client.log_out()
            await self.client.disconnect()
            self.is_connected = False
            return True
        return False

    async def disconnect(self):
        """Just disconnect to release file locks"""
        if self.client:
            await self.client.disconnect()
            try:
                # Force close the SQLite session database to release Windows file locks
                if hasattr(self.client.session, 'close'):
                    self.client.session.close()
            except Exception:
                pass
            self.client = None
            self.is_connected = False
            return True
        return False

    async def get_dialogs(self, limit=200, timeout_sec=60):
        # Wrap the search in a safe asyncio timeout (Server-side)
        try:
            return await asyncio.wait_for(self._get_dialogs_internal(limit), timeout=timeout_sec)
        except asyncio.TimeoutError:
            self.logger.error("⏳ Tempo esgotado ao buscar grupos!")
            return []

    async def _get_dialogs_internal(self, limit):
        try:
            dialogs = []
            # Use the provided limit
            async for dialog in self.client.iter_dialogs(limit=limit):
                # Verifica se é um Bot de forma segura
                is_bot = getattr(dialog.entity, 'bot', False) if dialog.is_user and dialog.entity else False
                
                # Se for Grupo, Canal ou Bot, adicionamos na lista
                if dialog.is_group or dialog.is_channel or is_bot:
                    dialogs.append({
                        "name": dialog.name,
                        "id": dialog.id
                    })
            return dialogs
        except Exception as e:
            self.logger.error(f"❌ Erro ao buscar diálogos: {e}")
            return []

    def run_coro(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop)
