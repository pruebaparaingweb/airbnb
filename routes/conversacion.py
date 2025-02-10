from fastapi import APIRouter, status, Body #APIRouter: nos permite definir todas las rutas dentro de este archivo
from starlette.status import HTTP_204_NO_CONTENT
from fastapi.encoders import jsonable_encoder
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import RedirectResponse
from typing import List
import requests
import time
from datetime import datetime

Templates = Jinja2Templates(directory="templates")

#url = 'http://127.0.0.1:8001'
#url_inicio = 'http://127.0.0.1:8000/'
url = 'https://api-airbnb-three.vercel.app'
url_inicio = 'https://airbnb-tapia.vercel.app'

conversacion = APIRouter()

def check_token(request: Request):
    nuevo_token = request.cookies.get("session_id")

    if nuevo_token is not None:

        headers = {'Authentication':nuevo_token}
        tokens = requests.get(url + '/usuarios/tokens/todos', headers=headers)

        if tokens.status_code != status.HTTP_401_UNAUTHORIZED:

            ts = time.time()
            tokens = tokens.json()

            for token in tokens:
                if (token["id_token"] == nuevo_token) and (token["expires_at"] >= ts) :
                    return token["email"]

    return None

# VER TODAS MIS CONVERSACIONES
@conversacion.get('/conversaciones')
async def find_conversaciones_by_usuario(request: Request):
    validez = check_token(request)

    if validez:
        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.get(url + '/conversaciones/todas/usuario', headers=headers)
        conversaciones = response.json()

        return Templates.TemplateResponse("conversacion/conversaciones.html", {"request": request, "usuario": validez, "conversaciones": conversaciones, "segment": "conversaciones" })
    else:
        return RedirectResponse(url_inicio)

# VER UNA CONVERACIÓN
@conversacion.get('/conversaciones/{id}')
async def find_conversaciones_by_idConversacion(id: str, request: Request):
    validez = check_token(request)

    if validez:
        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.get(url + '/conversaciones/' + id, headers=headers)
        conversacion = response.json()
        nueva_conversacion = jsonable_encoder(conversacion)
        nueva_conversacion["mensajes"]

        return Templates.TemplateResponse("conversacion/conversacion.html", {"request": request, "usuario": validez, "conversacion": nueva_conversacion, "segment": "conversaciones" })
    else:
        return RedirectResponse(url_inicio)


@conversacion.get('/conversaciones/contactar/vivienda/{id}')
async def get_conversacion(id: str, request: Request):
    validez = check_token(request)

    if validez:
        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.get(url + '/viviendas/' + id, headers=headers)
        vivienda = response.json()

        response = requests.get(url + '/conversaciones/usuario/propietario/' + vivienda["propietario"], headers=headers)
        conversacion = response.json()

        if conversacion is None:
            conversacion = {
                'participante1' : validez,
                'participante2' : vivienda["propietario"],
                'mensajes' : []
            }

            nueva_conversacion = jsonable_encoder(conversacion)

            response = requests.post(url + '/conversaciones' ,json=nueva_conversacion, headers=headers)
            conversacion = response.json()

        nueva_conversacion = jsonable_encoder(conversacion)
        return RedirectResponse('/conversaciones/' + nueva_conversacion["id"], status_code=status.HTTP_303_SEE_OTHER)                  
    else:
        return RedirectResponse(url_inicio)


@conversacion.get('/conversaciones/{id}/contactar/nuevo/mensaje/')
async def get_mensaje(id: str, request: Request):
    validez = check_token(request)

    if validez:
        headers = {'Authentication':request.cookies.get("session_id")}

        response = requests.get(url + '/conversaciones/' + id, headers=headers)
        conversacion = response.json()

        nueva_conversacion = jsonable_encoder(conversacion)

        if nueva_conversacion["participante1"] == validez:
            usuario = nueva_conversacion["participante2"]
        else:
            usuario = nueva_conversacion["participante1"]

        return Templates.TemplateResponse("conversacion/enviarMensaje.html", {"request": request, "usuario": usuario, "segment": "conversaciones" })
    else:
        return RedirectResponse(url_inicio)


@conversacion.post('/conversaciones/{id}/contactar/nuevo/mensaje/')
async def create_mensaje(id: str, request: Request):
    validez = check_token(request)

    if validez:

        form = await request.form()

        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.get(url + '/conversaciones/' + id, headers=headers)
        conversacion = response.json()

        mensajeTexto = form["inputMensaje"]

        if mensajeTexto != "" :

            date = datetime.now()
            dt_string = date.strftime("%Y-%m-%d %H:%M:%S")

            nueva_conversacion = jsonable_encoder(conversacion)

            if nueva_conversacion["participante1"] == validez:
                receptor = nueva_conversacion["participante2"]
            else:
                receptor = nueva_conversacion["participante1"]

            mensaje = {
                    'emisor' : validez,
                    'receptor' : receptor,
                    'contenido' : mensajeTexto,
                    'fecha' : dt_string
                }
            
            nueva_conversacion["mensajes"].append(mensaje)

            response = requests.put(url + '/conversaciones/' + nueva_conversacion["id"], json=nueva_conversacion, headers=headers)
            
            return RedirectResponse('/conversaciones/' + nueva_conversacion["id"], status_code=status.HTTP_303_SEE_OTHER)
        else:
            return Templates.TemplateResponse("vivienda/enviarMensaje.html", {"request": request, "usuario": receptor, "error": "Debes rellenar todos los campos", "segment": "index" })
                    
    else:
        return RedirectResponse(url_inicio)
