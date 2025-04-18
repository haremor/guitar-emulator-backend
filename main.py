import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, midi

app = FastAPI()

app.include_router(auth.router)
app.include_router(midi.router)

allowed_origins = [
	'http://localhost:3000',
    'https://geb-front.onrender.com/'
]

app.add_middleware(
	CORSMiddleware,
	allow_origins=allowed_origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)