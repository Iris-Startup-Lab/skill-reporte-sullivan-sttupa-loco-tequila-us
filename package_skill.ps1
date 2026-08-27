<#
.SYNOPSIS
    Empaqueta la skill 'reporte-sullivan-sttupa-loco-tequila-us' para distribución multiplataforma.

.DESCRIPTION
    Genera un archivo ZIP limpio y portable con todo lo necesario para ejecutar la skill
    en Windows, macOS o Linux.
    Excluye estrictamente datos confidenciales del cliente, carpetas temporales,
    archivos de Tableau y caches de Python. Garantiza un tamaño menor a 30 MB.

.PARAMETER OutputZip
    Nombre o ruta del archivo ZIP generado (por defecto: reporte-sullivan-sttupa-loco-tequila-us.zip).

.EXAMPLE
    .\package_skill.ps1
    .\package_skill.ps1 -OutputZip "dist/mi_skill.zip"
#>

[CmdletBinding()]
param(
    [string]$OutputZip = "reporte-sullivan-sttupa-loco-tequila-us.zip"
)

$ErrorActionPreference = "Stop"

# Directorio raíz del proyecto
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) { $ProjectRoot = (Get-Location).Path }

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  EMPAQUETADOR DE SKILL — DISTRIBUCIÓN MULTIPLATAFORMA" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Directorio base: $ProjectRoot"

# Resolver ruta absoluta de salida
if (-not [System.IO.Path]::IsPathRooted($OutputZip)) {
    $OutputZipPath = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($ProjectRoot, $OutputZip))
} else {
    $OutputZipPath = [System.IO.Path]::GetFullPath($OutputZip)
}

$OutputDir = [System.IO.Path]::GetDirectoryName($OutputZipPath)
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# Carpetas excluidas obligatorias
$ExcludeDirs = @(
    "Client_Data",
    "Client_Documents",
    ".agents",
    "Examples",
    "Output",
    ".git",
    "__pycache__"
)

# Extensiones excluidas (Tableau, binarios compilados, temporales)
$ExcludeExts = @(
    ".twb", ".twbx", ".hyper", ".tde",
    ".pyc", ".pyo", ".pyd",
    ".zip"
)

# Nombres de archivo excluidos
$ExcludeFileNames = @(
    ".DS_Store",
    "Thumbs.db",
    [System.IO.Path]::GetFileName($OutputZipPath)
)

Write-Host "Filtrando archivos según reglas de exclusión..." -ForegroundColor Yellow
$AllFiles = Get-ChildItem -Path $ProjectRoot -Recurse -File

$IncludedFiles = @()
foreach ($file in $AllFiles) {
    $relPath = $file.FullName.Substring($ProjectRoot.Length).TrimStart('\', '/')
    $parts = $relPath.Split([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    
    # 1. Verificar carpetas excluidas
    $isDirExcluded = $false
    foreach ($dir in $ExcludeDirs) {
        if ($parts -contains $dir) {
            $isDirExcluded = $true
            break
        }
    }
    if ($isDirExcluded) { continue }

    # 2. Verificar extensiones excluidas (Tableau, python cache, zips)
    if ($ExcludeExts -contains $file.Extension.ToLower()) { continue }

    # 3. Verificar nombres de archivos excluidos
    if ($ExcludeFileNames -contains $file.Name) { continue }

    $IncludedFiles += [PSCustomObject]@{
        FullName     = $file.FullName
        RelativePath = $relPath.Replace('\', '/')  # Normalizado a '/' para portabilidad Unix
        Length       = $file.Length
    }
}

Write-Host "Archivos calificados para empaquetado: $($IncludedFiles.Count)" -ForegroundColor Green
$UncompressedBytes = ($IncludedFiles | Measure-Object -Property Length -Sum).Sum
$UncompressedMB = [math]::Round($UncompressedBytes / 1MB, 2)
Write-Host "Tamaño total sin comprimir: $UncompressedMB MB"

# Eliminar archivo ZIP previo si existe
if (Test-Path $OutputZipPath) {
    Remove-Item -Path $OutputZipPath -Force
}

# Crear archivo ZIP usando System.IO.Compression para compatibilidad total de rutas Unix
Write-Host "Generando archivo ZIP comprimido..." -ForegroundColor Yellow
# En Windows PowerShell 5.1 hay que cargar AMBOS ensamblados:
#   - System.IO.Compression         -> ZipArchiveMode, CompressionLevel, ZipArchive
#   - System.IO.Compression.FileSystem -> ZipFile, ZipFileExtensions
# Cargar solo el segundo provoca "No se encuentra el tipo [System.IO.Compression.ZipArchiveMode]".
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$zip = [System.IO.Compression.ZipFile]::Open($OutputZipPath, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($item in $IncludedFiles) {
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $zip,
            $item.FullName,
            $item.RelativePath,
            [System.IO.Compression.CompressionLevel]::Optimal
        ) | Out-Null
    }
}
finally {
    $zip.Dispose()
}

# --------------------------------------------------------------------------
# Verificación de portabilidad a Linux. El paquete se consume en ambientes
# Linux (Claude ejecuta las skills ahí), donde:
#   - una entrada con '\' se extrae como UN archivo llamado "Scripts\x.py",
#   - el sistema es case-sensitive, así que dos nombres que solo difieren en
#     mayúsculas colisionan,
#   - un .sh con CRLF falla con "bad interpreter: ...^M".
# Mejor reventar aquí que entregar un ZIP que no arranca.
# --------------------------------------------------------------------------
Write-Host "Verificando portabilidad a Linux..." -ForegroundColor Yellow
$verify = [System.IO.Compression.ZipFile]::OpenRead($OutputZipPath)
try {
    $entries = $verify.Entries | ForEach-Object { $_.FullName }

    $badPaths = $entries | Where-Object {
        $_ -like '*\*' -or $_.StartsWith('/') -or ($_ -split '/') -contains '..'
    }
    if ($badPaths) {
        throw "Entradas con rutas no portables: $($badPaths -join ', ')"
    }

    $clashes = $entries | Group-Object { $_.ToLowerInvariant() } | Where-Object { $_.Count -gt 1 }
    if ($clashes) {
        throw "Nombres que solo difieren en capitalización (rompen en Linux): $(($clashes | ForEach-Object { $_.Group -join ' vs ' }) -join '; ')"
    }

    foreach ($entry in $verify.Entries) {
        if ($entry.FullName -like '*.sh') {
            $reader = New-Object System.IO.StreamReader($entry.Open())
            try { $text = $reader.ReadToEnd() } finally { $reader.Dispose() }
            if ($text.Contains("`r`n")) {
                throw "$($entry.FullName) tiene CRLF; en Linux falla el shebang."
            }
        }
    }

    Write-Host "  OK: $($entries.Count) entradas con rutas POSIX, sin colisiones de capitalización, .sh con LF." -ForegroundColor Green
}
finally {
    $verify.Dispose()
}

$FinalSizeBytes = (Get-Item $OutputZipPath).Length
$FinalSizeMB = [math]::Round($FinalSizeBytes / 1MB, 2)

Write-Host "----------------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "  PAQUETE GENERADO CON ÉXITO" -ForegroundColor Green
Write-Host "----------------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Destino: $OutputZipPath" -ForegroundColor White
Write-Host "Archivos incluidos: $($IncludedFiles.Count)" -ForegroundColor White
Write-Host "Tamaño final comprimido: $FinalSizeMB MB" -ForegroundColor White

if ($FinalSizeBytes -lt (30 * 1024 * 1024)) {
    Write-Host "Cumple con el límite: $FinalSizeMB MB < 30 MB (OK)" -ForegroundColor Green
} else {
    Write-Host "ADVERTENCIA: El archivo supera los 30 MB ($FinalSizeMB MB)" -ForegroundColor Red
    exit 1
}
Write-Host "======================================================================" -ForegroundColor Cyan
