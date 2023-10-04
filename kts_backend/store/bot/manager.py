import typing
from enum import Enum
from typing import Optional
from asyncio import Task

import asyncio

from sqlalchemy.exc import IntegrityError

from kts_backend.store.bot import constants
from kts_backend.store.vk_api.dataclasses import Message

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application

API_PATH = "https://api.vk.com/method/"


class GameStatus(Enum):
    WAITING_PLAYERS = 'waiting for players'
    PLAYER_TURN = 'players turn'
    VOTING = 'voting'


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

    async def does_word_begin_with_correct_letter(self, word, game_id):
        last_word = await self.app.store.game.get_last_word(game_id)
        correct_last_word_letter_index = -1
        for letter in last_word[::-1]:
            if letter in ['ъ', 'ь', 'ы']:
                correct_last_word_letter_index -= 1
            else:
                break
        if word.lower()[0] == last_word.lower()[correct_last_word_letter_index]:
            return True
        return False

    async def add_start_keyboard(self, update):
        message = Message(
            user_id=update.object.message.from_id,
            text='Для старта нажми на кнопку "Начать играть".',
            peer_id=update.object.message.peer_id,
            keyboard=constants.start_keyboard
        )
        await self.app.store.vk_api.messages_queue.put(message)

    async def send_rules(self, update):
        message = Message(
            user_id=update.object.message.from_id,
            text=constants.RULES,
            peer_id=update.object.message.peer_id,
            keyboard=constants.start_keyboard
        )
        await self.app.store.vk_api.messages_queue.put(message)

    async def create_game(self, update):
        await self.app.store.game.create_game(update.object.message.peer_id)
        message = Message(
            user_id=update.object.message.from_id,
            text='Начался набор игроков! Нажми на кнопку, чтобы участвовать в игре!',
            peer_id=update.object.message.peer_id,
            keyboard=constants.collect_players_keyboard
        )
        await self.app.store.vk_api.messages_queue.put(message)

    async def this_word_already_used(self, update, game):
        if update.object.message.text.lower() in await self.app.store.game.get_all_words(game.id):
            message = Message(
                user_id=update.object.message.from_id,
                text='Это слово уже было. Напиши новое.',
                peer_id=update.object.message.peer_id,
                keyboard=constants.voting_keyboard
            )
            await self.app.store.vk_api.messages_queue.put(message)
            return True
        return False

    async def add_word_and_start_voting(self, update, game):
        await self.app.store.game.add_word(game.id, update.object.message.text)
        await self.app.store.game.update_game_status_to_voting(game.id)
        message = Message(
            user_id=update.object.message.from_id,
            text='Это слово существует?',
            peer_id=update.object.message.peer_id,
            keyboard=constants.voting_keyboard
        )
        await self.app.store.vk_api.messages_queue.put(message)

    async def create_player_if_dont_exist(self, update, user, game):
        if user.id not in game.players_queue:
            await self.app.store.game.add_user_to_players_queue(update.object.message.from_id, game.id)
            await self.app.store.users.create_gamescore(update.object.message.from_id, game.id)

    async def this_word_incorrect(self, update):
        message = Message(
            user_id=update.object.message.from_id,
            text='Это слово не подходит. Попробуй ещё.',
            peer_id=update.object.message.peer_id,
            keyboard=constants.voting_keyboard
        )
        await self.app.store.vk_api.messages_queue.put(message)

    async def voting(self, update, user, game):
        if await self.app.store.game.number_who_didnt_vote(game.id) != 1:
            gamescore = await self.app.store.game.get_gamescore(update.object.message.from_id, game.id)
            # user = await self.app.store.users.get_user_by_vk_id(update.object.message.from_id)
            if update.object.message.payload == '{"button":"4"}' and gamescore.vote_status == 'still voting' and user.id != game.current_player:
                await self.app.store.game.change_vote_status_on_correct(update.object.message.from_id,
                                                                        game.id)
            elif update.object.message.payload == '{"button":"5"}' and gamescore.vote_status == 'still voting' and user.id != game.current_player:
                await self.app.store.game.change_vote_status_on_wrong(update.object.message.from_id,
                                                                      game.id)

        if await self.app.store.game.number_who_didnt_vote(game.id) == 1:
            # Если за "Да" проголосовали больше
            if await self.app.store.game.are_more_correct_voices(game.id):
                await self.app.store.game.add_point(game.current_player, game.id)
                await self.app.store.game.move_first_queue_element_to_end(game.id, game.players_queue)
                user = await self.app.store.users.get_user_by_id_from_db(game.players_queue[1])
                await self.app.store.game.update_current_player(user.vk_id, game.id)
                await self.app.store.game.update_game_status_to_players_turn(game.id)
                await self.app.store.game.add_players_turn_time(game.id)
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
                await self.app.store.game.remove_last_word(game.id)
                await self.app.store.game.change_vote_status_on_voting(update.object.message.from_id,
                                                                       game.id)
                await self.app.store.game.change_is_playing(game.current_player, game.id)
                await self.app.store.game.remove_user_from_players_queue(game.current_player,
                                                                         # тут наверно курент плеер
                                                                         game.id)
                user = await self.app.store.users.get_user_by_id_from_db(game.players_queue[1])
                await self.app.store.game.update_current_player(user.vk_id, game.id)
                await self.app.store.game.update_game_status_to_players_turn(game.id)
                await self.app.store.game.add_players_turn_time(game.id)
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
                        text=f'Поздравляем, {user.name} {user.last_name}! Ты победитель!',
                        peer_id=update.object.message.peer_id,
                        keyboard=constants.start_keyboard
                    )
                    await self.app.store.vk_api.messages_queue.put(message)
                    await self.app.store.game.end_game(game.id)

                # Иначе озвучиваем того, кто ходит следующий
                else:
                    message = Message(
                        user_id=update.object.message.from_id,
                        text=f'{user.name} {user.last_name}, пиши слово! Последнее правильное слово - {game.words[-2]}',
                        peer_id=update.object.message.peer_id,
                        keyboard=constants.start_keyboard
                    )
                    await self.app.store.vk_api.messages_queue.put(message)

    async def handle_updates(self):
        while self.is_running:
            updates = await self.app.store.vk_api.updates_queue.get()
            for update in updates:
                game = await self.app.store.game.get_active_game_by_chat_id(update.object.message.peer_id)
                try:  # Если пользователь есть, бот упадет из-за уникальности vk_id
                        await self.app.store.users.create_user(update.object.message.from_id)
                except IntegrityError as e:
                    print(str(e))
                user = await self.app.store.users.get_user_by_vk_id(update.object.message.from_id)

                # если нет активной игры
                if not game:
                    # Если по какой-то причине нет стартовой клавы, можно написать "хочу играть"
                    if update.object.message.text == 'хочу играть':
                        await self.add_start_keyboard(update)

                    # нажатие на кнопку "правила" (отправляем правила в чат)
                    elif update.object.message.payload == '{"button":"1"}':
                        await self.send_rules(update)

                    # Кнопка "начать играть". Тут создаём активную игру и отправляем клавиатуру с кнопкой "Буду играть!"
                    elif update.object.message.payload == '{"button":"2"}':
                        await self.create_game(update)

                # если есть активная игра
                else:
                    # Если нажали на кнопку "Буду играть!" добавляем юзера в базу
                    # Перед этим проверяем, что его нет в базе
                    if game.status == GameStatus.WAITING_PLAYERS.value and update.object.message.payload == '{"button":"3"}':
                        await self.create_player_if_dont_exist(update, user, game)

                    # Если ход игрока, принимаем слово, добавляем в массив, меняем статус игры на "голосование"
                    # И отправляем клавиатуру для голосования
                    elif game.status == GameStatus.PLAYER_TURN.value:
                        try:
                            is_button_update = update.object.message.payload
                        except:
                            is_button_update = False

                        if not is_button_update:
                            # Проверяем, что голосовал не тот, кто ходит
                            if user.id != game.current_player:
                                break

                            if await self.does_word_begin_with_correct_letter(update.object.message.text, game.id):
                                if await self.this_word_already_used(update, game):
                                    break
                                await self.add_word_and_start_voting(update, game)

                            else:
                                await self.this_word_incorrect(update)
                    # Голосование
                    elif game.status == GameStatus.VOTING.value:
                        await self.voting(update, user, game)


