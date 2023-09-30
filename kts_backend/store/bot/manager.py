import json

import vk_api
import random
import typing
from typing import Optional
from asyncio import Task

import asyncio

from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from kts_backend.store.vk_api.dataclasses import Update, Message, UpdateMessage, UpdateObject

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application

API_PATH = "https://api.vk.com/method/"
RULES = '''Правила игры: первый игрок называет слово.
            Следующему необходимо назвать слово, которое начинается на последнюю букву слова предыдущего игрока.
            Если такое слово существует и ещё не было названо, игрок получает балл.
            Иначе игрок выбывает.
            Игра продолжается до тех пор, пока не останется 1 игрок.'''


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.is_running = False
        self.bot_manager_task: Optional[Task] = None
        self.keyboard = json.dumps({
            "one_time": False,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "text",
                            "label": "Правила",
                            "payload": json.dumps({"button": "1"})
                        },
                        "color": "secondary"
                    },
                    {
                        "action": {
                            "type": "text",
                            "label": "Начать игру",
                            "payload": json.dumps({"button": "2"})
                        },
                        "color": "positive"
                    }
                ]
            ]
        })

    async def start(self):
        self.is_running = True
        self.bot_manager_task = asyncio.create_task(self.handle_updates())

    async def stop(self):
        self.is_running = False
        await self.bot_manager_task

    async def handle_updates(self):
        while self.is_running:
            updates = await self.app.store.vk_api.updates_queue.get()
            for update in updates:
                if update.object.message.payload == '{"button":"1"}':
                    message = Message(
                        user_id=update.object.message.from_id,
                        text=RULES,
                        peer_id=update.object.message.peer_id
                    )

                elif update.object.message.payload == '{"button":"2"}':
                    users = await self.app.store.users.get_users(self.app, update.object.message.peer_id)
                    print(users)
                    random.shuffle(users)

                    message = Message(
                        user_id=update.object.message.from_id,
                        text=f'Игра началась! {users[0]["first_name"]} {users[0]["last_name"]} ходит первым! Напиши первое слово.',
                        peer_id=update.object.message.peer_id
                    )
                    await self.app.store.game.create_game(update.object.message.peer_id)


                else:
                    message = Message(
                            user_id=update.object.message.from_id,
                            text=update.object.message.text,
                            peer_id=update.object.message.peer_id
                            )
                await self.app.store.vk_api.messages_queue.put(message)
