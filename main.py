from firebase_functions import https_fn
from backend.app.main import app as fastapi_app
from a2wsgi import ASGIMiddleware

wsgi_app = ASGIMiddleware(fastapi_app)

# Define a Cloud Function mapping all requests to our FastAPI app
@https_fn.on_request(
    region="asia-southeast1",
    timeout_sec=120,
    memory=2048,
    min_instances=0
)
def api(req: https_fn.Request) -> https_fn.Response:
    return https_fn.Response.from_app(wsgi_app, req.environ)
