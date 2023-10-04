import asyncio
import random
import typing
from typing import Optional

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

import constants
from kts_backend.base.base_accessor import BaseAccessor
from kts_backend.store.bot.manager import BotManager
from kts_backend.store.vk_api.dataclasses import Message, Update, UpdateObject, UpdateMessage
from kts_backend.store.vk_api.poller import Poller
from kts_backend.store.vk_api.sender import Sender

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application

API_PATH = "https://api.vk.com/method/"


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.poller: Optional[Poller] = None
        self.bot_manager: Optional[BotManager] = None
        self.sender: Optional[Sender] = None
        self.ts: Optional[int] = None

        self.updates_queue = None
        self.messages_queue = None

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))
        try:
            await self._get_long_poll_service()
        except Exception as e:
            self.logger.error("Exception", exc_info=e)
        self.updates_queue = asyncio.Queue()
        self.messages_queue = asyncio.Queue()
        self.poller = Poller(app.store)
        self.bot_manager = BotManager(app)
        self.sender = Sender(app)
        self.logger.info("start polling")
        await self.poller.start()
        await self.bot_manager.start()
        await self.sender.start()
        await self.app.store.game_timer.start()

    async def disconnect(self, app: "Application"):
        if self.session:
            await self.session.close()
        if self.poller:
            await self.poller.stop()
        if self.bot_manager:
            await self.bot_manager.stop()
        if self.sender:
            await self.sender.stop()


    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url

    async def _get_long_poll_service(self):
        async with self.session.get(
            self._build_query(
                host=API_PATH,
                method="groups.getLongPollServer",
                params={
                    "group_id": self.app.config.bot.group_id,
                    "access_token": self.app.config.bot.token,
                },
            )
        ) as resp:
            data = (await resp.json())["response"]
            self.logger.info(data)
            self.key = data["key"]
            self.server = data["server"]
            self.ts = data["ts"]
            self.logger.info(self.server)

    async def poll(self):
        async with self.session.get(
            self._build_query(
                host=self.server,
                method="",
                params={
                    "act": "a_check",
                    "key": self.key,
                    "ts": self.ts,
                    "wait": 5,
                },
            )

        ) as resp:
            data = await resp.json()
            self.logger.info(data)
            self.ts = data["ts"]
            raw_updates = data.get("updates", [])
            updates = []
            for update in raw_updates:
                print(update)
                try:

                    try:
                        payload = update["object"]["message"]["payload"]
                    except:
                        payload = None

                    updates.append(
                        Update(
                            type=update["type"],
                            object=UpdateObject(
                                message=UpdateMessage(
                                    from_id=update["object"]["message"]["from_id"],
                                    text=update["object"]["message"]["text"],
                                    peer_id=update["object"]["message"]["peer_id"],
                                    payload=payload
                                )
                            ),
                        )
                    )
                except:
                    pass
            return updates

    async def send_message(self, message) -> None:
        # while self.sender.is_running:
        #     message = await self.messages_queue.get()
        async with self.session.get(
                self._build_query(
                    API_PATH,
                    "messages.send",
                    params={
                        "random_id": random.randint(1, 2 ** 32),
                        "peer_id": message.peer_id,
                        "message": message.text,
                        "keyboard": message.keyboard,
                        "access_token": self.app.config.bot.token,
                    },
                )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)
