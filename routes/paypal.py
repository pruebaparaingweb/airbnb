from fastapi import APIRouter, Body, status #APIRouter: nos permite definir todas las rutas dentro de este archivo
from fastapi.templating import Jinja2Templates
from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from typing import List
import requests
from datetime import datetime
from json import JSONDecodeError
import json
import time
from fastapi import APIRouter, Request
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment
from paypalcheckoutsdk.orders import OrdersCreateRequest
from fastapi.responses import JSONResponse
import html
from routes.conversacion import url

Templates = Jinja2Templates(directory="templates")

paypal = APIRouter()

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

# Creating Access Token for Sandbox
client_id = "AWoA_0edBucmV3xTeqWnbfq1VP83lWrx4yVHGUiJ246iOPQ-4bEKcDM62WudhtWk7GLY0Esgnzght5BM"
client_secret = "ECy30GCYCh2bz-fpU2gDe5JfNGBpbNxqWyFSMvX4L4V421LKh5KomplAwom4tJgrh0snXAkX8n9lml0l"


# Preuba para inge. web
# client_id = "AQY70u7SFmNWknB9RpWjKFpsvrK1zCE0OBJswtgJzQIld2kjc5APW44xP9lEHeEuQbTRntT8p4o4veMP"
# client_secret = "EDmpW-YGU18EikUlu83XT0dYCGHiGFG2_md_ACbVKdGyjJGEcMjxcpe0Wpyifnc038hK-ccl2psDF3uh"

# Creating an environment
environment = SandboxEnvironment(
    client_id=client_id, client_secret=client_secret)
client = PayPalHttpClient(environment)


@paypal.post("/www/paypal/api/orders")
async def create_order_paypal(request: Request):
    try:
        products =  await request.json()

        # Parse the JSON string into a dictionary
        precio = products["items"]["unit_amount"]["value"]   
        request = OrdersCreateRequest()

        request.prefer('return=representation')
        request.request_body(
            {
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "amount": {
                            "currency_code": 'EUR',
                            "value": precio
                        }
                    }
                ],
                "items": products
            }
        )
        response = client.execute(request)
        return JSONResponse(content={"id": response.result.id})
    except JSONDecodeError:
        print("Error")

@paypal.get("/www/paypal/terminar/pedido")
async def finalizar_pago_reserva(request : Request):
    return RedirectResponse("")