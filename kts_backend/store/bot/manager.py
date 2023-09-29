import random
import typing
from typing import Optional
from asyncio import Task

import asyncio

from kts_backend.store.vk_api.dataclasses import Update, Message

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application

API_PATH = "https://api.vk.com/method/"


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.is_running = False
        self.bot_manager_task: Optional[Task] = None

    async def start(self):
        self.is_running = True
        self.bot_manager_task = asyncio.create_task(self.handle_updates())

    async def stop(self):
        self.is_running = False
        await self.bot_manager_task

    async def handle_updates(self):
        while self.is_running:
            updates = self.app.store.vk_api.updates_queue.get()
            for update in updates:
                message = Message(
                        user_id=update.object.message.from_id,
                        text=update.object.message.text,
                        peer_id=update.object.message.peer_id
                        )
                self.app.store.vk_api.messages_queue.put(message)


class Sender:
    def __init__(self, app: "Application"):
        self.app = app
        self.is_running = False
        self.sender_task: Optional[Task] = None

    async def start(self):
        self.is_running = True
        self.sender_task = asyncio.create_task(self.send_message())

    async def stop(self):
        self.is_running = False
        await self.sender_task

    async def send_message(self) -> None:
        while self.is_running:
            message = self.app.store.vk_api.messages_queue.get()
            async with self.app.store.vk_api.session.get(
                self.app.store.vk_api._build_query(
                    API_PATH,
                    "messages.send",
                    params={
                        "random_id": random.randint(1, 2**32),
                        "peer_id": message.peer_id,
                        "message": message.text,
                        "access_token": self.app.config.bot.token,
                    },
                )
            ) as resp:
                data = await resp.json()
                self.app.store.vk_api.logger.info(data)
