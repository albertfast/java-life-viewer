from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
import subprocess
from pathlib import Path

app = FastAPI()

# Static files
app.mount("/static", StaticFiles(directory="."), name="static")

# Java process
java_process = None

async def stream_java_output(websocket: WebSocket):
    """Stream Java output to WebSocket"""
    global java_process
    
    try:
        # Start Java process
        java_process = subprocess.Popen(
            ["java", "Main"],
            cwd="./java",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Stream output
        for line in iter(java_process.stdout.readline, ''):
            if line:
                await websocket.send_text(line)
                await asyncio.sleep(0.05)  # Smooth streaming
                
    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")
    finally:
        if java_process:
            java_process.terminate()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await stream_java_output(websocket)

@app.get("/")
async def get_home():
    return HTMLResponse(content=open("index.html").read())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
