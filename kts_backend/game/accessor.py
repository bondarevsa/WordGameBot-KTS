from datetime import datetime, timedelta
import asyncio
from sqlalchemy import text, select, update, func, literal, BigInteger, case, and_, delete, distinct, exists
from sqlalchemy.dialects.postgresql import array

from kts_backend.base.base_accessor import BaseAccessor
from kts_backend.game.models import GameModel, GameScoreModel
from kts_backend.users.models import UserModel


class GameAccessor(BaseAccessor):
    async def create_game(self, chat_id):
        async with self.app.database.session.begin() as session:
            game = GameModel(created_at=datetime.now(), chat_id=chat_id, words=[], is_active=1,
                             status='waiting for players', players_queue=[])
            session.add(game)

    async def get_active_game_by_chat_id(self, chat_id):
        async with self.app.database.session() as session:
            query = select(GameModel).where(GameModel.chat_id == chat_id).order_by(GameModel.is_active.desc()).limit(1)
            res = await session.execute(query)
            return res

    async def get_all_active_waiting_games(self):
        async with self.app.database.session() as session:
            query = select(GameModel).where(
                and_(GameModel.status == 'waiting for players', GameModel.is_active == True)
            )
            res = await session.execute(query)
            return res.fetchall()

    async def get_all_active_players_turn_games(self):
        async with self.app.database.session() as session:
            query = select(GameModel).where(
                and_(GameModel.status == 'players turn', GameModel.is_active == True)
            )
            res = await session.execute(query)
            return res.fetchall()

    async def get_first_player_id(self, game_id):
        async with self.app.database.session() as session:
            query = select(GameModel.players_queue).where(GameModel.id == game_id)
            res = await session.execute(query)
            return res.scalar()[0]

    async def update_game_status_to_players_turn(self, game_id):
        async with self.app.database.session() as session:
            query = update(GameModel).where(GameModel.id == game_id).values(status='players turn')
            await session.execute(query)
            await session.commit()

    async def update_game_status_to_voting(self, game_id):
        async with self.app.database.session() as session:
            query = update(GameModel).where(GameModel.id == game_id).values(status='voting')
            await session.execute(query)
            await session.commit()

    async def add_user_to_players_queue(self, user_vk_id, game_id):
        async with self.app.database.session() as session:
            user = await self.app.store.users.get_user_by_vk_id(user_vk_id)
            query = update(GameModel).values(
                players_queue=func.array_append(GameModel.players_queue, user.id)
            ).where(GameModel.id == game_id)
            await session.execute(query)
            await session.commit()

    async def remove_user_from_players_queue(self, user_id, game_id):
        async with self.app.database.session() as session:
            user = await self.app.store.users.get_user_by_id_from_db(user_id)
            query = update(GameModel).values(
                players_queue=func.array_remove(GameModel.players_queue, user.id)
            ).where(GameModel.id == game_id)
            await session.execute(query)
            await session.commit()

    async def remove_last_word(self, game_id):
        async with self.app.database.session() as session:
            last_word = await self.app.store.game.get_last_word(game_id)
            query = update(GameModel).values(
                words=func.array_remove(GameModel.words, last_word)
            ).where(GameModel.id == game_id)
            await session.execute(query)
            await session.commit()

    async def move_first_queue_element_to_end(self, game_id, players_queue):
        async with self.app.database.session() as session:
            query = (
                update(GameModel)
                .values(players_queue=players_queue[1:] + [players_queue[0]])
                .where(GameModel.id == game_id)
            )
            await session.execute(query)
            await session.commit()

    async def update_current_player(self, user_vk_id, game_id):
        async with self.app.database.session() as session:
            user = await self.app.store.users.get_user_by_vk_id(user_vk_id)
            query = update(GameModel).where(GameModel.id == game_id).values(current_player=user.id)
            await session.execute(query)
            await session.commit()

    async def add_word(self, game_id, word):
        async with self.app.database.session() as session:
            query = update(GameModel).values(
                words=func.array_append(GameModel.words, word.lower())
            ).where(GameModel.id == game_id)
            await session.execute(query)
            await session.commit()

    async def add_players_turn_time(self, game_id):
        async with self.app.database.session() as session:
            query = update(GameModel).values(players_turn_time=datetime.now()).where(GameModel.id == game_id)
            await session.execute(query)
            await session.commit()

    async def get_players_turn_time(self, game_id):
        async with self.app.database.session() as session:
            query = select(GameModel.players_turn_time).where(GameModel.id == game_id)
            res = await session.execute(query)
            return res.scalar()

    async def get_all_words(self, game_id):
        async with self.app.database.session() as session:
            query = select(GameModel.words).where(GameModel.id == game_id)
            res = await session.execute(query)
            return res.scalar()

    async def get_gamescore(self, user_vk_id, game_id):
        async with self.app.database.session() as session:
            user = await self.app.store.users.get_user_by_vk_id(user_vk_id)
            #query = select(GameScoreModel).where(GameScoreModel.player_id == user.id)
            query = select(GameScoreModel).where(
                and_(GameScoreModel.game_id == game_id, GameScoreModel.player_id == user.id))
            res = await session.execute(query)
            return list(res)[0][0]  # так вернёт в формате GameScoreModel

    async def change_vote_status_on_correct(self, user_vk_id, game_id):
        async with self.app.database.session() as session:
            user = await self.app.store.users.get_user_by_vk_id(user_vk_id)
            query = update(GameScoreModel).values(vote_status='correct').where(and_(GameScoreModel.game_id == game_id, GameScoreModel.player_id == user.id))
            await session.execute(query)
            await session.commit()

    async def change_vote_status_on_wrong(self, user_vk_id, game_id):
        async with self.app.database.session() as session:
            user = await self.app.store.users.get_user_by_vk_id(user_vk_id)
            query = update(GameScoreModel).values(vote_status='wrong').where(and_(GameScoreModel.game_id == game_id, GameScoreModel.player_id == user.id))
            await session.execute(query)
            await session.commit()

    async def change_vote_status_on_voting(self, user_vk_id, game_id):
        async with self.app.database.session() as session:
            user = await self.app.store.users.get_user_by_vk_id(user_vk_id)
            query = update(GameScoreModel).values(vote_status='still voting').where(and_(GameScoreModel.game_id == game_id, GameScoreModel.player_id == user.id))
            await session.execute(query)
            await session.commit()

    async def reset_vote_status(self, game_id):
        async with self.app.database.session() as session:
            query = update(GameScoreModel).values(vote_status='still voting').where(GameScoreModel.game_id == game_id)
            await session.execute(query)
            await session.commit()

    async def change_is_playing(self, user_id, game_id):
        async with self.app.database.session() as session:
            user = await self.app.store.users.get_user_by_id_from_db(user_id)
            query = update(GameScoreModel).values(is_playing=False).where(and_(GameScoreModel.game_id == game_id, GameScoreModel.player_id == user.id))
            await session.execute(query)
            await session.commit()

    async def number_who_didnt_vote(self, game_id):
        async with self.app.database.session() as session:
            query = select(func.count(case
                                      ([(and_(GameScoreModel.vote_status == 'still voting',
                                              GameScoreModel.is_playing == True,
                                              GameScoreModel.game_id == game_id), 1)], else_=None)))
            res = await session.execute(query)
            return res.scalar()

    async def are_more_correct_voices(self, game_id):
        async with self.app.database.session() as session:
            query = select(func.count(case
                                      ([(and_(GameScoreModel.vote_status == 'correct',
                                              GameScoreModel.is_playing == True,
                                              GameScoreModel.game_id == game_id), 1)], else_=None)))
            res_true = await session.execute(query)
            query = select(func.count(case
                                      ([(and_(GameScoreModel.vote_status == 'wrong',
                                              GameScoreModel.is_playing == True,
                                              GameScoreModel.game_id == game_id), 1)], else_=None)))
            res_false = await session.execute(query)
            if res_true.scalar() >= res_false.scalar():
                return True
            return False

    async def add_point(self, user_id, game_id):
        async with self.app.database.session() as session:
            user = await self.app.store.users.get_user_by_id_from_db(user_id)
            query = update(GameScoreModel).values(points=text("points + 1")).where(
                and_(GameScoreModel.game_id == game_id, GameScoreModel.player_id == user.id)
            )
            await session.execute(query)
            await session.commit()

    async def get_last_word(self, game_id):
        async with self.app.database.session() as session:
            query = select(GameModel.words).where(GameModel.id == game_id)
            res = await session.execute(query)
            return res.scalar()[-1]

    async def end_game(self, game_id):
        async with self.app.database.session() as session:
            query = update(GameModel).where(GameModel.id == game_id).values(is_active=False)
            await session.execute(query)
            await session.commit()





