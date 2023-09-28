from kts_backend.base.base_accessor import BaseAccessor
from kts_backend.users.models import UserDC
from kts_backend.web.app import Application

API_PATH = "https://api.vk.com/method/"


class UserAccessor(BaseAccessor):
    async def get_users(self, app: "Application", chat_id) -> list[UserDC]:
        async with app.store.vk_api.session.get(
                app.store.vk_api._build_query(
                    API_PATH,
                    "messages.getChat",
                    params={
                        "chat_id": chat_id,
                        "access_token": self.app.config.bot.token,
                    },
                )
        ) as resp:
            data = await resp.json()
            return data.get("response", [])['users']  # выведется массив айдишников

    # get_users возвращает только айдишники, поэтому ниже получаю инфу о пользователе по его id
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


