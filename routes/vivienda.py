from fastapi import APIRouter, status, Body #APIRouter: nos permite definir todas las rutas dentro de este archivo
from starlette.status import HTTP_204_NO_CONTENT
from fastapi.encoders import jsonable_encoder
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import RedirectResponse
from typing import List
import requests
import cloudinary
import cloudinary.uploader
import cloudinary.api
import time
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from babel.dates import format_date
import html
import ast
from routes.conversacion import url, url_inicio
import ast


# gmail_user = 'grupoa4ingenieriaweb2223@gmail.com'
# gmail_password = 'xybxfywwnhaftelv'

gmail_user = 'pruebaparaingweb@gmail.com'
gmail_password = 'astur900'


cloudinary.config( 
  # cloud_name = "web2022", 
  # api_key = "758781561277471", 
  # api_secret = "QsVHbVQ5Z_K-_kNzJiJ94-fAuWk" 

  cloud_name = "canallcc",
  api_key = "576949413175551",
  api_secret = "wrvazJg3fAPO18hSUlQJMsTba6M" 
)

Templates = Jinja2Templates(directory="templates")

vivienda = APIRouter()

#region check token
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
#endregion

#region Encontrar Todas las Viviendas
@vivienda.get('/viviendas')
async def find_all_viviendas(request : Request):
    validez = check_token(request)

    if validez:
        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.get(url + '/viviendas', headers=headers)
        viviendas = response.json()
        return Templates.TemplateResponse("viviendas.html", {"request": request, "viviendas" : viviendas, "segment": "index" }) 
    else:
        return RedirectResponse(url_inicio)
#endregion

#region Encontrar Todas las Viviendas Filtradas
@vivienda.post('/viviendas/filtradas')
async def find_all_viviendas_filtradas(request : Request):
    validez = check_token(request)

    if validez:
        form = await request.form()
        filtro = {
            "menor": form["inputPrecioDesde"],
            "mayor": form["inputPrecioHasta"],
            "huespedes": form["inputHuespedes"],
            "municipio" : form["inputMunicipio"],
            "fechaInicio": form["input_from"],
            "fechaFin": form["input_to"]
        }

        if form["input_to"] == "" or form["input_from"] == "":
            return Templates.TemplateResponse("viviendas.html", {"request": request, "filtro": filtro, "error":"Rellene las fechas en las que desea reservar", "segment": "index" })
        else:
            headers = {'Authentication':request.cookies.get("session_id")}
            filtroUsado = {
                "menor": form["inputPrecioDesde"],
                "mayor": form["inputPrecioHasta"],
                "huespedes": form["inputHuespedes"],
                "municipio" : form["inputMunicipio"],
                "fechaInicio": str(nueva_fecha(form["input_from"])),
                "fechaFin": str(nueva_fecha(form["input_to"]))
            }
            if filtroUsado["menor"] == "":
                filtroUsado["menor"] = 0
            if filtroUsado["mayor"] == "":
                filtroUsado["mayor"] = 1000000
            if filtroUsado["huespedes"] == "":
                filtroUsado["huespedes"] = 0

            response = requests.post(url + '/viviendas/filtro/multiple',params=filtroUsado, headers=headers)
            if response.status_code == status.HTTP_200_OK:
                viviendas = response.json()
                return Templates.TemplateResponse("viviendas.html", {"request": request, "viviendas" : viviendas, "filtro": filtro, "segment": "index" })
            else:
                return Templates.TemplateResponse("viviendas.html", {"request": request, "filtro": filtro, "error":"Rellene el municipio donde desea buscar", "segment": "index" })
    else:
        return RedirectResponse(url_inicio)
#endregion

#region Ver mis Viviendas
@vivienda.get('/viviendas/misviviendas/propietario')
async def find_vivienda_by_propietario(request : Request):
    validez = check_token(request)

    if validez:
        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.get(url + '/viviendas/misviviendas/propietario', headers=headers)
        viviendas = response.json()
        return Templates.TemplateResponse("vivienda/misViviendas.html", {"request": request, "viviendas" : viviendas, "segment": "misViviendas" }) 
    else:
        return RedirectResponse(url_inicio)
#endregion

#region Ver Detalles de una Vivienda
@vivienda.get('/viviendas/{id}/vivienda')
async def find_vivienda_by_id(id: str, request: Request):
    validez = check_token(request)

    if validez:
        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.get(url + '/viviendas/'+id, headers=headers)
        vivienda = response.json()

        localizacion = vivienda["localizacion"]
        municipio = localizacion["municipio"]

        response = requests.get(url + '/tiempo',params={"nombreMunicipio":municipio}, headers=headers)
        tiempo = response.json()

        if len(tiempo) > 0:
            tiempo7dias = {"temperaturas":[[tiempo[0]["fecha"], tiempo[0]["temperaturaMinima"], tiempo[0]["temperaturaMaxima"]], [tiempo[1]["fecha"], tiempo[1]["temperaturaMinima"], tiempo[1]["temperaturaMaxima"]], [tiempo[2]["fecha"], tiempo[2]["temperaturaMinima"], tiempo[2]["temperaturaMaxima"]], [tiempo[3]["fecha"], tiempo[3]["temperaturaMinima"], tiempo[3]["temperaturaMaxima"]], [tiempo[4]["fecha"], tiempo[4]["temperaturaMinima"], tiempo[4]["temperaturaMaxima"]], [tiempo[5]["fecha"], tiempo[5]["temperaturaMinima"], tiempo[5]["temperaturaMaxima"]], [tiempo[6]["fecha"], tiempo[6]["temperaturaMinima"], tiempo[6]["temperaturaMaxima"]]]}

            i = 0
            valores = ast.literal_eval(tiempo[0]["probabilidadPrecipitacion"])
            res = []

            for val in valores:
                if str(val).isnumeric():
                    res.append(val)

            tiempo[0]["probabilidadPrecipitacion"] = res

            foto = []

            while i < len(tiempo):
                if i != 0:
                    tiempo[i]["probabilidadPrecipitacion"] = ast.literal_eval(tiempo[i]["probabilidadPrecipitacion"])
                
                if not isinstance(tiempo[i]["probabilidadPrecipitacion"], int):
                    lista = [int(x) for x in tiempo[i]["probabilidadPrecipitacion"]]
                    media = round(sum(lista)/len(lista))
                else:
                    media = tiempo[i]["probabilidadPrecipitacion"]

                if media <= 25:
                    foto.append("sol.png")
                elif media > 25 and media <= 50:
                    foto.append("nuboso.png")
                elif media > 50 and media <= 75:
                    foto.append("meteorologia.png")
                else:
                    foto.append("lluvioso.png")

                i = i + 1

            precipitacion7dias = {"precipitacion":foto}
        else:
            tiempo7dias = {"temperaturas":[]}
            precipitacion7dias = {"precipitacion":[]}

        vivienda.update(tiempo7dias)
        vivienda.update(precipitacion7dias)

        if vivienda["fotos"] is None: vivienda["fotos"] = []
        if vivienda["reservas"] is None: vivienda["reservas"] = []

        if vivienda["propietario"] == validez :
            return Templates.TemplateResponse("vivienda/vivienda.html", {"request": request, "propietario":vivienda["propietario"], "vivienda": vivienda, "segment": "misViviendas" })
        else:
            return Templates.TemplateResponse("vivienda/vivienda.html", {"request": request, "vivienda": vivienda, "segment": "index" })

    else:
        return RedirectResponse(url_inicio)
#endregion

#region Crear Nueva Vivienda
@vivienda.get('/viviendas/nuevaVivienda')
async def get_vivienda(request: Request):
    validez = check_token(request)

    if validez:
        return Templates.TemplateResponse("vivienda/nuevaVivienda.html", {"request": request, "segment": "misViviendas" })
    else:
        return RedirectResponse(url_inicio)

@vivienda.post('/viviendas/nuevaVivienda')
async def create_vivienda(request: Request):
    validez = check_token(request)

    if validez:

        form = await request.form()

        data = requests.get("https://nominatim.openstreetmap.org/search.php?street=" + 
                        form["inputNumero"] + "%2F" + form["inputCalle"] + 
                        "&country=" +form["inputPais"] + 
                        "&postalcode="+ form["inputCodigoPostal"] +
                        "&county"+ form["inputProvincia"] + 
                        "&city=" + form["inputMunicipio"] + 
                        "&format=jsonv2").json()

        if len(data) > 0 :
            vivienda = {
                'nombre': form["inputNombre"],
                'descripcion': form['inputDescripcion'],
                'precio': form['inputPrecio'],
                'capacidad': form['inputCapacidad'], 
                'localizacion': 
                    { 'pais': form["inputPais"],
                    'provincia': form["inputProvincia"],
                    'municipio': form["inputMunicipio"],
                    'cp': form["inputCodigoPostal"],
                    'calle': form["inputCalle"],
                    'numero': form["inputNumero"],
                    'numeroBloque': form["inputNumeroBloque"],
                    'lat':data[0]['lat'],
                    'lon':data[0]['lon']
                    },
                'reservas':[],
                'propietario': validez,
                'fotos':[],
                'valoracion':-1,
                'reseñas':[]
            }

            headers = {'Authentication':request.cookies.get("session_id")}
            response = requests.post(url + '/viviendas',json=vivienda, headers=headers)
            if response.status_code == status.HTTP_200_OK:
                vivienda = response.json()
                urlActual = request.url_for("find_all_viviendas")
                return RedirectResponse(urlActual + '/nuevaVivienda/'+ vivienda["id"], status_code=status.HTTP_303_SEE_OTHER)
            else:
                vivienda = {
                'nombre': form["inputNombre"],
                'descripcion': form['inputDescripcion'],
                'precio': form['inputPrecio'],
                'capacidad': form['inputCapacidad'], 
                'localizacion': 
                    {'pais': form["inputPais"],
                    'provincia': form["inputProvincia"],
                    'municipio': form["inputMunicipio"],
                    'cp': form["inputCodigoPostal"],
                    'calle': form["inputCalle"],
                    'numero': form["inputNumero"],
                    'numeroBloque': form["inputNumeroBloque"]
                    },
                'reservas': [],
                'propietario': validez,
                'fotos':[],
                'valoracion':-1,
                'reseñas':[]
            }
                return Templates.TemplateResponse("vivienda/nuevaVivienda.html", {"request": request, "segment": "misViviendas","vivienda":vivienda,"error":"Rellene todos los campos" })
        else:
            vivienda = {
                'nombre': form["inputNombre"],
                'descripcion': form['inputDescripcion'],
                'precio': form['inputPrecio'],
                'capacidad': form['inputCapacidad'], 
                'localizacion': 
                    {'pais': form["inputPais"],
                    'provincia': form["inputProvincia"],
                    'municipio': form["inputMunicipio"],
                    'cp': form["inputCodigoPostal"],
                    'calle': form["inputCalle"],
                    'numero': form["inputNumero"],
                    'numeroBloque': form["inputNumeroBloque"]
                    },
                'reservas': [],
                'propietario': validez,
                'fotos':[],
                'valoracion':-1,
                'reseñas':[]
            }
            return Templates.TemplateResponse("vivienda/nuevaVivienda.html", {"request": request, "segment": "misViviendas","vivienda":vivienda,"error":"Localización incorrecta, rellene de nuevo los campos" })
    else:
        return RedirectResponse(url_inicio)

@vivienda.get('/viviendas/nuevaVivienda/{id}')     
async def get_vivienda(id:str, request: Request):
    validez = check_token(request)

    if validez:
        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.get(url + '/viviendas/'+id, headers=headers)
        vivienda = response.json()
        return Templates.TemplateResponse("vivienda/subirFotos.html", {"request": request, "vivienda": vivienda, "segment": "misViviendas"})
    else:
        return RedirectResponse(url_inicio)
#endregion

#region Editar Vivienda
@vivienda.get('/viviendas/editarVivienda/{id}')
async def get_editar_vivienda(id: str, request: Request):
    validez = check_token(request)

    if validez:
        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.get(url + '/viviendas/'+id, headers=headers)
        vivienda = response.json()
        if vivienda["fotos"] is None: vivienda["fotos"] = []
        if vivienda["reservas"] is None: vivienda["reservas"] = []
        return Templates.TemplateResponse("vivienda/editarVivienda.html", {"request": request, "vivienda": vivienda, "segment": "misViviendas" })
    else:
        return RedirectResponse(url_inicio)

@vivienda.post('/viviendas/editarVivienda/{id}')
async def update_vivienda(id: str, request: Request):
    validez = check_token(request)

    if validez:

        form = await request.form()

        data = requests.get("https://nominatim.openstreetmap.org/search.php?street=" + 
                        form["inputNumero"] + "%2F" + form["inputCalle"] + 
                        "&country=" +form["inputPais"] + 
                        "&postalcode="+ form["inputCodigoPostal"] +
                        "&county"+ form["inputProvincia"] + 
                        "&city=" + form["inputMunicipio"] + 
                        "&format=jsonv2").json()

        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.get(url + '/viviendas/'+ id, headers=headers)
        vivienda = response.json()
        if len(data) > 0 :
            vivienda = {
                'nombre' : form["inputNombre"],
                'descripcion' : form['inputDescripcion'],
                'precio' : form['inputPrecio'],
                'capacidad' : form['inputCapacidad'], 
                'localizacion': 
                    { 'pais': form["inputPais"],
                    'provincia': form["inputProvincia"],
                    'municipio': form["inputMunicipio"],
                    'cp': form["inputCodigoPostal"],
                    'calle': form["inputCalle"],
                    'numero': form["inputNumero"],
                    'numeroBloque': form["inputNumeroBloque"],
                    'lat':data[0]['lat'],
                    'lon':data[0]['lon']
                    },
                'propietario': validez,
                'fotos':vivienda["fotos"],
                'valoracion':vivienda["valoracion"],
                'reseñas':vivienda["reseñas"]
            }

            headers = {'Authentication':request.cookies.get("session_id")}
            requests.put(url + '/viviendas/'+ id,json= vivienda, headers=headers)
            urlActual = request.url_for("find_all_viviendas")
            return RedirectResponse(urlActual + '/'+ id + '/vivienda', status_code=status.HTTP_303_SEE_OTHER)
        else:
            headers = {'Authentication':request.cookies.get("session_id")}
            response = requests.get(url + '/viviendas/'+id, headers=headers)
            vivienda = response.json()
            if vivienda["fotos"] is None: vivienda["fotos"] = []
            return Templates.TemplateResponse("vivienda/editarVivienda.html", {"request": request, "segment": "misViviendas","vivienda": vivienda,"error":"Localización incorrecta, rellene de nuevo los campos" })
    else:
        return RedirectResponse(url_inicio)
#endregion

#region Borrar Vivienda
@vivienda.get('/viviendas/delete/{id}/propietario')
async def delete_vivienda(id: str, request: Request):
    validez = check_token(request)

    if validez:
        headers = {'Authentication':request.cookies.get("session_id")}
        requests.delete(url + '/viviendas/'+id, headers=headers)
        
        urlActual = request.url_for("find_all_viviendas") 
        return  RedirectResponse(urlActual + '/misviviendas/propietario' , status_code=status.HTTP_303_SEE_OTHER)
    else:
        return RedirectResponse(url_inicio)
#endregion

#region Borrar Imagen en Actualizar Vivienda
@vivienda.get('/viviendas/{id}/imagen/{indice}/delete')
async def delete_imagen_from_vivienda(id: str, indice: int, request: Request):
    validez = check_token(request)

    if validez:
        headers = {'Authentication':request.cookies.get("session_id")}
        requests.put(url + '/viviendas/'+id+ '/imagen/' + str(indice) + '/delete', headers=headers)
        urlActual = request.url_for("find_all_viviendas")
        return  RedirectResponse(urlActual + '/editarVivienda/' + id, status_code=status.HTTP_303_SEE_OTHER)
        #return Templates.TemplateResponse("vivienda/editarVivienda.html", {"request": request, "vivienda": vivienda, "segment": "misViviendas" })
    else:
        return RedirectResponse(url_inicio)
#endregion

#region Nueva Imagen en Actualizar Vivienda
@vivienda.post('/viviendas/{id}/imagen/')
async def new_imagen_for_vivienda(id: str,request: Request, urlFoto: str = Body(None)):
    validez = check_token(request)

    if validez:
        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.get(url + '/viviendas/'+ id, headers=headers)
        vivienda = response.json()
        nueva_vivienda = jsonable_encoder(vivienda)
        if nueva_vivienda["fotos"] is None :
            nueva_vivienda["fotos"] = []
        nueva_vivienda["fotos"].append(urlFoto)

        requests.put(url + '/viviendas/'+ id, json=nueva_vivienda, headers=headers)

        urlActual = request.url_for("find_all_viviendas")
        return RedirectResponse(urlActual + 'viviendas/editarVivienda/' + id, status_code=status.HTTP_303_SEE_OTHER)
    else:
        return RedirectResponse(url_inicio)
#endregion

#region Nueva Imagen en Nueva Vivienda
@vivienda.post('/viviendas/{id}/crearimagen/')
async def new_imagen_for_new_vivienda(id: str,request: Request, urlFoto: str = Body(None)):
    validez = check_token(request)

    if validez:
        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.get(url + '/viviendas/'+ id, headers=headers)
        vivienda = response.json()
        nueva_vivienda = jsonable_encoder(vivienda)
        if nueva_vivienda["fotos"] is None :
            nueva_vivienda["fotos"] = []
        nueva_vivienda["fotos"].append(urlFoto)

        requests.put(url + '/viviendas/'+ id, json=nueva_vivienda, headers=headers)

        urlActual = request.url_for("find_all_viviendas")
        return RedirectResponse(urlActual + 'viviendas/nuevaVivienda/' + id, status_code=status.HTTP_303_SEE_OTHER)
    else:
        return RedirectResponse(url_inicio)
#endregion

#region Ver Mapa con Todas las Viviendas
@vivienda.get('/viviendas/localizaciones/mapas')
async def localizaciones_en_mapa(request:Request):
    validez = check_token(request)

    if validez:
        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.get(url + '/viviendas/localizaciones/latlon', headers=headers)
        localizaciones = response.json()
        return Templates.TemplateResponse('map.html',{"request": request,"localizaciones":localizaciones, "segment":"mapas"})
    else:
        return RedirectResponse(url_inicio)
#endregion

#region Crear Nueva Reserva
@vivienda.get('/viviendas/{id}/nueva/reserva')
async def get_reserva(id: str, request: Request):
    validez = check_token(request)

    if validez:
        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.get(url + '/viviendas/' + id, headers=headers)
        vivienda = response.json()

        if (vivienda["reservas"]):
            reservasFuturas = reservas_futuras(vivienda["reservas"])
        else:
            reservasFuturas = []

        return Templates.TemplateResponse("vivienda/reservarVivienda.html", {"request": request, "vivienda": vivienda, "reservasFuturas":reservasFuturas, "segment": "index" })
    else:
        return RedirectResponse(url_inicio)

def reservas_futuras(reservas: List):

    reservasFuturas = []

    ts = time.time()

    for reserva in reservas:
            fecha = reserva["fechaFin"]
            ts_fecha = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S').timestamp()
            
            if ts < ts_fecha:
                reservasFuturas.append(reserva)

    return reservasFuturas

def nueva_fecha(fecha: str):
    month = fecha.split(",")[0].split(" ")[1]
    num_month = datetime.strptime(month, '%B').month 
    nueva_fecha = fecha.replace(month, str(num_month))
    fechaNueva_date = datetime.strptime(nueva_fecha, '%d %m, %Y')

    return fechaNueva_date

def check_date(fechaInicio: str, fechaFin: str, reservas: List):

    ts_fechaInicio = datetime.strptime(fechaInicio, '%Y-%m-%d %H:%M:%S').timestamp()
    ts_fechaFin = datetime.strptime(fechaFin, '%Y-%m-%d %H:%M:%S').timestamp()

    ts = time.time()

    if ts > ts_fechaInicio:
        return 0

    for reserva in reservas:
        ts_fechaInicio_Reserva = datetime.strptime(reserva["fechaInicio"], '%Y-%m-%d %H:%M:%S').timestamp()
        ts_fechaFin_Reserva = datetime.strptime(reserva["fechaFin"], '%Y-%m-%d %H:%M:%S').timestamp()

        if ts_fechaInicio <= ts_fechaInicio_Reserva and ts_fechaFin >= ts_fechaInicio_Reserva:
            return 1

        elif ts_fechaInicio >= ts_fechaInicio_Reserva and ts_fechaInicio <= ts_fechaFin_Reserva:
            return 1
        
    return 2

@vivienda.post('/viviendas/{id}/nueva/reserva')
async def create_reserva(id: str, request: Request):
    validez = check_token(request)

    if validez:

        form = await request.form()

        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.get(url + '/viviendas/' + id, headers=headers)
        vivienda = response.json()
        nueva_vivienda = jsonable_encoder(vivienda)

        if nueva_vivienda["reservas"] is None:
            nueva_vivienda["reservas"] = []

        fechaInicio = form["input_from"]
        fechaFin = form["input_to"]

        if fechaInicio == "" or fechaFin == "":
            reservasFuturas = reservas_futuras(nueva_vivienda["reservas"])
            return Templates.TemplateResponse("vivienda/reservarVivienda.html", {"request": request, "vivienda": vivienda, "reservasFuturas":reservasFuturas, "error": "Debes seleccionar las fechas correspondientes", "segment": "index" })

        fechaInicio = str(nueva_fecha(fechaInicio))
        fechaFin = str(nueva_fecha(fechaFin))

        if check_date(fechaInicio, fechaFin, nueva_vivienda["reservas"]) == 0:
            reservasFuturas = reservas_futuras(nueva_vivienda["reservas"])
            return Templates.TemplateResponse("vivienda/reservarVivienda.html", {"request": request, "vivienda": vivienda, "reservasFuturas":reservasFuturas, "error": "No se pueden reservar fechas pasadas", "segment": "index" })

        elif check_date(fechaInicio, fechaFin, nueva_vivienda["reservas"]) == 1:
            reservasFuturas = reservas_futuras(nueva_vivienda["reservas"])
            return Templates.TemplateResponse("vivienda/reservarVivienda.html", {"request": request, "vivienda": vivienda, "reservasFuturas":reservasFuturas, "error": "Fecha ya reservada", "segment": "index" })

        else:

            reserva = {
                "fechaInicio" : fechaInicio,
                "fechaFin" : fechaFin,
                "precio" : nueva_vivienda["precio"],
                "username" : validez,
                "vivienda" : nueva_vivienda["id"]
            }

            reserva_vivienda = {
                "fechaInicio" : fechaInicio,
                "fechaFin" : fechaFin,
                "username" : validez
            }

            # Parse the dates into datetime objects
            dt1 = datetime.strptime(fechaInicio, "%Y-%m-%d %H:%M:%S")
            dt2 = datetime.strptime(fechaFin, "%Y-%m-%d %H:%M:%S")

            # Find the difference between the two dates
            difference = dt2 - dt1

            # Print the number of days
            dias_reservados = difference.days
            precio_total = dias_reservados * float(nueva_vivienda["precio"])

            nueva_vivienda["reservas"].append(reserva_vivienda)

            # Localize the month name to Spanish
            month1 = format_date(dt1, "MMMM", locale='es_ES')
            month2 = format_date(dt2, "MMMM", locale='es_ES')

            fechaInicio = str(dt1.day) + " de " + month1 + " de " + str(dt1.year) 
            fechaFin = str(dt2.day) + " de " + month2 + " de " + str(dt2.year) 

            return Templates.TemplateResponse("paypal/paypal.html", {"request": request, "vivienda": nueva_vivienda, "reserva" : reserva,
                                                                     "fechaInicio" : fechaInicio, "dias" : dias_reservados, "fechaFin" : fechaFin,
                                                                     "precio_total" : precio_total, "segment": "index" })
    else:
        return RedirectResponse(url_inicio)
#endregion

#region pago
@vivienda.post('/viviendas/paypal/finalizar/pago')
async def finalizar_reserva_vivienda(request: Request):
    validez = check_token(request)

    if validez:

        body = await request.json()

        vivienda = html.unescape(body['vivienda'])
        reserva = html.unescape(body['reserva'])

        vivienda_dict = ast.literal_eval(vivienda)
        reserva_dict = ast.literal_eval(reserva)

        id = vivienda_dict["id"]
        
        #Update vivienda con la reserva nueva
        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.put(url + '/viviendas/' + id,json=vivienda_dict, headers=headers)
        
        #Crear la reserva
        requests.post(url + '/reservas', json=reserva_dict, headers=headers)

        # Email usuario
        await enviarEmail(validez, vivienda_dict, reserva_dict, False)

        #Email propietario
        await enviarEmail(vivienda_dict["propietario"], vivienda_dict, reserva_dict, True)

        url_actual = request.url_for('find_reserva_by_propietario')
    else:
        return RedirectResponse(url_inicio)

#endregion

#region Obtener mis Reservas
@vivienda.get('/viviendas/propietario/reservas')
async def find_reserva_by_propietario(request : Request):
    validez = check_token(request)

    if validez:
        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.get(url + '/reservas/todas/propietario', headers=headers)
        reservas = response.json()
        reservasFuturas = []
        reservasPasadas = []

        ts = time.time()

        for reserva in reservas:
            fecha = reserva["fechaFin"]
            ts_fecha = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S').timestamp()
            
            if ts >= ts_fecha:
                reservasPasadas.append(reserva)
            else:
                reservasFuturas.append(reserva)

            vivienda = requests.get(url + '/viviendas/' + reserva["vivienda"], headers=headers).json()
            nombreVivienda = {"nombreVivienda":vivienda["nombre"]}
            reserva.update(nombreVivienda)

            reseñaExistente = False
            for reseña in vivienda["reseñas"]:
                if reseña["username"] == validez:
                    reseñaExistente = True

            reseñaYaExistente = {"reseñaExistente":reseñaExistente}
            reserva.update(reseñaYaExistente)

            reserva["fechaInicio"] = reserva["fechaInicio"].split(" ")[0]
            reserva["fechaFin"] = reserva["fechaFin"].split(" ")[0]
        
        return Templates.TemplateResponse("vivienda/misReservas.html", {"request": request, "reservasPasadas" : reservasPasadas,"reservasFuturas":reservasFuturas, "segment": "misReservas" }) 
    else:
        return RedirectResponse(url_inicio)
#endregion

#region Crear Nueva Valoración
@vivienda.get('/viviendas/{id}/nueva/valoracion')
async def get_valoracion(id: str, request: Request):
    validez = check_token(request)

    if validez:
        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.get(url + '/viviendas/' + id, headers=headers)
        vivienda = response.json()

        for reseña in vivienda["reseñas"]:
                if reseña["username"] == validez:
                    url_actual = request.url_for("find_reserva_by_propietario")
                    return RedirectResponse(url_actual)

        return Templates.TemplateResponse("vivienda/reseñaVivienda.html", {"request": request, "vivienda": vivienda, "segment": "index" })
    else:
        return RedirectResponse(url_inicio)


@vivienda.post('/viviendas/{id}/nueva/valoracion')
async def create_valoracion(id: str, request: Request):
    validez = check_token(request)

    if validez:

        form = await request.form()

        headers = {'Authentication':request.cookies.get("session_id")}
        response = requests.get(url + '/viviendas/' + id, headers=headers)
        vivienda = response.json()
        nueva_vivienda = jsonable_encoder(vivienda)

        if nueva_vivienda["reseñas"] is None:
            nueva_vivienda["reseñas"] = []

        puntuacion = form["inputPuntuacion"]
        comentario = form["inputComentario"]

        if comentario != "" and puntuacion != "":
            puntuacion = float(puntuacion)

            if puntuacion >= 0 and puntuacion <= 5:

                date = datetime.now()
                dt_string = date.strftime("%Y-%m-%d %H:%M:%S")

                reseña = {
                    'username' : validez,
                    'puntuacion' : puntuacion,
                    'comentario' : comentario,
                    'fecha' : dt_string
                }
                

                nueva_vivienda["reseñas"].append(reseña)

                puntuacionTotal = 0
                puntuacionesTotales = 0

                for reseña in nueva_vivienda["reseñas"]:
                    puntuacionTotal = puntuacionTotal + reseña["puntuacion"]
                    puntuacionesTotales = puntuacionesTotales + 1
                
                nueva_vivienda["valoracion"] = puntuacionTotal/puntuacionesTotales

                response = requests.put(url + '/viviendas/' + id,json=nueva_vivienda, headers=headers)

                url_actual = request.url_for('find_reserva_by_propietario')
                return RedirectResponse(url_actual, status_code=status.HTTP_303_SEE_OTHER)
            
            else:
                return Templates.TemplateResponse("vivienda/reseñaVivienda.html", {"request": request, "vivienda": vivienda, "comentario": comentario, "error": "La puntuación debe estar entre 0 y 5", "segment": "index" })
        else:
            return Templates.TemplateResponse("vivienda/reseñaVivienda.html", {"request": request, "vivienda": vivienda, "comentario": comentario, "puntuacion": puntuacion, "error": "Debes rellenar todos los campos", "segment": "index" })
                    
    else:
        return RedirectResponse(url_inicio)
#endregion

#region Email Automático
async def enviarEmail(to_email: str, vivienda: dict, reserva: dict, propietario: bool):
    subject = 'Vivienda reservada con éxito'

    if propietario:
        body = 'Buenas,\n\n Se ha realizado una reserva a una de sus viviendas con éxito. \n\n Datos de la reserva: \n\n Nombre vivienda: ' + vivienda["nombre"] + '\n Descripcion vivienda: ' + vivienda["descripcion"] + '\n Precio Noche: ' + str(vivienda["precio"]) + ' €/noche \n Fecha Inicio: ' + reserva["fechaInicio"].split(" ")[0] + '\n Fecha Fin: ' + reserva["fechaFin"].split(" ")[0] + '\n Usuario: ' + reserva["username"] +'\n\n Muchas gracias por confiar en nosotros. \n Saludos, \n\n Casas Tapia - Grupo A4'
    else:
        body = 'Buenas,\n\n La reserva realizada se ha completado con éxito. \n\n Datos de la reserva: \n\n Nombre vivienda: ' + vivienda["nombre"] + '\n Descripcion vivienda: ' + vivienda["descripcion"] + '\n Precio Noche: ' + str(vivienda["precio"]) + ' €/noche \n Fecha Inicio: ' + reserva["fechaInicio"].split(" ")[0] + '\n Fecha Fin: ' + reserva["fechaFin"].split(" ")[0] + '\n\n Muchas gracias por confiar en nosotros. \n Saludos, \n\n Casas Tapia - Grupo A4'

    message = MIMEMultipart()
    message['From'] = gmail_user
    message['To'] = to_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    try:
        session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
        session.starttls() #enable security
        session.login(gmail_user, gmail_password) #login with mail_id and password
        text = message.as_string()
        session.sendmail(gmail_user, to_email, text)
        session.quit()
        print('Mail Sent')
    except Exception as e:
        print(e)
#endregion