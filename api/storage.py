import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class JSONStorage:
    def __init__(self):
        self.file_path = "tasks_db.json"
        self.ensure_file_exists()

    def ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump([], f)

    def _read_tasks(self) -> List[Dict]:
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def _write_tasks(self, tasks: List[Dict]):
        with open(self.file_path, 'w') as f:
            json.dump(tasks, f, indent=2, default=str)

    def create_task(self, task_id: str, ip: str, keyword: str, num_results: int) -> Dict:
        tasks = self._read_tasks()
        new_task = {
            "id": task_id,
            "ip": ip,
            "keyword": keyword,
            "num_results": num_results,
            "status": "running",
            "progress": 0,
            "total_processed": 0,
            "found_results": 0,
            "results": [],
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "error": None
        }
        tasks.append(new_task)
        self._write_tasks(tasks)
        return new_task

    def get_task(self, task_id: str) -> Optional[Dict]:
        tasks = self._read_tasks()
        for task in tasks:
            if task["id"] == task_id:
                return task
        return None

    def update_task(self, task_id: str, updates: Dict):
        tasks = self._read_tasks()
        for task in tasks:
            if task["id"] == task_id:
                task.update(updates)
                break
        self._write_tasks(tasks)

    def get_tasks_by_ip(self, ip: str) -> List[Dict]:
        tasks = self._read_tasks()
        return [task for task in tasks if task["ip"] == ip] 