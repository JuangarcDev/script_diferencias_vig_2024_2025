import os
import xml.etree.ElementTree as ET

# Variables configurables
XML_PATH = r"C:\ACC\SCRIPT_13012025_COMP_MPIO_2024_2025\Script_Diferencias_Mpios_2024_2025\Manta\Insumos\Registro_catastral_25436.xml"
TXT_PATH = r"C:\ACC\SCRIPT_13012025_COMP_MPIO_2024_2025\Script_Diferencias_Mpios_2024_2025\Manta\Insumos\Numeros_Prediales_Rurales_Exc.txt"
OUTPUT_XML = r"C:\ACC\SCRIPT_13012025_COMP_MPIO_2024_2025\Script_Diferencias_Mpios_2024_2025\Manta\Insumos\Registro_catastral_modificado.xml"
REPORT_PATH = r"C:\ACC\SCRIPT_13012025_COMP_MPIO_2024_2025\Script_Diferencias_Mpios_2024_2025\Manta\Insumos"

def load_predios_to_delete(txt_path):
    """Carga los identificadores de predios desde el archivo TXT y detecta duplicados."""
    try:
        with open(txt_path, "r") as file:
            lines = [line.strip() for line in file if line.strip()]
        
        total_lines = len(lines)
        unique_predios = set(lines)
        duplicated_predios = total_lines - len(unique_predios)

        message = (
            f"Total líneas en TXT: {total_lines}\n"
            f"Total identificadores únicos: {len(unique_predios)}\n"
            f"Duplicados encontrados: {duplicated_predios}\n"
        )
        print(message)

        return unique_predios, message
    except Exception as e:
        error_msg = f"Error al cargar el archivo TXT: {e}\n"
        print(error_msg)
        return set(), error_msg

def process_xml(xml_path, predios_to_delete):
    """Procesa el XML eliminando registros según las reglas dadas y genera un reporte."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        predios = root.findall(".//predio")
        total_initial = len(predios)
        eliminados_txt = 0
        eliminados_01 = 0
        identificador_base = None
        predios_en_xml = {p.find("codigo_predial_nacional").text.strip() for p in predios}
        
        # Identificar predios presentes en TXT pero no en XML
        predios_no_en_xml = predios_to_delete - predios_en_xml
        
        for predio in predios[:]:
            codigo_predial = predio.find("codigo_predial_nacional").text.strip()
            if identificador_base is None:
                identificador_base = codigo_predial[:5]

            if codigo_predial in predios_to_delete:
                root.remove(predio)
                eliminados_txt += 1
            elif len(codigo_predial) == 30 and codigo_predial[5:7] == "01":
                root.remove(predio)
                eliminados_01 += 1

        total_remaining = len(root.findall(".//predio"))
        return tree, total_initial, eliminados_txt, eliminados_01, total_remaining, identificador_base, len(predios_to_delete), len(predios_no_en_xml), predios_to_delete, predios_en_xml

    except Exception as e:
        print(f"Error al procesar el XML: {e}")
        return None, 0, 0, 0, 0, None, 0, 0, set(), set()

def check_missing_predios(txt_predios, xml_predios):
    """Verifica cuáles números del TXT no están siendo detectados correctamente en el XML y los guarda en el informe."""
    missing = txt_predios - xml_predios
    message = ""

    if missing:
        message += "Predios en TXT que no fueron identificados en el XML:\n"
        for predio in missing:
            message += f"'{predio}'\n"
        print(message)
    else:
        message += "No hay predios faltantes, todos están identificados correctamente.\n"
        print(message)

    return message

def generate_report(report_path, total_initial, eliminados_txt, eliminados_01, total_remaining, identificador_base, total_txt, no_en_xml, txt_analysis, missing_predios):
    """Genera un archivo de reporte con el resumen de la eliminación incluyendo mensajes de consola."""
    try:
        report_name = f"Reporte_Eliminacion_Predios_{identificador_base}.txt"
        report_full_path = os.path.join(report_path, report_name)

        with open(report_full_path, "w") as report:
            report.write("### REPORTE DE ELIMINACIÓN DE PREDIOS ###\n")
            report.write(f"{txt_analysis}\n")  # Incluye análisis del TXT (líneas, únicos, duplicados)
            report.write(f"Cantidad inicial de predios en XML: {total_initial}\n")
            report.write(f"Cantidad de números prediales identificados desde el TXT: {total_txt}\n")
            report.write(f"Cantidad de números prediales presentes en el TXT pero no en el XML: {no_en_xml}\n")
            report.write(f"Cantidad de predios eliminados desde TXT: {eliminados_txt}\n")
            report.write(f"Cantidad de predios eliminados por regla '01' en posición 6-7: {eliminados_01}\n")
            report.write(f"Cantidad final de predios en XML: {total_remaining}\n\n")
            report.write(missing_predios)  # Agrega la lista de predios faltantes en el XML

        return report_full_path

    except Exception as e:
        print(f"Error al generar el reporte: {e}")
        return None

def main():
    try:
        predios_to_delete, txt_analysis = load_predios_to_delete(TXT_PATH)
        tree, total_initial, eliminados_txt, eliminados_01, total_remaining, identificador_base, total_txt, no_en_xml, txt_predios, xml_predios = process_xml(XML_PATH, predios_to_delete)

        # Verificar predios que no fueron identificados
        missing_predios = check_missing_predios(txt_predios, xml_predios)

        if tree is not None:
            # Guardar XML modificado en la ruta especificada
            tree.write(OUTPUT_XML, encoding="utf-8", xml_declaration=True)
            print(f"Archivo XML modificado guardado en: {OUTPUT_XML}")

            # Generar reporte
            report_file = generate_report(REPORT_PATH, total_initial, eliminados_txt, eliminados_01, total_remaining, identificador_base, total_txt, no_en_xml, txt_analysis, missing_predios)
            if report_file:
                print(f"Proceso completado. Reporte generado en: {report_file}")
        else:
            print("No se pudo generar el XML modificado debido a un error en el procesamiento.")

    except Exception as e:
        print(f"Error general en la ejecución: {e}")

if __name__ == "__main__":
    main()