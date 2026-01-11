#!/bin/bash

# Ruta a tus modelos
MODELS_DIR="./models" # <--- AJUSTA ESTA RUTA SI ES DISTINTA EN TU PC

echo "🚑 Iniciando reparación de modelos en: $MODELS_DIR"

# Damos permisos totales primero para poder mover las cosas
sudo chmod -R 777 "$MODELS_DIR"

# Buscamos todas las carpetas _temporary
find "$MODELS_DIR" -type d -name "_temporary" | while read temp_dir; do
    target_dir=$(dirname "$temp_dir")
    echo "🔧 Reparando: $target_dir"
    
    # Mover el contenido de las tareas temporales a la carpeta final
    # Buscamos en profundidad porque Spark crea subcarpetas tipo /0/task_...
    sudo find "$temp_dir" -type f -name "part-*" -exec mv {} "$target_dir/" \;
    sudo find "$temp_dir" -type f -name ".part-*" -exec mv {} "$target_dir/" \;
    
    # Borrar la carpeta temporal
    sudo rm -rf "$temp_dir"
    
    # Crear archivo _SUCCESS
    sudo touch "$target_dir/_SUCCESS"
done

# Volvemos a asegurar permisos 777 para que el contenedor de predicción pueda leerlos
sudo chmod -R 777 "$MODELS_DIR"

echo "✅ ¡Modelos reparados! Listando resultados:"
ls -R "$MODELS_DIR" | grep ":$" | head -n 10