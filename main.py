import uvicorn
import httpx
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from routers import auth, midi

async def call_api():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/auth/login")
            print(f"Response status code: {response.status_code}")
    except httpx.RequestError as e:
        print(f"An error occurred while making the request: {e}")

async def scheduler():
    while True:
        try:
            await call_api()
        except Exception as e:
            print(f"An unexpected error occurred in the scheduler: {e}")
        await asyncio.sleep(3)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup")

    scheduler_task = asyncio.create_task(scheduler())

    yield

    print("Application shutdown")
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(midi.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)