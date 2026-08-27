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

# Detectar binario de Python disponible. Solo nombres en PATH y rutas estándar de
# Unix: nada de rutas personales de una máquina concreta (este script tiene que
# correr igual en Linux, macOS, WSL y Git Bash).
PY_BIN=""
for candidate in python3 python py; do
    if command -v "$candidate" &>/dev/null; then
        PY_BIN="$(command -v "$candidate")"
        break
    fi
done
if [[ -z "$PY_BIN" ]]; then
    # Rutas estándar + el intérprete del ambiente conda activo (vía variable de
    # entorno, no una ruta fija): en Git Bash sobre Windows, conda suele no estar
    # en el PATH del shell aunque el ambiente esté activado.
    for candidate in \
        /usr/bin/python3 /usr/local/bin/python3 /opt/homebrew/bin/python3 \
        "${CONDA_PREFIX:-}/bin/python" "${CONDA_PREFIX:-}/python" "${CONDA_PREFIX:-}/python.exe"
    do
        if [[ -n "$candidate" && -x "$candidate" ]]; then
            PY_BIN="$candidate"
            break
        fi
    done
fi

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
            parts = set(rel_root.replace(os.sep, "/").split("/"))
            if parts.intersection(exclude_dirs):
                continue

        for f in files:
            if f in exclude_files:
                continue
            ext = os.path.splitext(f)[1].lower()
            if ext in exclude_exts:
                continue

            full_path = os.path.join(root, f)
            # El ZIP debe guardar SIEMPRE rutas con '/': si se empaqueta desde
            # Windows (Git Bash) y quedan backslashes, al extraer en Linux se crea
            # un único archivo llamado literalmente "Scripts\dashboard_generator.py"
            # y la skill no arranca. os.sep cubre ambos sistemas.
            arcname = os.path.relpath(full_path, project_root).replace(os.sep, "/")
            if "\\" in arcname:
                raise SystemExit(f"ERROR: ruta no portable en el ZIP: {arcname!r}")

            zf.write(full_path, arcname)
            count += 1
            total_uncompressed += os.path.getsize(full_path)

# Verificación de portabilidad: el paquete se consume en Linux, así que ninguna
# entrada puede llevar backslash, ser absoluta ni contener '..'.
with zipfile.ZipFile(output_zip) as check:
    entries = check.namelist()
    offenders = [n for n in entries
                 if "\\" in n or n.startswith("/") or ".." in n.split("/")]
    if offenders:
        raise SystemExit("ERROR: entradas no portables: " + ", ".join(offenders[:5]))
    lowered = {}
    for n in entries:
        lowered.setdefault(n.lower(), []).append(n)
    clashes = [v for v in lowered.values() if len(v) > 1]
    if clashes:
        raise SystemExit("ERROR: nombres que solo difieren en capitalización "
                         "(rompen en Linux): " + str(clashes[:3]))
    for n in entries:
        if n.endswith(".sh") and b"\r\n" in check.read(n):
            raise SystemExit(f"ERROR: {n} tiene CRLF; en Linux falla el shebang.")

print(f"Archivos empaquetados: {count}")
print(f"Tamaño sin comprimir: {round(total_uncompressed / (1024*1024), 2)} MB")
print(f"Portabilidad Linux verificada: {len(entries)} entradas, rutas POSIX, sin colisiones de capitalización.")
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

if [[ ! -f "$FINAL_ZIP" ]]; then
    echo "ERROR: No se pudo generar el archivo ZIP: $FINAL_ZIP" >&2
    exit 1
fi

FINAL_BYTES=$(wc -c < "$FINAL_ZIP" | tr -d ' \r\n')
FINAL_MB=$(awk "BEGIN {printf \"%.2f\", $FINAL_BYTES / 1048576}")
MAX_BYTES=$((30 * 1024 * 1024))

echo "----------------------------------------------------------------------"
echo "  PAQUETE GENERADO CON ÉXITO"
echo "----------------------------------------------------------------------"
echo "Destino: $FINAL_ZIP"
echo "Tamaño final comprimido: ${FINAL_MB} MB"

if (( FINAL_BYTES < MAX_BYTES )); then
    echo "Verificación: ${FINAL_MB} MB < 30 MB (CUMPLE CON EL LÍMITE)"
else
    echo "ADVERTENCIA: El archivo supera los 30 MB (${FINAL_MB} MB)" >&2
    exit 1
fi
echo "======================================================================"
