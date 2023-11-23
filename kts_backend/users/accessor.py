from sqlalchemy import select

from kts_backend.base.base_accessor import BaseAccessor
from kts_backend.game.models import GameScoreModel
from kts_backend.users.models import UserDC, UserModel
from kts_backend.web.app import Application

API_PATH = "https://api.vk.com/method/"


class UserAccessor(BaseAccessor):
    async def get_сonversation_members(self, app: "Application", peer_id) -> list[UserDC]:
        async with app.store.vk_api.session.get(
                app.store.vk_api._build_query(
                    API_PATH,
                    "messages.getConversationMembers",
                    params={
                        "peer_id": peer_id,
                        "access_token": self.app.config.bot.token,
                    },
                )
        ) as resp:
            data = await resp.json()
            return data.get("response", [])['profiles']

    async def get_user_by_id(self, app: "Application", user_id):
        try:
            async with app.store.vk_api.session.get(
                    app.store.vk_api._build_query(
                        API_PATH,
                        "users.get",
                        params={
                            "user_ids": user_id,
                            "access_token": self.app.config.bot.token,
                        },
                    )
            ) as resp:
                data = await resp.json()
                user_info = data.get("response", [])[0]
                return user_info
        except Exception as e:
            self.logger.error(f"Ошибка при получении информации о пользователе: {str(e)}")
            return None

    async def create_user(self, user_vk_id):
        async with self.app.database.session.begin() as session:
            user_by_id = await self.get_user_by_id(self.app, user_vk_id)
            user = UserModel(vk_id=user_by_id['id'], name=user_by_id['first_name'], last_name=user_by_id['last_name'])
            session.add(user)

    async def create_gamescore(self, user_vk_id, game_id):
        async with self.app.database.session.begin() as session:
            user = await self.get_user_by_vk_id(user_vk_id)
            gamescore = GameScoreModel(player_id=user.id, game_id=game_id, points=0,
                                       is_playing=1, vote_status='still voting')
            session.add(gamescore)

    async def get_user_by_vk_id(self, vk_id):
        async with self.app.database.session() as session:
            query = select(UserModel).where(UserModel.vk_id == vk_id)
            res = await session.execute(query)
            return list(res)[0][0]  # так вернёт в формате UserModel

    async def get_user_by_id_from_db(self, user_id):
        async with self.app.database.session() as session:
            query = select(UserModel).where(UserModel.id == user_id)
            res = await session.execute(query)
            return list(res)[0][0]  # так вернёт в формате UserModel
