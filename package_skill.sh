#!/usr/bin/env bash
# ==============================================================================
# Script de Empaquetado para la Skill: reporte-sullivan-sttupa-loco-tequila-us
# Compatible con Linux, macOS, WSL y Git Bash
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_ZIP="${1:-reporte-sullivan-sttupa-loco-tequila-us.zip}"

# Resolver ruta absoluta del archivo ZIP de salida
if [[ "$OUTPUT_ZIP" = /* ]]; then
    FINAL_ZIP="$OUTPUT_ZIP"
else
    FINAL_ZIP="$SCRIPT_DIR/$OUTPUT_ZIP"
fi

ZIP_DIR="$(dirname "$FINAL_ZIP")"
mkdir -p "$ZIP_DIR"

echo "======================================================================"
echo "  EMPAQUETADOR DE SKILL — DISTRIBUCIÓN MULTIPLATAFORMA (BASH)"
echo "======================================================================"
echo "Directorio base: $SCRIPT_DIR"
echo "Archivo destino: $FINAL_ZIP"

cd "$SCRIPT_DIR"

# Eliminar archivo ZIP previo si existe
if [[ -f "$FINAL_ZIP" ]]; then
    rm -f "$FINAL_ZIP"
fi

# Detectar binario de Python disponible
PY_BIN=""
for candidate in python3 python py "/e/Users/1167486/AppData/Local/anaconda3/python" "/c/Python3*/python" "/usr/bin/python3" "/usr/local/bin/python3"; do
    if command -v "$candidate" &>/dev/null; then
        PY_BIN="$(command -v "$candidate")"
        break
    elif [[ -x "$candidate" ]]; then
        PY_BIN="$candidate"
        break
    fi
done

if [[ -n "$PY_BIN" ]]; then
    echo "Usando motor Python ($PY_BIN) para empaquetado cross-platform..."

    "$PY_BIN" - "$OUTPUT_ZIP" <<'EOF'
import os
import sys
import zipfile

project_root = os.path.abspath(os.getcwd())
output_zip_arg = sys.argv[1] if len(sys.argv) > 1 else "reporte-sullivan-sttupa-loco-tequila-us.zip"

if not os.path.isabs(output_zip_arg):
    output_zip = os.path.abspath(os.path.join(project_root, output_zip_arg))
else:
    output_zip = output_zip_arg

out_dir = os.path.dirname(output_zip)
if out_dir:
    os.makedirs(out_dir, exist_ok=True)

exclude_dirs = {
    "Client_Data",
    "Client_Documents",
    ".agents",
    "Examples",
    "Output",
    ".git",
    "__pycache__"
}

exclude_exts = {
    ".twb", ".twbx", ".hyper", ".tde",
    ".pyc", ".pyo", ".pyd",
    ".zip"
}

exclude_files = {
    ".DS_Store",
    "Thumbs.db",
    os.path.basename(output_zip)
}

count = 0
total_uncompressed = 0

with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
    for root, dirs, files in os.walk(project_root):
        # Excluir directorios en el recorrido
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        rel_root = os.path.relpath(root, project_root)
        if rel_root != ".":
            parts = set(rel_root.replace("\\\\", "/").split("/"))
            if parts.intersection(exclude_dirs):
                continue

        for f in files:
            if f in exclude_files:
                continue
            ext = os.path.splitext(f)[1].lower()
            if ext in exclude_exts:
                continue

            full_path = os.path.join(root, f)
            arcname = os.path.relpath(full_path, project_root).replace("\\\\", "/")
            
            zf.write(full_path, arcname)
            count += 1
            total_uncompressed += os.path.getsize(full_path)

print(f"Archivos empaquetados: {count}")
print(f"Tamaño sin comprimir: {round(total_uncompressed / (1024*1024), 2)} MB")
EOF

elif command -v zip &>/dev/null; then
    echo "Usando utilidad nativa 'zip'..."
    zip -r -q "$FINAL_ZIP" . \
        -x "Client_Data/*" \
        -x "Client_Documents/*" \
        -x ".agents/*" \
        -x "Examples/*" \
        -x "Output/*" \
        -x "*/__pycache__/*" \
        -x "__pycache__/*" \
        -x ".git/*" \
        -x "*.twb" \
        -x "*.twbx" \
        -x "*.hyper" \
        -x "*.tde" \
        -x "*.pyc" \
        -x "*.pyo" \
        -x "*.pyd" \
        -x "*.zip" \
        -x "*.DS_Store" \
        -x "*Thumbs.db"
else
    echo "ERROR: Se requiere 'python3' o 'zip' para ejecutar este script." >&2
    exit 1
fi

if [[ ! -f "$OUTPUT_ZIP" ]]; then
    echo "ERROR: No se pudo generar el archivo ZIP: $OUTPUT_ZIP" >&2
    exit 1
fi

FINAL_BYTES=$(wc -c < "$OUTPUT_ZIP" | tr -d ' \r\n')
FINAL_MB=$(awk "BEGIN {printf \"%.2f\", $FINAL_BYTES / 1048576}")
MAX_BYTES=$((30 * 1024 * 1024))

echo "----------------------------------------------------------------------"
echo "  PAQUETE GENERADO CON ÉXITO"
echo "----------------------------------------------------------------------"
echo "Destino: $(pwd)/$OUTPUT_ZIP"
echo "Tamaño final comprimido: ${FINAL_MB} MB"

if (( FINAL_BYTES < MAX_BYTES )); then
    echo "Verificación: ${FINAL_MB} MB < 30 MB (CUMPLE CON EL LÍMITE)"
else
    echo "ADVERTENCIA: El archivo supera los 30 MB (${FINAL_MB} MB)" >&2
    exit 1
fi
echo "======================================================================"
