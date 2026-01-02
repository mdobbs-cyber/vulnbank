import docker
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serves build artifacts
# Make sure to mount API first so it takes precedence


class ContainerInfo(BaseModel):
    name: str
    status: str
    state: str
    health: Optional[str] = None
    provisioning_complete: bool = True

class StatusResponse(BaseModel):
    containers: List[ContainerInfo]
    game_start_time: Optional[str] = None

@app.get("/api/status", response_model=StatusResponse)
def get_status():
    client = docker.from_env()
    containers = client.containers.list(all=True)
    result = []
    
    earliest_creation = None

    for container in containers:
        name = container.name
        status = container.status # e.g., 'running', 'exited'
        state = container.attrs['State']['Status']
        health = container.attrs['State'].get('Health', {}).get('Status')
        created = container.attrs['Created']
        
        # Track earliest creation time for running containers as "start of game"
        if status == 'running':
            if earliest_creation is None or created < earliest_creation:
                earliest_creation = created

        # specific check for splunk forwarder provisioning
        provisioning = True
        if "splunk-forwarder" in name:
            try:
                # Check logs for Ansible completion
                logs = container.logs().decode('utf-8')
                if "PLAY RECAP" not in logs:
                    provisioning = False
            except Exception:
                provisioning = False
        
        result.append(ContainerInfo(
            name=name,
            status=status,
            state=state,
            health=health,
            provisioning_complete=provisioning
        ))
    
    # Sort by name for consistent display
    result.sort(key=lambda x: x.name)

    return StatusResponse(containers=result, game_start_time=earliest_creation)

# Serve React App
app.mount("/", StaticFiles(directory="/app/frontend_dist", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
