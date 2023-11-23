import typing

from kts_backend.game.views import WordAddView

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/word.add_word", WordAddView)
