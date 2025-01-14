# -*- coding: utf-8 -*-
"""
Script para comparar archivos XML de registros catastrales entre dos vigencias.

Propósito:
- Identificar registros que cumplen ciertas condiciones en archivos XML organizados por municipios.
- Comparar los datos entre dos carpetas (vigencia 2024 y 2025).
- Generar reportes detallados con resultados de las consultas, conteos y diferencias.

Inputs:
1. Ruta de la carpeta de archivos XML para vigencia 2024.
2. Ruta de la carpeta de archivos XML para vigencia 2025.
3. Condiciones de consulta (definidas en el script o como entrada).

Outputs:
1. Archivos de reporte en formato .txt con:
   - Descripción de la validación realizada.
   - Año de la vigencia y código del municipio evaluado.
   - Cantidad de registros que cumplen la condición.
   - Lista de números prediales únicos.
   - Diferencias entre vigencias.

Estructura del script:
1. Validación de las carpetas y archivos XML.
2. Ejecución de consultas específicas en los datos XML.
3. Comparación de resultados entre vigencias.
4. Generación de reportes.
"""

import os
import re
import xml.etree.ElementTree as ET

def validar_carpetas_y_archivos(ruta_2024, ruta_2025):
    """
    Valida las carpetas de entrada y verifica la estructura de los archivos XML.

    Args:
        ruta_2024 (str): Ruta de la carpeta para vigencia 2024.
        ruta_2025 (str): Ruta de la carpeta para vigencia 2025.

    Returns:
        dict: Resultado con diferencias, archivos válidos y no válidos en ambas carpetas.
    """
    # Listar todos los archivos en las carpetas
    todos_archivos_2024 = sorted(os.listdir(ruta_2024))
    todos_archivos_2025 = sorted(os.listdir(ruta_2025))

    # Filtrar archivos que cumplen con la estructura esperada
    archivos_validos_2024 = sorted([f for f in todos_archivos_2024 if re.match(r"^Registro_catastral_25\d{3}\.xml$", f)])
    archivos_validos_2025 = sorted([f for f in todos_archivos_2025 if re.match(r"^Registro_catastral_25\d{3}\.xml$", f)])

    # Archivos que no cumplen con la estructura
    archivos_no_validos_2024 = list(set(todos_archivos_2024) - set(archivos_validos_2024))
    archivos_no_validos_2025 = list(set(todos_archivos_2025) - set(archivos_validos_2025))

    # Comparar diferencias entre las carpetas
    diferencias = {
        "faltantes_2024": list(set(archivos_validos_2025) - set(archivos_validos_2024)),
        "faltantes_2025": list(set(archivos_validos_2024) - set(archivos_validos_2025))
    }

    # Imprimir conteos y nombres de archivos
    print("Conteo inicial de archivos:")
    print(f"- 2024: {len(todos_archivos_2024)} archivos encontrados")
    print(f"- 2025: {len(todos_archivos_2025)} archivos encontrados")
    print("\nArchivos que cumplen con la estructura de nombre:")
    print(f"- 2024: {len(archivos_validos_2024)} archivos válidos")
    print(f"- 2025: {len(archivos_validos_2025)} archivos válidos")
    print("\nArchivos que no cumplen con la estructura:")
    print(f"- 2024: {len(archivos_no_validos_2024)} archivos no válidos")
    print(f"  Nombres: {', '.join(archivos_no_validos_2024)}")
    print(f"- 2025: {len(archivos_no_validos_2025)} archivos no válidos")
    print(f"  Nombres: {', '.join(archivos_no_validos_2025)}")
    print("\nDiferencias entre las carpetas:")
    print(f"- Archivos faltantes en 2024: {len(diferencias['faltantes_2024'])}")
    print(f"  Nombres: {', '.join(diferencias['faltantes_2024']) if diferencias['faltantes_2024'] else 'Ninguno'}")
    print(f"- Archivos faltantes en 2025: {len(diferencias['faltantes_2025'])}")
    print(f"  Nombres: {', '.join(diferencias['faltantes_2025']) if diferencias['faltantes_2025'] else 'Ninguno'}")

    return {
        "archivos_validos_2024": archivos_validos_2024,
        "archivos_validos_2025": archivos_validos_2025,
        "archivos_no_validos_2024": archivos_no_validos_2024,
        "archivos_no_validos_2025": archivos_no_validos_2025,
        "diferencias": diferencias
    }

def procesar_archivo_xml(ruta_archivo, consulta=None):
    """
    Procesa un archivo XML y extrae los números prediales que cumplen con una consulta específica.

    Args:
        ruta_archivo (str): Ruta del archivo XML a procesar.
        consulta (func): Función que recibe un elemento <predio> y devuelve True si cumple la condición.

    Returns:
        dict: Diccionario con conteo y lista de números prediales que cumplen la condición.
    """
    numeros_prediales = []
    try:
        tree = ET.parse(ruta_archivo)
        root = tree.getroot()

        # Iterar sobre los elementos <predio>
        for predio in root.findall(".//predio"):
            # Si hay una consulta definida, verificar que el predio la cumpla
            if consulta and not consulta(predio):
                continue

            # Extraer el número predial
            codigo_predial = predio.find("codigo_predial_nacional")
            if codigo_predial is not None:
                numeros_prediales.append(codigo_predial.text)

    except Exception as e:
        print(f"Error procesando {ruta_archivo}: {e}")

    return {
        "conteo": len(numeros_prediales),
        "numeros_prediales": list(set(numeros_prediales))  # Eliminar duplicados
    }

def identificar_predios_sin_propietarios(ruta_archivo):
    """
    Identifica los números prediales nacionales únicos que no tienen propietarios asociados.

    Args:
        ruta_archivo (str): Ruta del archivo XML a procesar.

    Returns:
        dict: Diccionario con conteo y lista de predios sin propietarios.
    """
    predios_sin_propietarios = {}
    try:
        # Cargar y parsear el archivo XML
        tree = ET.parse(ruta_archivo)
        root = tree.getroot()

        # Agrupar predios por "codigo_predial_nacional"
        for predio in root.findall(".//predio"):
            codigo_predial = predio.find("codigo_predial_nacional").text

            # Buscar si tiene algún documento asociado
            interesados = predio.find(".//interesados/persona_natural/documento")
            documento = interesados.text if interesados is not None else ""

            # Si el documento está vacío o es nulo, lo contamos
            if codigo_predial:
                if codigo_predial not in predios_sin_propietarios:
                    predios_sin_propietarios[codigo_predial] = 0

                if documento.strip() == "":
                    predios_sin_propietarios[codigo_predial] += 1

        # Filtrar predios donde todos los registros de "documento" sean vacíos
        predios_sin_documentos = [
            predio for predio, conteo in predios_sin_propietarios.items() if conteo > 0
        ]

    except Exception as e:
        print(f"Error procesando el archivo {ruta_archivo}: {e}")
        return {"conteo": 0, "numeros_prediales": []}

    return {
        "conteo": len(predios_sin_documentos),
        "numeros_prediales": predios_sin_documentos
    }



def comparar_diferencias(numeros_2024, numeros_2025):
    """
    Compara los números prediales entre dos listas y encuentra diferencias.

    Args:
        numeros_2024 (list): Lista de números prediales de la vigencia 2024.
        numeros_2025 (list): Lista de números prediales de la vigencia 2025.

    Returns:
        list: Lista de números prediales que están en 2025 pero no en 2024.
    """
    return list(set(numeros_2025) - set(numeros_2024))

def main(ruta_2024, ruta_2025, ruta_resultados):
    """
    Función principal para ejecutar el script.

    Args:
        ruta_2024 (str): Ruta de la carpeta de vigencia 2024.
        ruta_2025 (str): Ruta de la carpeta de vigencia 2025.
        ruta_resultados (str): Carpeta donde guardar los reportes.

    Returns:
        None
    """
    # Validar carpetas y archivos
    validacion = validar_carpetas_y_archivos(ruta_2024, ruta_2025)

    # Archivo consolidado de resultados
    ruta_reporte_consolidado = os.path.join(ruta_resultados, "Reporte_Consolidado.txt")

    with open(ruta_reporte_consolidado, "w") as reporte:
        reporte.write("Reporte consolidado de predios sin propietarios asociados\n")
        reporte.write("--------------------------------------------------------\n\n")

        # Procesar archivos válidos
        for archivo_2024 in validacion["archivos_validos_2024"]:
            ruta_archivo = os.path.join(ruta_2024, archivo_2024)
            resultado = identificar_predios_sin_propietarios(ruta_archivo)

            # Escribir resultados en el archivo consolidado
            reporte.write(f"----    RESULTADOS {archivo_2024}:    ----\n")
            reporte.write(f"Cantidad de predios sin propietarios: {resultado['conteo']}\n")
            reporte.write("Números prediales únicos:\n")
            for codigo in resultado["numeros_prediales"]:
                reporte.write(f"- {codigo}\n")
            reporte.write("\n")

        print("Procesamiento completado. Resultados almacenados en el archivo consolidado.")

if __name__ == "__main__":
    # Rutas de ejemplo, actualiza según tu entorno
    ruta_2024 = r"C:\ACC\SCRIPT_13012025_COMP_MPIO_2024_2025\p_2024"
    ruta_2025 = r"C:\ACC\SCRIPT_13012025_COMP_MPIO_2024_2025\p_2025"
    ruta_resultados = r"C:\ACC\SCRIPT_13012025_COMP_MPIO_2024_2025\Script_Diferencias_Mpios_2024_2025"

    if not os.path.exists(ruta_resultados):
        os.makedirs(ruta_resultados)

    main(ruta_2024, ruta_2025, ruta_resultados)