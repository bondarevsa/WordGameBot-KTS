import asyncio
import random
from asyncio import Task
from datetime import timedelta, datetime
from typing import Optional

from kts_backend.store.bot import constants
from kts_backend.store.bot.manager import GameStatus
from kts_backend.store.vk_api.dataclasses import Message

from kts_backend.web.app import Application


class GameTimer:
    def __init__(self, app: 'Application'):
        self.app = app
        self.is_running = False
        self.game_timer_task: Optional[Task] = None
        self.chat_ids: list = []   # чтобы знать, в каком чате он уже запущен

    async def start(self):
        self.is_running = True
        self.game_timer_task = asyncio.create_task(self.timer())

    async def stop(self, chat_id):
        self.is_running = False
        self.chat_ids.remove(chat_id)
        await self.game_timer_task

    async def timer(self):
        while self.is_running:
            games = await self.app.store.game.get_all_active_waiting_games()
            for game in games:
                game = game[0]
                if game.status == GameStatus.WAITING_PLAYERS.value and game.created_at + timedelta(seconds=20) <= datetime.now() and games != []:
                    # Если меньше двух игроков, игра не начинается
                    if len(game.players_queue) < 2:
                        message = Message(
                            user_id=0,
                            text=f'Число игроков меньше двух. Начните заново, когда будете готовы.',
                            peer_id=game.chat_id,
                            keyboard=constants.start_keyboard
                        )
                        await self.app.store.vk_api.messages_queue.put(message)
                        await self.app.store.game.end_game(game.id)
                        break

                    await self.app.store.game.update_game_status_to_players_turn(game.id)
                    await self.app.store.game.add_players_turn_time(game.id)
                    first_player_id = await self.app.store.game.get_first_player_id(game.id)
                    first_player = await self.app.store.users.get_user_by_id_from_db(first_player_id)
                    first_word = random.choice(constants.init_words)
                    await self.app.store.game.add_word(game.id, first_word)
                    message = Message(
                        user_id=0,
                        text=f'Игра началась! Первое слово - {first_word}. Ходит {first_player.name} {first_player.last_name}',
                        peer_id=game.chat_id,
                        keyboard=constants.start_keyboard
                    )
                    await self.app.store.vk_api.messages_queue.put(message)
                    await self.app.store.game.update_current_player(first_player.vk_id, game.id)

            games = await self.app.store.game.get_all_active_players_turn_games()
            for game in games:
                game = game[0]
                if game.status == GameStatus.PLAYER_TURN.value and game.players_turn_time + timedelta(seconds=30) <= datetime.now() and games != []:
                    user = await self.app.store.users.get_user_by_id_from_db(game.current_player)
                    await self.app.store.game.change_vote_status_on_voting(user.vk_id, game.id)
                    await self.app.store.game.change_is_playing(user.id, game.id)
                    await self.app.store.game.remove_user_from_players_queue(user.id, game.id)
                    user = await self.app.store.users.get_user_by_id_from_db(game.players_queue[1])
                    await self.app.store.game.update_current_player(user.vk_id, game.id)
                    await self.app.store.game.update_game_status_to_players_turn(game.id)
                    await self.app.store.game.add_players_turn_time(game.id)
                    await self.app.store.game.reset_vote_status(game.id)
                    message = Message(
                        user_id=0,
                        text=f'Время вышло. Ты проиграл.',
                        peer_id=game.chat_id,
                        keyboard=constants.voting_keyboard
                    )
                    await self.app.store.vk_api.messages_queue.put(message)
                    if await self.app.store.game.number_who_didnt_vote(game.id) != 1:
                        message = Message(
                            user_id=0,
                            text=f'Следующий ходит {user.name} {user.last_name}.Последнее правильное слово - {game.words[-1]}',
                            peer_id=game.chat_id,
                            keyboard=constants.voting_keyboard
                        )
                        await self.app.store.vk_api.messages_queue.put(message)
                        await self.app.store.game.update_game_status_to_players_turn(game.id)
                    else:
                        message = Message(
                            user_id=0,
                            text=f'Поздравляем, {user.name} {user.last_name}! Ты победитель!',
                            peer_id=game.chat_id,
                            keyboard=constants.start_keyboard
                        )
                        await self.app.store.vk_api.messages_queue.put(message)
                        await self.app.store.game.end_game(game.id)

            await asyncio.sleep(2)
