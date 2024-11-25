from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

REQUEST_COUNT = Counter(
    'http_requests_total', 'Tasa de solicitudes HTTP por método y estado',
    ['method', 'endpoint', 'http_status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds', 'Latencia de solicitudes HTTP por endpoint',
    ['method', 'endpoint']
)

instrumentator = Instrumentator(
    should_group_status_codes=False,  # Captura métricas por códigos HTTP específicos
    should_ignore_untemplated=True,  # Evita capturar rutas dinámicas con parámetros
)

# Agrega métricas automáticas y personalizadas
instrumentator.add(
    lambda: REQUEST_COUNT
).add(
    lambda: REQUEST_LATENCY)

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Inicio del temporizador para medir la latencia
        method = request.method
        endpoint = request.url.path
        with REQUEST_LATENCY.labels(method=method, endpoint=endpoint).time():
            response = await call_next(request)
        
        # Incrementa el contador de solicitudes HTTP
        REQUEST_COUNT.labels(
            method=method, 
            endpoint=endpoint, 
            http_status=response.status_code
        ).inc()
        
        return response
