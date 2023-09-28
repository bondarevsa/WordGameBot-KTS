from datetime import datetime

from sqlalchemy import text

from kts_backend.base.base_accessor import BaseAccessor


class GameAccessor(BaseAccessor):
    async def create_game(self, chat_id):
        async with self.app.database.session() as session:
            stmt = text('''INSERT INTO games (created_at, chat_id, status, words) 
                            VALUES (:created_at, :chat_id, :status, :words)''')
            values = {"created_at": datetime.now(), "chat_id": chat_id, "status": 0, "words": []}
            await session.execute(stmt, values)
            await session.commit()

            for user_id in self.app.store.users.get_users(self.app, chat_id):
                user = self.app.store.users.get_user_by_id(self.app, user_id)
                stmt = text('''INSERT INTO users (vk_id, name, last_name) 
                                VALUES (:vk_id, :name, :last_name)''')
                values = {"vk_id": user['id'], "name": user['first_name'], "last_name": user['last_name']}
                await session.execute(stmt, values)
                await session.commit()

                stmt = text('''INSERT INTO gamescores (player_id, game_id, points, is_playing) 
                                            VALUES (:player_id, :game_id, :points, :is_playing)''')
                values = {"player_id": user_id, "game_id": game_id, "points": 0, "is_playing": 1}
                await session.execute(stmt, values)
                await session.commit()

    async def get_last_game(self, chat_id):
        async with self.app.database.session() as session:
            stmt = text('''SELECT * FROM games
                           WHERE chat_id = :chat_id
                           ORDER BY created_at DESC
                           LIMIT 1''')
            result = await session.execute(stmt, {"chat_id": chat_id})
            last_game = result.scalar()
            return last_game

