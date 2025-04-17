import uvicorn
from fastapi import FastAPI
from routers import auth, midi

app = FastAPI()

app.include_router(auth.router)
app.include_router(midi.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)