from typing import Optional

from aiohttp.web import (
    Application as AiohttpApplication,
    Request as AiohttpRequest,
    View as AiohttpView,
)

from kts_backend.store import Store, setup_store
#from kts_backend.store.admin.accessor import AdminAccessor
from kts_backend.store.database.database import Database
from kts_backend.web.config import Config, setup_config
#from kts_backend.web.logger import setup_logging
#from kts_backend.web.mw import setup_middlewares
#from kts_backend.web.routes import setup_routes


class Application(AiohttpApplication):
    config: Optional[Config] = None
    store: Optional[Store] = None
    database: Optional[Database] = None
    #admin_accessor: Optional[AdminAccessor] = None


app = Application()

def setup_app(config_path: str) -> Application:
    #setup_logging(app)
    setup_config(app, config_path)
    #session_setup(app, EncryptedCookieStorage(app.config.session.key))
    #setup_routes(app)
    # setup_aiohttp_apispec(
    #     app, title="Vk Quiz Bot", url="/docs/json", swagger_path="/docs"
    # )
    #setup_middlewares(app)
    setup_store(app)
    return app
