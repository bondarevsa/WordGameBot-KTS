import typing

#from app.store.admin.accessor import AdminAccessor
#from kts_backend.store.database.sqlalchemy_base import db
from kts_backend.store.database.database import Database
if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application
    #from kts_backend.store.admin.accessor import AdminAccessor


class Store:
    def __init__(self, app: "Application"):
        from kts_backend.users.accessor import UserAccessor

        from kts_backend.store.bot.manager import BotManager
        #from kts_backend.store.admin.accessor import AdminAccessor
        #from kts_backend.store.quiz.accessor import QuizAccessor
        from kts_backend.store.vk_api.accessor import VkApiAccessor

        #self.quizzes = QuizAccessor(app)
        #self.admins = AdminAccessor(app)
        self.users = UserAccessor(app)
        self.vk_api = VkApiAccessor(app)
        #self.bots_manager = BotManager(app)
        #self.user = UserAccessor(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.store = Store(app)
