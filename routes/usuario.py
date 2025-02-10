from fastapi import APIRouter, Response, status #APIRouter: nos permite definir todas las rutas dentro de este archivo
from bson import ObjectId
from starlette.status import HTTP_204_NO_CONTENT, HTTP_303_SEE_OTHER
from fastapi.encoders import jsonable_encoder
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import RedirectResponse
from typing import List
import requests
import time
from routes.conversacion import url, url_inicio

usuario = APIRouter()
Templates = Jinja2Templates(directory="templates")


def check_token(nuevo_token: str):
    headers = {'Authentication':nuevo_token}
    tokens = requests.get(url + '/usuarios/tokens/todos', headers=headers)
    ts = time.time()
    tokens = tokens.json()

    if len(tokens) > 0:
        for token in tokens:
            if (token["id_token"] == nuevo_token) and (token["expires_at"] >= ts) :
                return True

    return False


# GOOGLE

from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from authlib.integrations.starlette_client import OAuth
from starlette.config import environ

# CLIENT_ID = "279553875286-bu62e94dpbibtqn02s0vbf2m6arjros6.apps.googleusercontent.com"
# CLIENT_SECRET = "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"

CLIENT_ID = "853416967262-2tj4veftl34oseq1jrir94lru2pstb6a.apps.googleusercontent.com"
CLIENT_SECRET = "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"

oauth = OAuth()
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    client_kwargs={
        'scope': 'openid profile email'
    }
)

@usuario.get('/')
async def log_in(request : Request):
    return Templates.TemplateResponse("oauth/inicio.html", {"request": request, "segment": "misViviendas" })

@usuario.route('/login')
async def login_via_google(request : Request):
    google = oauth.create_client('google')
    redirect_uri = request.url_for('authorize_google')
    return await google.authorize_redirect(request, redirect_uri)

@usuario.route('/auth')
async def authorize_google(request : Request):
    google = oauth.create_client('google')
    token = await google.authorize_access_token(request)
    user = await google.parse_id_token(request, token)

    valores = {'email' : user["email"], 'id_token' : token["id_token"], 'expires_at' : token["expires_at"]}

    requests.put(url + '/usuarios/token/nuevo', json=valores)

    headers = {'Authentication':token["id_token"]}
    response = RedirectResponse("/viviendas", status_code=HTTP_303_SEE_OTHER, headers=headers)
    response.set_cookie(key="session_id", value=token["id_token"])

    return response


@usuario.get('/logout', tags=['authentication'])  # Tag it as "authentication" for our docs
async def logout(request: Request):
    nuevo_token = request.cookies.get('session_id')
    validez = check_token(nuevo_token)

    if validez:
        # Remove the user
        request.session.pop('user', None)

        requests.put(url + '/usuarios/token/borrar', json=nuevo_token)

        url_nueva = request.url_for('log_in')
        response = RedirectResponse(url_nueva)
        response.delete_cookie("session_id")

        return response
    else:
        return RedirectResponse(url)
