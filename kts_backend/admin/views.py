import json
import urllib
import uuid
from hashlib import sha256

from aiohttp_session import new_session, get_session

from kts_backend.web.app import View
from kts_backend.web.utils import json_response, error_json_response


class AdminLoginView(View):
    async def post(self):
        data = self.request.content
        try:
            data_decode = data._buffer[0].decode('utf-8')
            parsed_data = urllib.parse.parse_qs(data_decode)
            if not parsed_data:
                data = json.loads(data_decode)
                email = data['email']
                password = data['password']
            else:
                email = parsed_data.get('email', [''])[0]
                password = parsed_data.get('password', [''])[0]
            #email = data['email']
            #password = data['password']
            admin = await self.request.app.store.admins.get_by_email(email)
            if admin and admin.password == sha256(password.encode()).hexdigest():
                session = await new_session(request=self.request)
                session['manager'] = {'cookie': str(uuid.uuid4()), 'email': admin.email, 'id': admin.id}
                print(session['manager'])
                return json_response(data={"id": admin.id, "email": admin.email})
            return error_json_response(http_status=403, status='forbidden')
        except KeyError as e:
            jsn_response = '{"email":["Missing data for required field."]}'
            return error_json_response(http_status=400, status='bad_request', data=json.loads(jsn_response))


class AdminCurrentView(View):
    async def get(self):
        session = await get_session(self.request)
        if 'manager' not in session.keys():
            return error_json_response(http_status=401, status='unauthorized')
        return json_response(data={'id': session['manager']['id'], 'email': session['manager']['email']})


