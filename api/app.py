import sys
import os
# Añadir el directorio raíz al PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.scrape_heading_task import scrape_heading_task
from src.scrape_query import scrape_query
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Optional
from storage import JSONStorage
import random
import string
from fastapi.responses import FileResponse
import json

app = FastAPI()
executor = ThreadPoolExecutor(max_workers=5)
storage = JSONStorage()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchTask(BaseModel):
    keyword: str
    num_results: int = 10

class TaskResponse(BaseModel):
    id: str
    keyword: str
    status: str
    progress: float
    total_processed: int
    found_results: int
    results: List[dict] = []
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

def get_client_ip(request: Request) -> str:
    return request.client.host

# Añadir un diccionario para controlar las tareas activas
active_tasks = {}

def run_search(task_id: str, keyword: str, num_results: int):
    try:
        # Procesar keyword para reemplazar espacios con '+'
        processed_keyword = '+'.join(keyword.split())
        
        all_results = []
        valid_policies = [
            "Ver política de devoluciones",
            "Ver políticas de devolución",
            "Ver política de devolución del vendedor",
            "Ver políticas de devolución del vendedor"
        ]
        
        page = 1
        productos_procesados = 0
        
        while len(all_results) < num_results:
            task = storage.get_task(task_id)
            if task["status"] == "cancelling":
                raise Exception("Tarea cancelada por el usuario")
                
            results = scrape_query({"keyword": processed_keyword, "page": page})
            
            if not results:
                break
                
            for item in results:
                task = storage.get_task(task_id)
                if task["status"] == "cancelling":
                    raise Exception("Tarea cancelada por el usuario")
                
                productos_procesados += 1
                
                # Actualizar inmediatamente el contador de productos procesados
                storage.update_task(task_id, {
                    "total_processed": productos_procesados
                })
                
                url = item["link"]
                result = scrape_heading_task({"link": url})
                
                if result["return_policy"].lower() in [policy.lower() for policy in valid_policies]:
                    all_results.append(result)
                    
                    # Actualizar resultados y progreso en una actualización separada
                    progress = (len(all_results) / num_results) * 100
                    storage.update_task(task_id, {
                        "progress": progress,
                        "found_results": len(all_results),
                        "results": all_results
                    })
                
                if len(all_results) >= num_results:
                    break
            
            page += 1
        
        # Actualizar estado final
        storage.update_task(task_id, {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "progress": 100
        })
        
    except Exception as e:
        current_task = storage.get_task(task_id)
        final_status = "cancelled" if current_task["status"] == "cancelling" else "failed"
        
        storage.update_task(task_id, {
            "status": final_status,
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat()
        })

@app.post("/create-task")
async def create_task(task: SearchTask, request: Request):
    try:
        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        ip = get_client_ip(request)
        
        # Crear nueva tarea
        new_task = storage.create_task(task_id, ip, task.keyword, task.num_results)
        
        # Iniciar búsqueda en segundo plano
        executor.submit(run_search, task_id, task.keyword, task.num_results)
        
        return {"task_id": task_id, "message": "Tarea iniciada correctamente"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear la tarea: {str(e)}"
        )

@app.get("/task-status/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    task = storage.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return task

@app.get("/task-history", response_model=List[TaskResponse])
async def get_task_history(request: Request):
    ip = get_client_ip(request)
    return storage.get_tasks_by_ip(ip)

@app.post("/cancel-task/{task_id}")
async def cancel_task(task_id: str):
    task = storage.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    if task["status"] != "running":
        raise HTTPException(status_code=400, detail="Solo se pueden cancelar tareas en ejecución")
    
    active_tasks[task_id] = False
    return {"message": "Tarea cancelada correctamente"}

@app.get("/download-results/{task_id}")
async def download_results(task_id: str):
    # Obtener la tarea
    task = storage.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="La tarea aún no ha terminado")
    
    # Crear el nombre del archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"amazon_results_{task_id}_{timestamp}.json"
    
    # Crear el directorio temporal si no existe
    os.makedirs("temp", exist_ok=True)
    file_path = os.path.join("temp", filename)
    
    # Preparar los datos para el archivo
    export_data = {
        "task_id": task["id"],
        "keyword": task["keyword"],
        "total_results": task["found_results"],
        "completed_at": task["completed_at"],
        "results": task["results"]
    }
    
    # Guardar los datos en el archivo
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    # Devolver el archivo
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/json",
        background=BackgroundTask(lambda: os.remove(file_path))  # Eliminar el archivo después de enviarlo
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)