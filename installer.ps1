# 1º Descargar e instalar Python
Write-Output "Descargando e instalando Python..."
$pythonInstallerUrl = "https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe"
$pythonInstallerPath = "$env:TEMP\python_installer.exe"
Invoke-WebRequest -Uri $pythonInstallerUrl -OutFile $pythonInstallerPath
Start-Process -FilePath $pythonInstallerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait

# 2º Asegurarse de que pip está instalado
Write-Output "Verificando la instalación de pip..."
python -m ensurepip --default-pip

# 3º Descargar e instalar Node.js (versión LTS)
Write-Output "Descargando e instalando Node.js..."
$nodeInstallerUrl = "https://nodejs.org/dist/v22.11.0/node-v22.11.0-x64.msi"
$nodeInstallerPath = "$env:TEMP\node_installer.msi"
Invoke-WebRequest -Uri $nodeInstallerUrl -OutFile $nodeInstallerPath
Start-Process -FilePath "msiexec.exe" -ArgumentList "/i $nodeInstallerPath /quiet" -Wait

# 4º Descargar e instalar Git
Write-Output "Descargando e instalando Git..."
$gitInstallerUrl = "https://github.com/git-for-windows/git/releases/download/v2.42.0.windows.1/Git-2.42.0-64-bit.exe"
$gitInstallerPath = "$env:TEMP\git_installer.exe"
Invoke-WebRequest -Uri $gitInstallerUrl -OutFile $gitInstallerPath
Start-Process -FilePath $gitInstallerPath -ArgumentList "/VERYSILENT" -Wait

# 5º Clonar el repositorio de GitHub
Write-Output "Clonando el repositorio de GitHub..."
$repositoryUrl = "https://github.com/usuario/repositorio.git"  # Reemplaza con la URL de tu repositorio
$destinationPath = "C:\"  # Reemplaza con la ubicación donde deseas clonar el repositorio
git clone $repositoryUrl $destinationPath

# 6º Cambiar al directorio del proyecto
Write-Output "Cambiando al directorio del proyecto..."
Set-Location -Path $destinationPath

# 7º Instalar los paquetes de Python desde requirements.txt
Write-Output "Instalando los paquetes de Python desde requirements.txt..."
pip install -r requirements.txt

# 8º Ejecutar api/app.py
Write-Output "Ejecutando api/app.py..."
Start-Process -FilePath "python" -ArgumentList "api/app.py"

# 9º Cambiar al directorio del frontend y ejecutar npm install
Write-Output "Cambiando al directorio del frontend y ejecutando npm install..."
Set-Location -Path "$destinationPath\frontend"
npm install

# 10º Ejecutar npm run dev
Write-Output "Ejecutando npm run dev..."
npm run dev
