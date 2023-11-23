import json

# from aiohttp_apispec import querystring_schema, request_schema, response_schema

from kts_backend.game.models import GameModel, GameScoreModel
from kts_backend.web.app import View
from aiohttp_session import get_session

from kts_backend.web.utils import error_json_response, json_response
from kts_backend.store.bot import constants


class WordAddView(View):
    async def post(self):
        session = await get_session(self.request)
        if 'manager' not in session.keys():
            return error_json_response(http_status=401, status='unauthorized')
        try:
            word = (await self.request.json())["word"]
        except KeyError:
            jsn_response = '{"title":["Missing data for required field."]}'
            return error_json_response(http_status=400, status='bad_request', data=json.loads(jsn_response))

        if word in constants.init_words:
            return error_json_response(http_status=409, status='conflict')

        constants.init_words.append(word)
        return json_response(data={"word": word})
