from asyncio import Task
from typing import Optional

import asyncio

from kts_backend.web.app import Application


class Sender:
    def __init__(self, app: "Application"):
        self.app = app
        self.is_running = False
        self.sender_task: Optional[Task] = None

    async def start(self):
        self.is_running = True
        self.sender_task = asyncio.create_task(self.app.store.vk_api.send_message())

    async def stop(self):
        self.is_running = False
        await self.sender_task

