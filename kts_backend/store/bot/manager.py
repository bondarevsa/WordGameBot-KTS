import json
from datetime import datetime, timedelta

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
                # если нет активной игры
                if not have_active_game:
                    # Отправляем стартовую клавиатуру
                    message = Message(
                        user_id=update.object.message.from_id,
                        text='Может поиграем?',
                        peer_id=update.object.message.peer_id,
                        keyboard=constants.start_keyboard
                    )

                    # нажатие на кнопку "правила" (отправляем правила в чат)
                    if update.object.message.payload == '{"button":"1"}':
                        message = Message(
                            user_id=update.object.message.from_id,
                            text=RULES,
                            peer_id=update.object.message.peer_id,
                            keyboard=constants.start_keyboard
                        )

                    # Кнопка "начать играть". Тут создаём активную игру и отправляем клавиатуру с кнопкой "Буду играть!"
                    if update.object.message.payload == '{"button":"2"}':
                        await self.app.store.game.create_game(update.object.message.peer_id)
                        message = Message(
                            user_id=update.object.message.from_id,
                            text='Начался набор игроков! Нажми на кнопку, чтобы участвовать в игре!',
                            peer_id=update.object.message.peer_id,
                            keyboard=constants.collect_players_keyboard
                        )

                    await self.app.store.vk_api.messages_queue.put(message)

                # если есть активная игра
                else:
                    # если статус игры "ожидание игроков" и с момента начала игры прошло 30 сек меняем статус на "ход игрока"
                    if game.status == 'waiting for players' and game.created_at + timedelta(seconds=5) <= datetime.now():
                        # Если меньше двух игроков, игра не начинается
                        if len(game.players_queue) < 2:
                            message = Message(
                                user_id=update.object.message.from_id,
                                text=f'Число игроков меньше двух. Начните заново, когда будете готовы.',
                                peer_id=update.object.message.peer_id,
                                keyboard=constants.start_keyboard
                            )
                            await self.app.store.vk_api.messages_queue.put(message)
                            break

                        await self.app.store.game.update_game_status_to_players_turn(game.id)
                        first_player_id = await self.app.store.game.get_first_player_id(game.id)
                        first_player = await self.app.store.users.get_user_by_id_from_db(first_player_id)
                        message = Message(
                            user_id=update.object.message.from_id,
                            text=f'Игра началась! Первое слово пишет {first_player.name} {first_player.last_name}',
                            peer_id=update.object.message.peer_id,
                            keyboard=constants.start_keyboard
                        )
                        await self.app.store.vk_api.messages_queue.put(message)
                        await self.app.store.game.update_current_player(first_player.vk_id, game.id)

                    # Если время набора игроков не вышло и нажали на кнопку "Буду играть!" добавляем юзера в базу
                    # Перед этим проверяем, что его нет в базе
                    elif game.status == 'waiting for players' and update.object.message.payload == '{"button":"3"}':
                        if update.object.message.from_id not in game.players_queue:
                            try:  # если два раза нажать "Буду играть", то база упадет, тк ошибка уникальности vk_id. Поэтому try
                                await self.app.store.users.create_user_and_gamescore(update.object.message.from_id, game.id)
                                await self.app.store.game.add_user_to_players_queue(update.object.message.from_id, game.id)
                            except:
                                pass

                    # Если ход игрока, принимаем слово, добавляем в массив, меняем статус игры на "голосование"
                    # И отправляем клавиатуру для голосования
                    elif game.status == 'players turn':
                        try:
                            is_button_update = update.object.message.payload
                        except:
                            is_button_update = False
                        if not is_button_update:
                            user = await self.app.store.users.get_user_by_vk_id(update.object.message.from_id)
                            if user.id == game.current_player:
                                await self.app.store.game.add_word(game.id, update.object.message.text)
                                await self.app.store.game.update_game_status_to_voting(game.id)
                                message = Message(
                                    user_id=update.object.message.from_id,
                                    text='Это слово подходит?',
                                    peer_id=update.object.message.peer_id,
                                    keyboard=constants.voting_keyboard
                                )
                                await self.app.store.vk_api.messages_queue.put(message)
                    # Голосование
                    elif game.status == 'voting':
                        # Если проголосовали все
                        if await self.app.store.game.number_who_didnt_vote(game.id) == 0:
                            # Если за "Да" проголосовали больше
                            if await self.app.store.game.are_more_correct_voices(game.id):
                                await self.app.store.game.add_point(update.object.message.from_id, game.id)
                                await self.app.store.game.move_first_queue_element_to_end(game.id, game.players_queue)
                                user = await self.app.store.users.get_user_by_id_from_db(game.players_queue[1])
                                await self.app.store.game.update_current_player(user.vk_id, game.id)
                                await self.app.store.game.update_game_status_to_players_turn(game.id)
                                await self.app.store.game.reset_vote_status(game.id)
                                message = Message(
                                    user_id=update.object.message.from_id,
                                    text=f'Большинство проголосовали за. {user.name} {user.last_name}, теперь твоя очередь',
                                    peer_id=update.object.message.peer_id,
                                    keyboard=constants.voting_keyboard
                                )
                                await self.app.store.vk_api.messages_queue.put(message)
                            # Если за "Нет" проголосовали больше - удаляем игрока
                            else:
                                await self.app.store.game.change_vote_status_on_voting(update.object.message.from_id,
                                                                                       game.id)
                                await self.app.store.game.change_is_playing(update.object.message.from_id, game.id)
                                await self.app.store.game.remove_user_from_players_queue(update.object.message.from_id,
                                                                                         game.id)
                                user = await self.app.store.users.get_user_by_id_from_db(game.players_queue[1])
                                await self.app.store.game.update_current_player(user.vk_id, game.id)
                                await self.app.store.game.update_game_status_to_players_turn(game.id)
                                await self.app.store.game.reset_vote_status(game.id)
                                message = Message(
                                    user_id=update.object.message.from_id,
                                    text=f'Большинство считает, что такого слова нет. Ты выбываешь.',
                                    peer_id=update.object.message.peer_id,
                                    keyboard=constants.voting_keyboard
                                )
                                await self.app.store.vk_api.messages_queue.put(message)

                                # Если остался 1 (2 - 1 удалённый) игрок, заканчиваем игру
                                if len(game.players_queue) == 2:
                                    message = Message(
                                        user_id=update.object.message.from_id,
                                        text=f'Поздравляем, {user.name} {user.last_name}! Ты выиграл!',
                                        peer_id=update.object.message.peer_id,
                                        keyboard=constants.start_keyboard
                                    )
                                    await self.app.store.vk_api.messages_queue.put(message)
                                    await self.app.store.game.end_game(game.id)

                                # Иначе озвучиваем того, кто ходит следующий
                                else:
                                    message = Message(
                                        user_id=update.object.message.from_id,
                                        text=f'{user.name} {user.last_name}, пиши слово!',
                                        peer_id=update.object.message.peer_id,
                                        keyboard=constants.start_keyboard
                                    )
                                    await self.app.store.vk_api.messages_queue.put(message)

                        # Если ещё не все проголосовали и апдейты приходят от тех, кто ещё не голосовал
                        else:
                            gamescore = await self.app.store.game.get_gamescore(update.object.message.from_id)
                            if update.object.message.payload == '{"button":"4"}' and gamescore.vote_status == 'still voting':
                                await self.app.store.game.change_vote_status_on_correct(update.object.message.from_id, game.id)
                            elif update.object.message.payload == '{"button":"5"}' and gamescore.vote_status == 'still voting':
                                await self.app.store.game.change_vote_status_on_wrong(update.object.message.from_id, game.id)
