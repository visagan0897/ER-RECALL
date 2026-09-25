from fastapi import FastAPI

app = FastAPI(title="ER Recall API")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "er-recall-api"
    }