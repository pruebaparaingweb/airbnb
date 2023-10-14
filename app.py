from typing import Union
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from routes.vivienda import vivienda
from routes.usuario import usuario
from routes.paypal import paypal
from routes.conversacion import conversacion
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(
    title="A4ServidorRestConJinja",
    description="Servidor API REST para microservicios grupo A4",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key="web2223")

app.mount("/static", StaticFiles(directory="static"), name="static")
Templates = Jinja2Templates(directory="templates")

app.include_router(vivienda) # Incluye todas las rutas definidas para el vivienda
app.include_router(usuario) # Incluye todas las rutas definidas para el vivienda
app.include_router(conversacion)
app.include_router(paypal)
@app.get('/')
@app.get('/{path}')
async def index(request:Request, path: Union[str , None] = None):

    try:
        if (path == None):
            path = "index.html"

        # Detect the current page
        segment = get_segment( request )

        # Serve the file (if exists) from app/templates/FILE.html
        return Templates.TemplateResponse(path, {"request": request, "segment": segment}) 
        
    except:
       raise HTTPException(404)


def get_segment(request : Request ): 

    try:

        #Ultimo valor del path locahost:8000/algo.html -> segment = algo.html
        segment = request.url._url.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment    

    except:
        return None  

@app.exception_handler(404)
def page_not_found(request: Request, error : str):
    return Templates.TemplateResponse("page-404.html", {"request": request, "error" : error }) 

