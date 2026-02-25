import asyncio
import threading
import logging
from telethon import TelegramClient, events, errors
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
            self.logger.error(f"Login error: {e}")
            return str(e)

    async def get_last_message(self, source_id, timeout_sec=45):
        # Enforce timeout inside the task, not the thread future
        try:
            return await asyncio.wait_for(self._get_last_message_internal(source_id), timeout=timeout_sec)
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout while fetching message from source {source_id}.")
            return None

    async def _get_last_message_internal(self, source_id):
        try:
            # Handle numeric IDs
            try:
                if isinstance(source_id, str) and (source_id.startswith('-100') or source_id.isdigit()):
                    source_id = int(source_id)
            except ValueError:
                pass

            messages = await self.client.get_messages(source_id, limit=1)
            if messages:
                return messages[0]
        except Exception as e:
            self.logger.error(f"Error fetching message from {source_id}: {e}")
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
        # 1. Prepare Media (if any) to avoid redundant uploads
        reusable_media = None
        if message.media:
            try:
                # Send to 'me' (Saved Messages) first to get a stable cloud reference
                # We use the raw media to ensure we have a "cache" on the server
                sent_to_me = await self.client.send_message('me', file=message.media)
                reusable_media = sent_to_me.media
                self.logger.info("Media 'cached' in Saved Messages for faster broadcasting.")
            except Exception as e:
                self.logger.error(f"Error caching media: {e}")
                # Fallback to original media if caching fails
                reusable_media = message.media

        # Store original text to reset or reuse correctly in loop
        original_text = message.text or ""

        for target in target_ids:
            try:
                # Update message.text directly. Telethon recalculates entities 
                # internally when this property is set.
                message.text = await self._mutate_message(original_text)

                if reusable_media:
                    # Send message using the updated .text property
                    await self.client.send_message(
                        target, 
                        message.text, 
                        file=reusable_media
                    )
                else:
                    # Send plain text
                    await self.client.send_message(
                        target, 
                        message.text
                    )
                
                # Anti-ban random delay (Human-like behavior)
                delay = random.uniform(5, 20)
                self.logger.info(f"Sent msg to {target}. Delaying {delay:.1f}s...")
                await asyncio.sleep(delay) 
                
            except errors.FloodWaitError as e:
                self.logger.warning(f"Flood wait: {e.seconds}s")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                self.logger.error(f"Error sending to {target}: {e}")

    async def logout(self):
        """Disconnect and delete the session file"""
        if self.client:
            await self.client.log_out()
            await self.client.disconnect()
            self.is_connected = False
            return True
        return False

    async def get_dialogs(self, timeout_sec=60):
        # Wrap the search in a safe asyncio timeout (Server-side)
        try:
            return await asyncio.wait_for(self._get_dialogs_internal(), timeout=timeout_sec)
        except asyncio.TimeoutError:
            self.logger.error("Timeout while fetching groups!")
            return []

    async def _get_dialogs_internal(self):
        try:
            dialogs = []
            async for dialog in self.client.iter_dialogs(limit=100):
                if dialog.is_group or dialog.is_channel:
                    dialogs.append({
                        "name": dialog.name,
                        "id": dialog.id
                    })
            return dialogs
        except Exception as e:
            self.logger.error(f"Error fetching dialogs: {e}")
            return []

    def run_coro(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop)
