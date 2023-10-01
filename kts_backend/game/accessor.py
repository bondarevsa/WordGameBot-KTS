from datetime import datetime, timedelta
import asyncio
from sqlalchemy import text, select, update

from kts_backend.base.base_accessor import BaseAccessor
from kts_backend.game.models import GameModel, GameScoreModel
from kts_backend.users.models import UserModel


class GameAccessor(BaseAccessor):
    async def create_game(self, chat_id):
        async with self.app.database.session.begin() as session:
            game = GameModel(created_at=datetime.now() + timedelta(seconds=30), chat_id=chat_id, words=[], is_active=1,
                             status='waiting for players')
            session.add(game)

    # async def create_game(self, chat_id):
    #     async with self.app.database.session.begin() as session:
    #         game = GameModel(created_at=datetime.now(), chat_id=chat_id, status='waiting for players',
    #                          is_active=1, words=[])
    #         session.add(game)
    #         await session.flush()
    #
    #         users = await self.app.store.users.get_сonversation_members(self.app, chat_id)
    #         users_list = [UserModel(vk_id=player['id'], name=player['first_name'], last_name=player['last_name'])
    #                       for player in users]
    #         session.add_all(users_list)
    #         await session.flush()
    #
    #         gamescores_list = [GameScoreModel(player_id=user.id, game_id=game.id, points=0, is_playing=1) for user in
    #                            users_list]
    #         session.add_all(gamescores_list)

    async def get_active_game_by_chat_id(self, chat_id):
        async with self.app.database.session() as session:
            query = select(GameModel).where(GameModel.chat_id == chat_id).order_by(GameModel.is_active.desc()).limit(1)
            res = await session.execute(query)
            return res

    async def update_game_status_by_id(self, game_id):
        async with self.app.database.session() as session:
            query = update(GameModel).where(GameModel.id == game_id).values(status='players turn')
            await session.execute(query)
            await session.commit()

    async def add_user_to_players_queue(self, game_id, user_id):
        async with self.app.database.session() as session:
            # SQL-запрос для добавления user_id в массив players_queue
            query = (
                update(GameModel)
                .where(GameModel.id == game_id)
                .values(players_queue=GameModel.players_queue + [user_id])
            )

            await session.execute(query)
            await session.commit()

