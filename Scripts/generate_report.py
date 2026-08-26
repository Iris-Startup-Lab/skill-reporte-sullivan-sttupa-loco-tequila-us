"""
================================================================================
 SISTEMA TRIPARTITO DE REPORTES EJECUTIVOS — ORQUESTADOR MULTIMARCA
================================================================================
Permite generar reportes ejecutivos (Dashboard HTML y Reporte PDF) de forma
agnóstica para las 3 marcas del ecosistema:
    1. Sullivan Rutherford Estate (Activo / Listo para producción)
    2. Loco Tequila USA (Próximamente)
    3. Sttupa (Próximamente)

Soporta ejecución vía argumentos CLI o modo interactivo por consola.
Acepta fuentes de datos en formato Excel (.xlsx/.xls) y CSV (.csv).
================================================================================
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Importar generadores locales
from dashboard_generator import generate as generate_dashboard
from pdf_generator import build_pdf as generate_pdf

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BRANDS = {
    "sullivan": {
        "name": "Sullivan Rutherford Estate",
        "status": "active",
        "demo_order_sales": PROJECT_ROOT / "Data_for_demo" / "Sullivan_data_demo" / "Apr_OrderSales.xlsx",
        "demo_financial_report": PROJECT_ROOT / "Data_for_demo" / "Sullivan_data_demo" / "Apr_FinancialReport.xlsx",
        "fallback_order_sales": PROJECT_ROOT / "Client_Data" / "Sullivan_data" / "Apr_OrderSales.xlsx",
        "fallback_financial_report": PROJECT_ROOT / "Client_Data" / "Sullivan_data" / "Apr_FinancialReport.xlsx",
        "design_file": PROJECT_ROOT / "Designs" / "Design_sullivan.md",
        "default_period": "April 2026",
    },
    "loco_tequila": {
        "name": "Loco Tequila USA",
        "status": "coming_soon",
        "design_file": PROJECT_ROOT / "Designs" / "Design_loco_tequila.md",
    },
    "sttupa": {
        "name": "Sttupa",
        "status": "coming_soon",
        "design_file": PROJECT_ROOT / "Designs" / "Design_sttupa.md",
    },
}


def print_coming_soon(brand_key: str):
    brand_info = BRANDS.get(brand_key, {"name": brand_key})
    print("\n" + "=" * 70)
    print(f"  MARCA SELECCIONADA: {brand_info['name']}")
    print("=" * 70)
    print("  ESTADO: [ Próximamente ]")
    print()
    print(f"  La generación automatizada de reportes para {brand_info['name']}")
    print("  se encuentra actualmente en desarrollo y estará disponible muy pronto.")
    print()
    print("  Recursos preparados para esta marca:")
    if "design_file" in brand_info and brand_info["design_file"].exists():
        print(f"    - Especificación de diseño: {brand_info['design_file'].relative_to(PROJECT_ROOT)}")
    print("    - Logotipos e isotipos: Imagenes_iconos/")
    print("    - Fuentes tipográficas oficiales: Fonts/")
    print("=" * 70 + "\n")


def run_sullivan(order_sales_path: Path, financial_report_path: Path | None,
                 period_label: str, output_dir: Path, output_format: str):
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = period_label.lower().replace(" ", "_").replace("-", "_")

    dashboard_out = output_dir / f"sullivan_dashboard_{slug}.html"
    pdf_out = output_dir / f"sullivan_report_{slug}.pdf"

    print("\n" + "=" * 70)
    print(f"  INICIANDO GENERACIÓN DE REPORTES — SULLIVAN RUTHERFORD ESTATE")
    print("=" * 70)
    print(f"  Periodo:          {period_label}")
    print(f"  Datos de Ventas:  {order_sales_path}")
    print(f"  Reporte Finanzas: {financial_report_path if financial_report_path else 'No provisto'}")
    print(f"  Directorio Salida:{output_dir}")
    print("-" * 70)

    generated_files = []

    # 1. Dashboard HTML
    if output_format in ("all", "html", "dashboard"):
        print("  -> Generando Dashboard HTML interactivo...")
        try:
            generate_dashboard(
                order_sales_path=str(order_sales_path),
                financial_report_path=str(financial_report_path) if financial_report_path else None,
                output_path=str(dashboard_out),
                title=f"Sullivan Rutherford Estate — {period_label}",
                period_label=period_label
            )
            generated_files.append(("Dashboard HTML", dashboard_out))
        except Exception as e:
            print(f"  [ERROR] Falló la generación del Dashboard: {e}")
            raise

    # 2. Reporte PDF
    if output_format in ("all", "pdf"):
        print("  -> Generando Reporte Ejecutivo en PDF...")
        try:
            generate_pdf(
                order_sales_path=str(order_sales_path),
                financial_report_path=str(financial_report_path) if financial_report_path else None,
                output_path=str(pdf_out),
                period_label=period_label
            )
            generated_files.append(("Reporte PDF", pdf_out))
        except Exception as e:
            print(f"  [ERROR] Falló la generación del PDF: {e}")
            raise

    print("-" * 70)
    print("  RESULTADO: Generación completada con éxito.")
    for label, path in generated_files:
        print(f"    * {label}: {path}")
    print("=" * 70 + "\n")


def interactive_menu():
    print("\n" + "=" * 70)
    print("  SISTEMA TRIPARTITO DE REPORTES EJECUTIVOS — SELECCIÓN DE MARCA")
    print("=" * 70)
    print("  Por favor seleccione la marca para la que desea generar reportes:")
    print("    1) Sullivan Rutherford Estate [ACTIVO]")
    print("    2) Loco Tequila USA           [PRÓXIMAMENTE]")
    print("    3) Sttupa                     [PRÓXIMAMENTE]")
    print("=" * 70)

    choice = input("  Ingrese opción (1-3): ").strip()

    if choice == "2":
        print_coming_soon("loco_tequila")
        return
    elif choice == "3":
        print_coming_soon("sttupa")
        return
    elif choice != "1":
        print("\n  Opción no válida. Saliendo.")
        return

    # Marca Sullivan seleccionada
    sullivan_info = BRANDS["sullivan"]
    print("\n" + "-" * 70)
    print("  FUENTE DE DATOS PARA SULLIVAN")
    print("-" * 70)
    print("  Seleccione el origen de los datos:")
    print("    1) Usar datos Demo preconfigurados (Data_for_demo/Sullivan_data_demo)")
    print("    2) Proporcionar archivo de datos propio (.xlsx o .csv)")
    print("-" * 70)

    data_choice = input("  Ingrese opción (1-2): ").strip()

    if data_choice == "1":
        order_sales = sullivan_info["demo_order_sales"]
        if not order_sales.exists():
            order_sales = sullivan_info["fallback_order_sales"]
        financial = sullivan_info["demo_financial_report"]
        if not financial.exists():
            financial = sullivan_info["fallback_financial_report"]
        period = sullivan_info["default_period"]
    elif data_choice == "2":
        raw_order = input("  Ruta del archivo de ventas (.xlsx o .csv): ").strip().strip('"')
        order_sales = Path(raw_order)
        if not order_sales.exists():
            print(f"  [ERROR] El archivo '{order_sales}' no existe.")
            return

        raw_fin = input("  Ruta del reporte financiero (.xlsx o .csv, Enter para omitir): ").strip().strip('"')
        financial = Path(raw_fin) if raw_fin else None
        if financial and not financial.exists():
            print(f"  [AVISO] El archivo financiero '{financial}' no existe; se omitirá la reconciliación.")
            financial = None

        period = input("  Etiqueta del periodo (ej. 'April 2026', 'Week 30 2026'): ").strip()
        if not period:
            period = sullivan_info["default_period"]
    else:
        print("\n  Opción no válida. Saliendo.")
        return

    raw_out = input("  Directorio de salida (Enter para 'Output'): ").strip().strip('"')
    output_dir = Path(raw_out) if raw_out else PROJECT_ROOT / "Output"

    run_sullivan(
        order_sales_path=order_sales,
        financial_report_path=financial,
        period_label=period,
        output_dir=output_dir,
        output_format="all"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generador agnóstico y orquestador de reportes ejecutivos para marcas."
    )
    parser.add_argument(
        "--brand",
        choices=["sullivan", "loco_tequila", "sttupa"],
        help="Marca para la cual generar el reporte."
    )
    parser.add_argument(
        "--data-source",
        choices=["demo", "custom"],
        default="demo",
        help="Origen de datos ('demo' para datos predeterminados, 'custom' para archivos propios)."
    )
    parser.add_argument(
        "--order-sales",
        help="Ruta al archivo transaccional de ventas (.xlsx o .csv)."
    )
    parser.add_argument(
        "--financial-report",
        help="Ruta al archivo de reconciliación financiera (.xlsx o .csv)."
    )
    parser.add_argument(
        "--period-label",
        default="April 2026",
        help="Etiqueta del periodo analizado (ej. 'April 2026', 'Week 30 2026')."
    )
    parser.add_argument(
        "--output-dir",
        default="Output",
        help="Directorio donde guardar los reportes generados."
    )
    parser.add_argument(
        "--format",
        choices=["all", "html", "pdf"],
        default="all",
        help="Formato de reporte a generar: 'all' (HTML + PDF), 'html' o 'pdf'."
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Iniciar menú interactivo en consola."
    )

    args = parser.parse_args()

    # Si no se pasó marca ni modo interactivo y no hay argumentos suficientes, abrir menú interactivo
    if args.interactive or (not args.brand and len(sys.argv) == 1):
        interactive_menu()
        return

    brand = args.brand.lower() if args.brand else "sullivan"

    if brand in ("loco_tequila", "sttupa"):
        print_coming_soon(brand)
        return

    # Flujo para Sullivan
    sullivan_info = BRANDS["sullivan"]

    if args.order_sales:
        order_sales_path = Path(args.order_sales)
    elif args.data_source == "demo":
        order_sales_path = sullivan_info["demo_order_sales"]
        if not order_sales_path.exists():
            order_sales_path = sullivan_info["fallback_order_sales"]
    else:
        print("[ERROR] Debe proporcionar --order-sales al usar --data-source custom.")
        sys.exit(1)

    if not order_sales_path.exists():
        print(f"[ERROR] No se encontró el archivo de ventas: {order_sales_path}")
        sys.exit(1)

    if args.financial_report:
        financial_report_path = Path(args.financial_report)
        if not financial_report_path.exists():
            print(f"[AVISO] No se encontró {financial_report_path}, omitiendo reconciliación.")
            financial_report_path = None
    elif args.data_source == "demo":
        financial_report_path = sullivan_info["demo_financial_report"]
        if not financial_report_path.exists():
            financial_report_path = sullivan_info["fallback_financial_report"]
    else:
        financial_report_path = None

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir

    run_sullivan(
        order_sales_path=order_sales_path,
        financial_report_path=financial_report_path,
        period_label=args.period_label,
        output_dir=output_dir,
        output_format=args.format
    )


if __name__ == "__main__":
    main()
