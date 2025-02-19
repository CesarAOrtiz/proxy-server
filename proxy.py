from fastapi import FastAPI, Request
import requests
import random
import time
from stem import Signal
from stem.control import Controller
from concurrent.futures import ThreadPoolExecutor
from fastapi.responses import Response

app = FastAPI()

# Lista de instancias de Tor con diferentes puertos
TOR_PROXIES = [
    {"http": "http://127.0.0.1:8118", "https": "http://127.0.0.1:8118"},
]

# ThreadPool para manejar cambios de IP sin bloquear solicitudes
executor = ThreadPoolExecutor(max_workers=len(TOR_PROXIES))

# Función para cambiar la IP sin bloquear otras solicitudes


def renew_tor_ip():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)
        time.sleep(3)  # Esperar para que la nueva IP se aplique


@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy(request: Request, full_path: str):
    try:
        # Construir la URL completa de destino
        target_url = f"http://{full_path}" if not full_path.startswith(
            "http") else full_path

        # Usar Privoxy como proxy HTTP y HTTPS
        proxies = random.choice(TOR_PROXIES)

        # Renovar la IP en segundo plano
        executor.submit(renew_tor_ip)

        # Preparar los headers originales y asegurarse de incluir el `Host`
        headers = dict(request.headers)
        headers["Host"] = target_url.replace(
            "https://", "").replace("http://", "").split("/")[0]

        # Preparar el body de la solicitud (para POST, PUT, etc.)
        body = await request.body()

        # Hacer la solicitud con el método original
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=body if request.method in ["POST", "PUT", "PATCH"] else None,
            params=request.query_params,
            cookies=request.cookies,
            proxies=proxies,
            timeout=30
        )

        # Devolver la respuesta exactamente como la del servidor original
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )

    except requests.exceptions.RequestException as e:
        return Response(content=f"Error al acceder a {target_url}: {str(e)}", status_code=500)


@app.get("/")
async def root():
    return {"message": "Proxy API is running. Use /proxy?url=<your_url> to make requests."}
