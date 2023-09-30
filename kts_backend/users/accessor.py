from kts_backend.base.base_accessor import BaseAccessor
from kts_backend.users.models import UserDC
from kts_backend.web.app import Application

API_PATH = "https://api.vk.com/method/"


class UserAccessor(BaseAccessor):
    async def get_users(self, app: "Application", peer_id) -> list[UserDC]:
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
