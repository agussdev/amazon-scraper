<template>
  <div class="container">
    <h1><a href="https://t.me/+Yqjt6ap25kxmYmJk" target="_blank">@svqdev</a> Amazon Scraper</h1>
    
    <!-- Tabs -->
    <div class="tabs">
      <button 
        :class="['tab-button', { active: activeTab === 'search' }]"
        @click="activeTab = 'search'"
      >
        Buscador
      </button>
      <button 
        :class="['tab-button', { active: activeTab === 'tasks' }]"
        @click="activeTab = 'tasks'"
      >
        Tareas Activas <span v-if="tasks.length" class="task-count">{{ tasks.length }}</span>
      </button>
      <button 
        :class="['tab-button', { active: activeTab === 'history' }]"
        @click="loadHistory"
      >
        Historial
      </button>
    </div>

    <!-- Search Tab -->
    <div v-if="activeTab === 'search'" class="tab-content">
      <div class="search-form">
        <div class="form-group">
          <label for="keyword">Palabra clave:</label>
          <input 
            type="text" 
            id="keyword" 
            v-model="keyword" 
            placeholder="Introduce palabra clave"
          >
        </div>
        
        <div class="form-group">
          <label for="numResults">Número de resultados:</label>
          <input 
            type="number" 
            id="numResults" 
            v-model="numResults" 
            min="1"
          >
        </div>
        
        <button @click="createTask" :disabled="isLoading">
          {{ isLoading ? 'Creando tarea...' : 'Iniciar búsqueda' }}
        </button>
      </div>
    </div>

    <!-- Tasks Tab -->
    <div v-if="activeTab === 'tasks'" class="tab-content">
      <div v-if="tasks.length > 0" class="tasks-list">
        <div v-for="task in tasks" :key="task.id" class="task-card">
          <div class="task-header">
            <h3>Búsqueda: {{ task.keyword }}</h3>
            <div class="task-actions">
              <button 
                v-if="task.status === 'running'"
                @click="cancelTask(task.id)"
                class="cancel-button"
              >
                Cancelar
              </button>
              <span class="task-status" :class="task.status">{{ getStatusText(task.status) }}</span>
            </div>
          </div>
          
          <div class="task-stats">
            <div class="stat">
              <span class="stat-label">Productos procesados:</span>
              <span class="stat-value">{{ task.total_processed }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">Resultados encontrados:</span>
              <span class="stat-value">{{ task.found_results }}</span>
            </div>
          </div>

          <div class="progress-container">
            <div class="progress-bar">
              <div 
                class="progress" 
                :style="{ width: `${task.progress}%` }"
              ></div>
            </div>
            <span class="progress-text">{{ Math.round(task.progress) }}%</span>
          </div>

          <div class="task-details">
            <p>Estado: {{ task.status }}</p>
            <p>Productos procesados: {{ task.total_processed }}</p>
            <p>Resultados encontrados: {{ task.found_results }}</p>
            <p v-if="task.error" class="error">Error: {{ task.error }}</p>
          </div>

          <!-- Tabla de resultados -->
          <table v-if="task.results && task.results.length > 0" class="results-table">
            <thead>
              <tr>
                <th>Nombre del producto</th>
                <th>Precio</th>
                <th>Política de devolución</th>
                <th>Link</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(result, index) in task.results" :key="index">
                <td>{{ result.product_name }}</td>
                <td>{{ result.price }}</td>
                <td>{{ result.return_policy }}</td>
                <td>
                  <a :href="result.link" target="_blank" class="view-product-btn">
                    Ver producto
                  </a>
                </td>
              </tr>
            </tbody>
          </table>

          <div class="task-actions" v-if="task.status === 'completed'">
            <button 
              @click="downloadResults(task.id)"
              class="download-button"
            >
              Descargar Resultados
            </button>
          </div>
        </div>
      </div>
      <div v-else class="no-tasks">
        No hay tareas activas
      </div>
    </div>

    <!-- History Tab -->
    <div v-if="activeTab === 'history'" class="tab-content">
      <div v-if="taskHistory.length > 0" class="history-list">
        <div v-for="task in taskHistory" :key="task.id" class="task-card">
          <div class="task-header">
            <span>Búsqueda: {{ task.keyword }}</span>
            <span>{{ new Date(task.created_at).toLocaleString() }}</span>
          </div>
          <div class="task-details">
            <p>Estado: {{ task.status }}</p>
            <p>Resultados encontrados: {{ task.found_results }}</p>
          </div>
          
          <table v-if="task.results && task.results.length > 0" class="results-table">
            <thead>
              <tr>
                <th>Nombre del producto</th>
                <th>Precio</th>
                <th>Política de devolución</th>
                <th>Link</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(result, index) in task.results" :key="index">
                <td>{{ result.product_name }}</td>
                <td>{{ result.price }}</td>
                <td>{{ result.return_policy }}</td>
                <td>
                  <a :href="result.link" target="_blank" class="view-product-btn">
                    Ver producto
                  </a>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-else class="no-history">
        No hay búsquedas en el historial
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'App',
  data() {
    return {
      activeTab: 'search',
      keyword: '',
      numResults: 10,
      isLoading: false,
      tasks: [],
      updateInterval: null,
      taskHistory: [],
    }
  },
  methods: {
    async checkTasksStatus() {
      for (const task of this.tasks) {
        if (task.status === 'running') {
          try {
            const response = await axios.get(`http://localhost:8000/task-status/${task.id}`);
            const updatedTask = response.data;
            
            // Actualizar la tarea existente manteniendo la reactividad
            const index = this.tasks.findIndex(t => t.id === task.id);
            if (index !== -1) {
              Object.assign(this.tasks[index], updatedTask);
            }
          } catch (error) {
            console.error('Error al actualizar estado de tarea:', error);
          }
        }
      }
    },
    
    startTasksUpdate() {
      // Actualizar cada 500ms mientras haya tareas en ejecución
      this.updateInterval = setInterval(() => {
        if (this.tasks.some(task => task.status === 'running')) {
          this.checkTasksStatus();
        } else {
          clearInterval(this.updateInterval);
        }
      }, 500);
    },
    
    async createTask() {
      try {
        this.isLoading = true;
        const response = await axios.post('http://localhost:8000/create-task', {
          keyword: this.keyword,
          num_results: this.numResults
        });

        const newTask = {
          id: response.data.task_id,
          keyword: this.keyword,
          num_results: this.numResults,
          status: 'running',
          progress: 0,
          total_processed: 0,
          found_results: 0,
          results: []
        };

        this.tasks.unshift(newTask);
        this.startTasksUpdate();
        
        // Limpiar el formulario
        this.keyword = '';
        this.numResults = 10;
        
        // Cambiar a la pestaña de tareas
        this.activeTab = 'tasks';
      } catch (error) {
        console.error('Error al crear la tarea:', error);
      } finally {
        this.isLoading = false;
      }
    },

    async loadHistory() {
      this.activeTab = 'history';
      try {
        const response = await axios.get('http://localhost:8000/task-history');
        this.taskHistory = response.data;
      } catch (error) {
        console.error('Error al cargar el historial:', error);
      }
    },

    async cancelTask(taskId) {
      try {
        await axios.post(`http://localhost:8000/cancel-task/${taskId}`);
        // Opcional: Actualizar el estado de la tarea inmediatamente en el frontend
        const taskIndex = this.tasks.findIndex(t => t.id === taskId);
        if (taskIndex !== -1) {
          this.tasks[taskIndex].status = 'cancelling';
        }
      } catch (error) {
        console.error('Error al cancelar la tarea:', error);
      }
    },
    
    getStatusText(status) {
      const statusMap = {
        'running': 'En progreso',
        'completed': 'Completada',
        'failed': 'Error',
        'cancelled': 'Cancelada',
        'cancelling': 'Cancelando...'
      };
      return statusMap[status] || status;
    },

    async downloadResults(taskId) {
      try {
        // Hacer la petición para descargar el archivo
        const response = await axios.get(
          `http://localhost:8000/download-results/${taskId}`,
          { responseType: 'blob' }  // Importante para recibir el archivo
        );
        
        // Crear un blob con la respuesta
        const blob = new Blob([response.data], { type: 'application/json' });
        
        // Crear URL del blob
        const url = window.URL.createObjectURL(blob);
        
        // Crear un elemento <a> temporal
        const link = document.createElement('a');
        link.href = url;
        
        // Obtener el nombre del archivo del header de la respuesta o usar uno por defecto
        const contentDisposition = response.headers['content-disposition'];
        const filename = contentDisposition
          ? contentDisposition.split('filename=')[1].replace(/"/g, '')
          : `amazon_results_${taskId}.json`;
        
        link.setAttribute('download', filename);
        
        // Añadir el link al documento, hacer click y removerlo
        document.body.appendChild(link);
        link.click();
        link.remove();
        
        // Liberar la URL del blob
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error('Error al descargar resultados:', error);
        // Mostrar mensaje de error al usuario
        alert('Error al descargar los resultados. Por favor, intenta de nuevo.');
      }
    }
  },
  beforeUnmount() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
    }
  }
}
</script>

<style>
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.search-form {
  padding: 20px;
  background: #373535;
  border-radius: 8px;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
  color: #e0e0e0;
}

input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

button {
  padding: 10px 20px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background: #cccccc;
}

.task-card {
  background: #373535;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.task-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.9em;
  font-weight: 500;
}

.task-status.running {
  background: #2196F3;
  color: white;
}

.task-status.completed {
  background: #4CAF50;
  color: white;
}

.task-status.failed {
  background: #f44336;
  color: white;
}

.task-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.stat {
  background: #242424;
  padding: 10px 15px;
  border-radius: 6px;
  flex: 1;
}

.stat-label {
  display: block;
  color: #888;
  font-size: 0.9em;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 1.2em;
  color: #fff;
  font-weight: 500;
}

.progress-container {
  margin: 15px 0;
}

.progress-bar {
  background: #242424;
  height: 10px;
  border-radius: 5px;
  overflow: hidden;
  margin-bottom: 5px;
  border: 1px solid #333;
}

.progress {
  background: linear-gradient(90deg, #4CAF50, #45a049);
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 5px;
}

.progress-text {
  font-size: 0.9em;
  color: #888;
  display: block;
  text-align: center;
}

.task-details {
  margin-top: 10px;
}

.error {
  color: red;
}

.results-section {
  margin-top: 30px;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
  background: #1a1a1a;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.results-table th,
.results-table td {
  padding: 15px;
  text-align: left;
  border: 1px solid #333;
  color: #e0e0e0;
}

.results-table th {
  background-color: #2c2c2c;
  font-weight: bold;
  color: #fff;
}

.results-table tr {
  transition: background-color 0.3s ease;
}

.results-table tr:nth-child(even) {
  background-color: #242424;
}

.results-table tr:hover {
  background-color: #2a2a2a;
}

.view-product-btn {
  display: inline-block;
  padding: 8px 16px;
  background-color: #4CAF50;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  transition: all 0.3s ease;
  text-align: center;
  font-size: 0.9em;
  border: none;
  cursor: pointer;
}

.view-product-btn:hover {
  background-color: #45a049;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.view-product-btn:active {
  transform: translateY(0);
  box-shadow: none;
}

/* Ajustar el ancho de las columnas */
.results-table th:nth-child(1) {
  width: 40%;  /* Nombre del producto */
}

.results-table th:nth-child(2) {
  width: 15%;  /* Precio */
}

.results-table th:nth-child(3) {
  width: 25%;  /* Política de devolución */
}

.results-table th:nth-child(4) {
  width: 20%;  /* Link */
  text-align: center;
}

.results-table td:last-child {
  text-align: center;  /* Centrar el botón */
}

/* Estilos para los títulos */
h2, h3 {
  color: #e0e0e0;
  margin-bottom: 1rem;
}

/* Estilos para la barra de progreso */
.task-progress {
  margin: 1rem 0;
}

.progress-bar {
  background: #2c2c2c;
  border: 1px solid #333;
}

.progress {
  background: #4CAF50;
}

.tabs {
  display: flex;
  margin-bottom: 20px;
  border-bottom: 1px solid #333;
}

.tab-button {
  padding: 10px 20px;
  margin-right: 10px;
  background: transparent;
  border: none;
  color: #e0e0e0;
  cursor: pointer;
  position: relative;
  transition: all 0.3s ease;
}

.tab-button.active {
  color: #4CAF50;
  border-bottom: 2px solid #4CAF50;
}

.tab-button:hover {
  background: #2a2a2a;
}

.task-count {
  background: #4CAF50;
  color: white;
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 0.8em;
  margin-left: 5px;
}

.no-tasks {
  text-align: center;
  padding: 20px;
  color: #888;
}

.tab-content {
  padding: 20px;
  background: #1a1a1a;
  border-radius: 8px;
}

.task-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cancel-button {
  padding: 6px 12px;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
  transition: all 0.3s ease;
}

.cancel-button:hover {
  background-color: #c82333;
  transform: translateY(-1px);
}

.cancel-button:active {
  transform: translateY(0);
}

.task-status.cancelled {
  background: #6c757d;
  color: white;
}

.task-status.cancelling {
  background: #ffc107;
  color: #000;
}

body {
  margin: 0;
  background-color: #1a1a1a;
  color: #e0e0e0;
  font-family: Arial, sans-serif;
}

.download-button {
  padding: 8px 16px;
  background-color: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.download-button:hover {
  background-color: #1976D2;
  transform: translateY(-1px);
}

.download-button:active {
  transform: translateY(0);
}
</style>