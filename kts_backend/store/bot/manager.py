import json
from datetime import datetime

import vk_api
import random
import typing
from typing import Optional
from asyncio import Task

import asyncio

from vk_api.keyboard import VkKeyboard, VkKeyboardColor

import constants
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
                try:
                    game_chunked = await self.app.store.game.get_active_game_by_chat_id(update.object.message.peer_id)
                    game = list(game_chunked)[0][0]
                    have_active_game = game.is_active
                except:
                    have_active_game = False

                if not have_active_game:
                    message = Message(
                        user_id=update.object.message.from_id,
                        text='Может поиграем?',
                        peer_id=update.object.message.peer_id,
                        keyboard=constants.start_keyboard
                    )

                    if update.object.message.payload == '{"button":"1"}':
                        message = Message(
                            user_id=update.object.message.from_id,
                            text=RULES,
                            peer_id=update.object.message.peer_id,
                            keyboard=constants.start_keyboard
                        )

                    if update.object.message.payload == '{"button":"2"}':
                        await self.app.store.game.create_game(update.object.message.peer_id)
                        message = Message(
                            user_id=update.object.message.from_id,
                            text='Начался набор игроков! Нажми на кнопку, чтобы участвовать в игре!',
                            peer_id=update.object.message.peer_id,
                            keyboard=constants.collect_players_keyboard
                        )

                    await self.app.store.vk_api.messages_queue.put(message)

                else:
                    if game.status == 'waiting for players' and game.created_at <= datetime.now(): # тут потом добавить current_player и сделать проверку на количество игроков
                        await self.app.store.game.update_game_status_by_id(game.id)

                    elif game.status == 'waiting for players' and update.object.message.payload == '{"button":"3"}':
                        await self.app.store.users.create_user_and_gamescore(update.object.message.from_id, game.id)
                        await self.app.store.game.add_user_to_players_queue(update.object.message.from_id, game.id)














                # await self.app.store.game.create_game(update.object.message.peer_id)  # удалить потом
                # КНОПКА ПРАВИЛА
                # if update.object.message.payload == '{"button":"1"}':
                #     message = Message(
                #         user_id=update.object.message.from_id,
                #         text=RULES,
                #         peer_id=update.object.message.peer_id
                #     )

                # Узнаю, есть ли в этом чате активная игра
                # try:
                #     have_active_game_chunked = await self.app.store.game.get_active_game_by_chat_id(update.object.message.peer_id)
                #     have_active_game = list(have_active_game_chunked)[0][0].is_active  # тут будет True, если есть активная игра
                # except:
                #     have_active_game = False

                # Если нет, то нажав на кнопку "Начать игру", будет создана случайная последовательность игроков
                # Создана игра в базе данных и отправлено соответствующее сообщение
                # if not have_active_game:
                #     if update.object.message.payload == '{"button":"2"}':
                #         users = await self.app.store.users.get_сonversation_members(self.app, update.object.message.peer_id)
                #         print(users)
                #         random.shuffle(users)
                #
                #         message = Message(
                #             user_id=update.object.message.from_id,
                #             text=f'Игра началась! {users[0]["first_name"]} {users[0]["last_name"]} ходит первым! Напиши первое слово.',
                #             peer_id=update.object.message.peer_id
                #         )
                #         await self.app.store.game.create_game(update.object.message.peer_id)

                # Если есть активная игра
                # else:
                    # Заметка на завтра
                    # Кнопку с правилами я уже обработал, как и кнопку начать играть
                    # Поэтому сюда сто проц приходит слово, которое надо обработать
                    # Теперь мысли:
                    # Сначала проверяем, пустой ли массив слов. Если да, то это первое слово(впоследствии до него могло быть неправльное). Добавляем в массив.
                    # Если не пустой, то проверяем, начинается ли оно с последней буквы прошлого слова (то есть прошлое слово надо где-то хранить (надеюсь, в переменной)).
                    # Если да, то записываем в словарь и передаём ход.
                    # Если нет, выводим пользователя из игры
                    # Хранить каким-то образом количество активных пользователей. И сделать цикл While players_count != 1: play
                    # Else: поменять статус игры в базе на false. Игра закончена.

                    # message = Message(
                    #     user_id=update.object.message.from_id,
                    #     text='Игра уже идёт!',
                    #     peer_id=update.object.message.peer_id
                    # )


                # ЭХО БОТ
                # else:
                #     message = Message(
                #             user_id=update.object.message.from_id,
                #             text=update.object.message.text,
                #             peer_id=update.object.message.peer_id
                #             )
                # await self.app.store.vk_api.messages_queue.put(message)
