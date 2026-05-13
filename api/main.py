"""TRADO FastAPI"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="TRADO",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])

@app.get("/health")
async def health(): return {"status":"healthy","service":"TRADO"}

@app.get("/api/status")
async def status(): return {"bot_running":True,"env":os.getenv("ENVIRONMENT","prod")}