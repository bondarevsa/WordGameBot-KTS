import typing

from sqlalchemy import select
from sqlalchemy import text
from kts_backend.admin.models import AdminModel
from hashlib import sha256

from kts_backend.base.base_accessor import BaseAccessor
from kts_backend.store import Database

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


class AdminAccessor(BaseAccessor):
    def __init__(self, app: 'Application', database: Database = None):
        super().__init__(app)
        self.database = database

    async def get_by_email(self, email: str) -> AdminModel | None:
        async with self.app.database.session() as session:

           try:
                stmt = select(AdminModel).where(AdminModel.email == email)

                result = await session.execute(stmt)
                return result.first()[0]
           except:
               return None

    async def create_admin(self, email: str, password: str) -> AdminModel:
        raise NotImplemented

    async def connect(self, app: "Application"):
        async with self.app.database.session() as session:

            try:
                stmt = text("INSERT INTO admins (id, email, password) VALUES (:id, :email, :password)")
                values = {"id": 1, "email": self.app.config.admin.email,
                          "password": sha256(self.app.config.admin.password.encode()).hexdigest()}
                await session.execute(stmt, values)
                await session.commit()
            except:
                pass





