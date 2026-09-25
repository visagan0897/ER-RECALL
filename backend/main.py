from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from database import get_connection


app = FastAPI(
    title="ER Recall API",
    version="0.1.0",
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    request_id = getattr(request.state, "request_id", str(uuid4()))

    response = JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
            },
            "request_id": request_id,
        },
    )
    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "er-recall-api",
    }


@app.get("/db-health")
def db_health():
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()

        return {
            "status": "ok",
            "database": "connected",
            "test_result": result[0],
        }
    finally:
        conn.close()