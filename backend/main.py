from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from database import get_connection


app = FastAPI(
    title="ER Recall API",
    version="0.1.0",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
            }
        },
    )


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