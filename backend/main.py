from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import gesture, intent, buffer_analysis, image_caption

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with prefix
app.include_router(gesture.router, prefix="/api")
app.include_router(intent.router, prefix="/api")
app.include_router(buffer_analysis.router, prefix="/api")
app.include_router(image_caption.router, prefix="/api")