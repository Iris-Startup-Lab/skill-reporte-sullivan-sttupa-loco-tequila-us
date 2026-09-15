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
import re
import sys
from pathlib import Path

# Forzar UTF-8 en stdout/stderr ANTES de cualquier otro import: en consolas
# Windows legacy (cp1252) los caracteres no-ASCII (—, ó, á, ñ) se corrompen, y
# los generadores pueden emitir avisos durante su propia importación.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass

# Los generadores se importan de forma DIFERIDA dentro de run_sullivan(): así un
# fallo en el motor de dashboard (p. ej. una dependencia gráfica ausente) no
# tumba el CLI cuando solo se pidió --format pdf, y al revés.

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
        # Raíz de semanas, NO una semana concreta: antes esto apuntaba a
        # `Week_2026_08_23` y por eso, aunque el cliente dejara diez semanas
        # en la carpeta, el reporte solo veía esa. `discover_week_dirs` acepta
        # que la ruta sea una semana o que las contenga.
        "weekly_client_dir": PROJECT_ROOT / "Client_Data" / "Sullivan_data" / "Weekly",
        "weekly_demo_dir": PROJECT_ROOT / "Data_for_demo" / "Sullivan_weekly_demo",
    },
    "loco_tequila": {
        "name": "Loco Tequila USA",
        "status": "active",
        "design_file": PROJECT_ROOT / "Designs" / "Design_loco_tequila.md",
        "data_dir": PROJECT_ROOT / "Client_Data" / "Loco_tequila_usa_data",
        "demo_data_dir": PROJECT_ROOT / "Data_for_demo" / "Loco_tequila_demo",
    },
    "sttupa": {
        "name": "Sttupa",
        "status": "coming_soon",
        "design_file": PROJECT_ROOT / "Designs" / "Design_sttupa.md",
    },
}


def resolve_data_dir(explicit: str | None, client_dir: Path, demo_dir: Path,
                     label: str) -> Path:
    """
    Elige la carpeta de datos con una precedencia explícita: lo que pidió el
    usuario > los datos del cliente > los datos demo.

    Existe porque `Client_Data/` se excluye del paquete a propósito (son datos
    del cliente y no se distribuyen), así que una instalación limpia no la
    tiene. Antes eso hacía que el flujo semanal y el de Loco fallaran de
    entrada; ahora caen al demo y el reporte dice de dónde salieron los datos.
    """
    if explicit:
        chosen = Path(explicit)
        if not chosen.exists():
            print(f"[ERROR] No se encontró la carpeta indicada para {label}: {chosen}")
            sys.exit(1)
        return chosen
    if client_dir.exists():
        return client_dir
    if demo_dir.exists():
        print(f"[AVISO] No hay datos de cliente para {label} en {client_dir}.")
        print(f"        Se usan los datos DEMO de {demo_dir}.")
        print(f"        Para tus propios datos: --data-dir \"Ruta/A/Mis_Datos\".")
        return demo_dir
    print(f"[ERROR] No hay datos para {label}: no existe ni {client_dir} ni {demo_dir}.")
    print("        Genera los demo con: python Scripts/make_demo_data.py")
    sys.exit(1)


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
                 period_label: str, output_dir: Path, output_format: str,
                 lang: str = "en"):
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9_]+", "_", period_label.lower().strip()).strip("_") or "report"

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
            from dashboard_generator import generate as generate_dashboard
            generate_dashboard(
                order_sales_path=str(order_sales_path),
                financial_report_path=str(financial_report_path) if financial_report_path else None,
                output_path=str(dashboard_out),
                title=f"Sullivan Rutherford Estate — {period_label}",
                period_label=period_label,
                lang=lang,
            )
            generated_files.append(("Dashboard HTML", dashboard_out))
        except Exception as e:
            print(f"  [ERROR] Falló la generación del Dashboard: {e}")
            raise

    # 2. Reporte PDF
    if output_format in ("all", "pdf"):
        print("  -> Generando Reporte Ejecutivo en PDF...")
        try:
            from pdf_generator import build_pdf as generate_pdf
            generate_pdf(
                order_sales_path=str(order_sales_path),
                financial_report_path=str(financial_report_path) if financial_report_path else None,
                output_path=str(pdf_out),
                period_label=period_label,
                lang=lang,
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


def run_sullivan_weekly(weekly_data_dir: Path, output_dir: Path,
                        output_format: str, tock_basis: str = "net_receivable",
                        lang: str = "en"):
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 70)
    print("  INICIANDO GENERACIÓN DE REPORTE SEMANAL — SULLIVAN RUTHERFORD ESTATE")
    print("=" * 70)
    print(f"  Cadencia:         Semanal (DTC + Distribución + Depletions)")
    print(f"  Directorio Datos: {weekly_data_dir}")
    print(f"  Base Tock:        {tock_basis}")
    print(f"  Directorio Salida:{output_dir}")

    # Se procesan TODAS las semanas que haya bajo la carpeta indicada. El
    # nombre del archivo sale del periodo real de la más reciente, no de una
    # constante, así que dos cortes distintos ya no se sobreescriben.
    from sullivan_weekly_processor import (process_sullivan_weekly_series,
                                          weekly_output_name)
    weekly_series = process_sullivan_weekly_series(weekly_data_dir, tock_basis=tock_basis)
    weekly_data = weekly_series[-1]
    dashboard_out = output_dir / weekly_output_name(weekly_data)
    print(f"  Semanas detectadas: {len(weekly_series)}"
          + (f"  ({weekly_series[0]['date_closing']} .. {weekly_series[-1]['date_closing']})"
             if len(weekly_series) > 1 else ""))
    print(f"  Periodo detectado:{weekly_data['period_label']}")
    if len(weekly_series) > 1:
        print("  El HTML embebe las " + str(len(weekly_series))
              + " semanas: el selector cambia el tablero completo.")
    print("-" * 70)

    generated_files = []

    if output_format in ("all", "html", "dashboard"):
        print("  -> Generando Dashboard Semanal HTML interactivo...")
        try:
            from dashboard_weekly_sullivan import generate_sullivan_weekly_dashboard
            generate_sullivan_weekly_dashboard(
                data_dir=weekly_data_dir,
                output_file=dashboard_out,
                tock_basis=tock_basis,
                weeks=weekly_series,
                lang=lang,
            )
            generated_files.append(("Dashboard Semanal HTML", dashboard_out))
        except Exception as e:
            print(f"  [ERROR] Falló la generación del Dashboard Semanal: {e}")
            raise

    if output_format in ("all", "pdf"):
        print("  -> Generando Reporte Semanal en PDF...")
        try:
            from pdf_weekly_sullivan import build_weekly_pdf
            pdf_out = output_dir / weekly_output_name(
                weekly_data, prefix="sullivan_weekly_report", suffix=".pdf")
            build_weekly_pdf(weekly_data_dir, pdf_out, tock_basis=tock_basis,
                             weeks=weekly_series, lang=lang)
            generated_files.append(("Reporte Semanal PDF", pdf_out))
        except Exception as e:
            print(f"  [ERROR] Falló la generación del PDF Semanal: {e}")
            raise

    print("-" * 70)
    print("  RESULTADO: Generación semanal completada con éxito.")
    for label, path in generated_files:
        print(f"    * {label}: {path}")
    print("=" * 70 + "\n")


def run_sullivan_unified(order_sales_path: Path, financial_report_path: Path | None,
                         weekly_data_dir: Path | None, period_label: str,
                         output_dir: Path, output_format: str = "all",
                         tock_basis: str = "net_receivable",
                         lang: str = "en"):
    """
    Las dos cadencias en un solo entregable: lo que ambos reportes decían igual
    aparece una vez, y lo exclusivo de cada uno se conserva (el mapa Albers del
    mensual, las cuentas por cobrar y depletions del semanal).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9_]+", "_", period_label.lower().strip()).strip("_") or "report"
    out = output_dir / f"sullivan_dashboard_unified_{slug}.html"

    print("\n" + "=" * 70)
    print("  INICIANDO GENERACIÓN DE REPORTE UNIFICADO — SULLIVAN RUTHERFORD ESTATE")
    print("=" * 70)
    print(f"  Cadencia:         Unificada (mensual + semanal en un solo entregable)")
    print(f"  Periodo mensual:  {period_label}")
    print(f"  Datos de Ventas:  {order_sales_path}")
    print(f"  Reporte Finanzas: {financial_report_path if financial_report_path else 'No provisto'}")
    print(f"  Datos semanales:  {weekly_data_dir if weekly_data_dir else 'No provistos'}")
    print(f"  Directorio Salida:{output_dir}")
    print("-" * 70)

    generated_files = []

    if output_format in ("all", "html", "dashboard"):
        print("  -> Generando Dashboard Unificado HTML interactivo...")
        try:
            from dashboard_sullivan_unified import generate_unified_dashboard
            generate_unified_dashboard(
                order_sales_path=order_sales_path,
                financial_report_path=financial_report_path,
                weekly_data_dir=weekly_data_dir,
                output_path=out,
                period_label=period_label,
                tock_basis=tock_basis,
                lang=lang,
            )
            generated_files.append(("Dashboard Unificado HTML", out))
        except Exception as e:
            print(f"  [ERROR] Falló la generación del Dashboard Unificado: {e}")
            raise

    if output_format in ("all", "pdf"):
        print("  -> Generando Reporte Unificado en PDF...")
        try:
            from pdf_sullivan_unified import build_unified_pdf
            pdf_out = output_dir / f"sullivan_report_unified_{slug}.pdf"
            build_unified_pdf(order_sales_path, financial_report_path,
                              weekly_data_dir, pdf_out, period_label, tock_basis,
                              lang=lang)
            generated_files.append(("Reporte Unificado PDF", pdf_out))
        except Exception as e:
            print(f"  [ERROR] Falló la generación del PDF Unificado: {e}")
            raise

    print("-" * 70)
    print("  RESULTADO: Generación unificada completada con éxito.")
    for label, path in generated_files:
        print(f"    * {label}: {path}")
    print("=" * 70 + "\n")


def run_loco_tequila(output_dir: Path, data_dir: Path | None = None,
                     account_map: str | None = None,
                     output_format: str = "all",
                     lang: str = "en"):
    """
    Genera el dashboard directivo de Loco Tequila USA a partir de datos REALES.
    Antes esta función producía un HTML con todas las cifras incrustadas a mano;
    ahora lee la carpeta de datos del cliente (o la que el usuario indique).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    info = BRANDS["loco_tequila"]
    data_dir = resolve_data_dir(str(data_dir) if data_dir else None,
                                info["data_dir"], info["demo_data_dir"],
                                "Loco Tequila USA")
    dashboard_out = output_dir / "loco_tequila_usa_dashboard.html"

    print("\n" + "=" * 70)
    print("  INICIANDO GENERACIÓN DE REPORTE — LOCO TEQUILA USA")
    print("=" * 70)
    print("  Marca:            Loco Tequila USA")
    print(f"  Directorio Datos: {data_dir}")
    print(f"  Mapa de cuentas:  {account_map if account_map else 'No provisto (heurística)'}")
    print(f"  Directorio Salida:{output_dir}")
    print("-" * 70)

    generated_files = []

    # Los 7 insumos crudos se procesan UNA vez y se comparten entre los dos
    # entregables: leerlos dos veces no aporta nada y duplica el tiempo.
    try:
        from loco_data_processor import process_loco_data
        print("  -> Procesando los insumos crudos...")
        loco_data = process_loco_data(data_dir, account_map)
    except Exception as e:
        print(f"  [ERROR] Falló el procesamiento de los datos de Loco Tequila: {e}")
        raise

    if output_format in ("all", "html", "dashboard"):
        print("  -> Generando Dashboard HTML...")
        try:
            from loco_dashboard_generator import generate_loco_tequila_dashboard
            generate_loco_tequila_dashboard(dashboard_out, data_dir, account_map,
                                            data=loco_data, lang=lang)
            generated_files.append(("Dashboard HTML", dashboard_out))
        except Exception as e:
            print(f"  [ERROR] Falló la generación del Dashboard de Loco Tequila: {e}")
            raise

    if output_format in ("all", "pdf"):
        print("  -> Generando Reporte Ejecutivo en PDF...")
        try:
            from pdf_loco_tequila import build_loco_pdf
            pdf_out = output_dir / "loco_tequila_usa_report.pdf"
            build_loco_pdf(pdf_out, data_dir, account_map, data=loco_data,
                           lang=lang)
            generated_files.append(("Reporte PDF", pdf_out))
        except Exception as e:
            print(f"  [ERROR] Falló la generación del PDF de Loco Tequila: {e}")
            raise

    if output_format in ("all", "xlsx"):
        print("  -> Generando Libro de Excel de referencia (segunda validación)...")
        try:
            from loco_excel_reference import generate_loco_excel_reference
            xlsx_out = output_dir / "loco_tequila_usa_reference.xlsx"
            generate_loco_excel_reference(xlsx_out, data_dir, account_map)
            generated_files.append(("Libro de referencia (Excel)", xlsx_out))
        except Exception as e:
            print(f"  [ERROR] Falló la generación del libro de Excel de Loco Tequila: {e}")
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
    print("    2) Loco Tequila USA           [ACTIVO]")
    print("    3) Sttupa                     [PRÓXIMAMENTE]")
    print("=" * 70)

    choice = input("  Ingrese opción (1-3): ").strip()

    if choice == "2":
        raw_dir = input("  Carpeta con tus datos (Enter para usar los del repo o el demo): ").strip().strip('"')
        raw_map = input("  CSV cuenta → vendedor → canal (Enter para omitir): ").strip().strip('"')
        raw_out = input("  Directorio de salida (Enter para 'Output'): ").strip().strip('"')
        run_loco_tequila(
            output_dir=Path(raw_out) if raw_out else PROJECT_ROOT / "Output",
            data_dir=Path(raw_dir) if raw_dir else None,
            account_map=raw_map or None,
        )
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
        "--data-dir",
        help="Carpeta con los datos crudos de la marca (usado por Loco Tequila USA). "
             "Permite que el usuario procese sus propios archivos en vez de los del repo."
    )
    parser.add_argument(
        "--account-map",
        help="CSV opcional cuenta → vendedor → canal comercial (Loco Tequila USA). "
             "Sin él, vendedor y canal se estiman por heurística."
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
        choices=["all", "html", "dashboard", "pdf", "xlsx"],
        default="all",
        help="Formato a generar: 'all' (HTML + PDF, y para Loco Tequila también "
             "el libro de Excel de referencia), 'html' (alias: 'dashboard'), "
             "'pdf' o 'xlsx' (libro de referencia con gráficas y tablas cruzadas "
             "ligadas por fórmula al dataset — por ahora solo Loco Tequila)."
    )
    parser.add_argument(
        "--cadence",
        choices=["monthly", "weekly", "unified"],
        default="monthly",
        help="Cadencia del reporte: 'monthly' (mensual DTC reconciliado), "
             "'weekly' (semanal DTC + Distribución) o 'unified' (las dos en un "
             "solo HTML, sin repetir los bloques comunes)."
    )
    parser.add_argument(
        "--weekly-data-dir",
        default=None,
        help="Directorio de datos semanales de Sullivan. Sin él se usan los datos "
             "del cliente si existen, y si no, los demo de Data_for_demo/."
    )
    parser.add_argument(
        "--tock-basis",
        choices=["net_receivable", "net_sales"],
        default="net_receivable",
        help="Base de cálculo de Tock en el reporte semanal: 'net_receivable' "
             "(lo efectivamente cobrable, recomendado) o 'net_sales' (venta neta "
             "antes de comisiones y cortesías)."
    )
    parser.add_argument(
        "--lang",
        choices=["en", "es"],
        default="en",
        help="Idioma de los entregables. Fija el idioma del PDF y con cuál "
             "ABRE el dashboard HTML; el HTML lleva los dos idiomas y un "
             "selector ES/EN, así que un solo archivo sirve a los dos "
             "públicos. La taxonomía (Tasting Room, Founder's Club, SKU, "
             "distribuidores) se queda en inglés en ambos idiomas para que "
             "siga cuadrando contra Commerce7 y Park Street."
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

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir

    if brand == "loco_tequila":
        run_loco_tequila(output_dir, args.data_dir, args.account_map, args.format,
                         lang=args.lang)
        return

    if brand == "sttupa":
        print_coming_soon(brand)
        return

    # Flujo para Sullivan
    if args.cadence == "weekly":
        weekly_dir = resolve_data_dir(
            args.weekly_data_dir or args.data_dir,
            BRANDS["sullivan"]["weekly_client_dir"],
            BRANDS["sullivan"]["weekly_demo_dir"],
            "Sullivan semanal",
        )
        run_sullivan_weekly(
            weekly_data_dir=weekly_dir,
            output_dir=output_dir,
            output_format=args.format,
            tock_basis=args.tock_basis,
            lang=args.lang,
        )
        return

    # Flujos que necesitan los archivos mensuales (mensual y unificado)
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

    if args.cadence == "unified":
        # La parte semanal es opcional: si no hay datos, el reporte sale completo
        # en su parte mensual y lo declara, en vez de mostrar ceros.
        weekly_dir = None
        explicit_weekly = args.weekly_data_dir or args.data_dir
        if explicit_weekly:
            weekly_dir = Path(explicit_weekly)
            if not weekly_dir.exists():
                print(f"[ERROR] No se encontró la carpeta semanal indicada: {weekly_dir}")
                sys.exit(1)
        else:
            for candidate in (sullivan_info["weekly_client_dir"],
                              sullivan_info["weekly_demo_dir"]):
                if candidate.exists():
                    weekly_dir = candidate
                    break
            if weekly_dir is None:
                print("[AVISO] Sin datos semanales: el reporte unificado sale solo "
                      "con la cadencia mensual.")
        run_sullivan_unified(
            order_sales_path=order_sales_path,
            financial_report_path=financial_report_path,
            weekly_data_dir=weekly_dir,
            period_label=args.period_label,
            output_dir=output_dir,
            output_format=args.format,
            tock_basis=args.tock_basis,
            lang=args.lang,
        )
        return

    run_sullivan(
        order_sales_path=order_sales_path,
        financial_report_path=financial_report_path,
        period_label=args.period_label,
        output_dir=output_dir,
        output_format=args.format,
        lang=args.lang,
    )


if __name__ == "__main__":
    main()
