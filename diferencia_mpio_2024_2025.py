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

def validar_carpetas_y_archivos(ruta_2024, ruta_2025, reporte=None):
    """
    Valida las carpetas de entrada y verifica la estructura de los archivos XML.

    Args:
        ruta_2024 (str): Ruta de la carpeta para vigencia 2024.
        ruta_2025 (str): Ruta de la carpeta para vigencia 2025.
        reporte (file, optional): Archivo abierto para escribir el reporte.

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

    # Escribir en el archivo de reporte si se proporciona
    if reporte:
        reporte.write("Conteo inicial de archivos:\n")
        reporte.write(f"- 2024: {len(todos_archivos_2024)} archivos encontrados\n")
        reporte.write(f"- 2025: {len(todos_archivos_2025)} archivos encontrados\n")
        reporte.write("\nArchivos que cumplen con la estructura de nombre:\n")
        reporte.write(f"- 2024: {len(archivos_validos_2024)} archivos válidos\n")
        reporte.write(f"- 2025: {len(archivos_validos_2025)} archivos válidos\n")
        reporte.write("\nArchivos que no cumplen con la estructura:\n")
        reporte.write(f"- 2024: {len(archivos_no_validos_2024)} archivos no válidos\n")
        reporte.write(f"  Nombres: {', '.join(archivos_no_validos_2024)}\n")
        reporte.write(f"- 2025: {len(archivos_no_validos_2025)} archivos no válidos\n")
        reporte.write(f"  Nombres: {', '.join(archivos_no_validos_2025)}\n")
        reporte.write("\nDiferencias entre las carpetas:\n")
        reporte.write(f"- Archivos faltantes en 2024: {len(diferencias['faltantes_2024'])}\n")
        reporte.write(f"  Nombres: {', '.join(diferencias['faltantes_2024']) if diferencias['faltantes_2024'] else 'Ninguno'}\n")
        reporte.write(f"- Archivos faltantes en 2025: {len(diferencias['faltantes_2025'])}\n")
        reporte.write(f"  Nombres: {', '.join(diferencias['faltantes_2025']) if diferencias['faltantes_2025'] else 'Ninguno'}\n")
        reporte.write("\n")

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

#CONSULTA 1
def identificar_predios_sin_interesados(ruta_archivo):
    """
    Identifica los números prediales nacionales únicos que no tienen interesados asociados.
    Un predio se considera sin interesados si la sección <interesados> está vacía o no existe.

    Args:
        ruta_archivo (str): Ruta del archivo XML a procesar.

    Returns:
        dict: Diccionario con conteo y lista de predios sin interesados.
    """
    predios_sin_interesados = {}
    try:
        # Cargar y parsear el archivo XML
        tree = ET.parse(ruta_archivo)
        root = tree.getroot()

        # Iterar sobre cada predio
        for predio in root.findall(".//predio"):
            # Obtener el código predial nacional
            codigo_predial = predio.find("codigo_predial_nacional").text

            # Verificar si <interesados> está vacío o no existe
            interesados = predio.find(".//interesados")
            if interesados is None or len(interesados) == 0:  # Nodo <interesados> ausente o sin subnodos
                if codigo_predial:
                    predios_sin_interesados[codigo_predial] = True

    except Exception as e:
        print(f"Error procesando el archivo {ruta_archivo}: {e}")
        return {"conteo": 0, "numeros_prediales": []}

    # Extraer las claves de predios sin interesados
    predios_sin_datos = list(predios_sin_interesados.keys())

    return {
        "conteo": len(predios_sin_datos),
        "numeros_prediales": predios_sin_datos
    }

#CONSULTA 2
def identificar_predios_sin_avaluos(ruta_archivo):
    """
    Identifica los números prediales nacionales cuyos <avaluo> están vacíos o ausentes.

    Args:
        ruta_archivo (str): Ruta del archivo XML a procesar.

    Returns:
        dict: Diccionario con conteo y lista de predios sin avaluos.
    """
    predios_sin_avaluos = {}
    try:
        # Cargar y parsear el archivo XML
        tree = ET.parse(ruta_archivo)
        root = tree.getroot()

        # Iterar sobre cada predio
        for predio in root.findall(".//predio"):
            # Obtener el código predial nacional
            codigo_predial = predio.find("codigo_predial_nacional").text

            # Verificar si <avaluo> está vacío o ausente
            avaluo = predio.find(".//avaluo")
            if avaluo is None or not avaluo.text.strip():  # Nodo <avaluo> ausente o sin valor
                if codigo_predial:
                    predios_sin_avaluos[codigo_predial] = True

    except Exception as e:
        print(f"Error procesando el archivo {ruta_archivo}: {e}")
        return {"conteo": 0, "numeros_prediales": []}

    # Extraer las claves de predios sin avaluos
    predios_sin_datos = list(predios_sin_avaluos.keys())

    return {
        "conteo": len(predios_sin_datos),
        "numeros_prediales": predios_sin_datos
    }

# CONSULTA 3
def identificar_predios_avaluo_cero_o_condiciones(ruta_archivo):
    """
    Identifica los predios cuyo valor de avalúo es 0 o ausente y cumplen con
    condiciones adicionales.

    Condiciones adicionales:
    - La posición 22 del número predial nacional es igual a '0'.
    - La condición del predio es 'NPH'.

    Args:
        ruta_archivo (str): Ruta del archivo XML a procesar.

    Returns:
        dict: Diccionario con conteo y lista de predios que cumplen las condiciones.
    """
    predios_avaluo_cero = {}
    try:
        # Cargar y parsear el archivo XML
        tree = ET.parse(ruta_archivo)
        root = tree.getroot()

        # Iterar sobre cada predio
        for predio in root.findall(".//predio"):
            # Obtener campos relevantes
            codigo_predial = predio.find("codigo_predial_nacional").text
            condicion_predio = predio.find("condicion_predio").text
            avaluo = predio.find(".//avaluo")
            avaluo_valor = int(avaluo.text) if avaluo is not None and avaluo.text.isdigit() else 0

            # Verificar condiciones
            if avaluo_valor == 0:
                posicion_22 = codigo_predial[21] if len(codigo_predial) >= 22 else None
                if posicion_22 == '0' or condicion_predio == "NPH":
                    predios_avaluo_cero[codigo_predial] = {
                        "avaluo": avaluo_valor,
                        "condicion_predio": condicion_predio
                    }

    except Exception as e:
        print(f"Error procesando el archivo {ruta_archivo}: {e}")
        return {"conteo": 0, "numeros_prediales": []}

    # Extraer las claves de predios que cumplen las condiciones
    predios_cumplen = list(predios_avaluo_cero.keys())

    return {
        "conteo": len(predios_cumplen),
        "numeros_prediales": predios_cumplen
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

def extraer_codigo_municipio(nombre_archivo):
    """
    Extrae el código del municipio basado en el nombre del archivo.
    Args:
        nombre_archivo (str): Nombre del archivo, ej. "Registro_catastral_25019.xml".
    Returns:
        str: Código del municipio (los 5 caracteres antes de .xml o después del segundo _).
    """
    if nombre_archivo.endswith(".xml"):
        # Extraer los 5 caracteres antes de ".xml"
        return nombre_archivo.split("_")[-1].split(".")[0]
    return None

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
    # Archivo consolidado de resultados
    ruta_reporte_consolidado = os.path.join(ruta_resultados, "Reporte_Consolidado.txt")

    with open(ruta_reporte_consolidado, "w") as reporte:
        reporte.write("Reporte consolidado de validación de archivos\n")
        reporte.write("------------------------------------------------\n\n")

        # Validar carpetas y escribir resultados en el reporte
        validacion = validar_carpetas_y_archivos(ruta_2024, ruta_2025, reporte)

        # Procesar archivos válidos 2024
        for archivo_2024 in validacion["archivos_validos_2024"]:
            ruta_archivo_2024 = os.path.join(ruta_2024, archivo_2024)
            resultado_2024 = identificar_predios_sin_interesados(ruta_archivo_2024)

            # Extraer código del municipio
            codigo_municipio = extraer_codigo_municipio(archivo_2024)

            # Escribir resultados en el archivo consolidado
            #CONSULTA 1 PREDIOS SIN INTERESADOS
            reporte.write(f"---- RESULTADOS MUNICIPIO {codigo_municipio} CON PREDIOS SIN INTERESADOS, PARA LA VIGENCIA 2024 ----\n")
            reporte.write(f"----    RESULTADOS {archivo_2024}:    ----\n")
            reporte.write(f"Cantidad de predios sin propietarios: {resultado_2024['conteo']}\n")
            reporte.write("Números prediales únicos:\n")
            for codigo in resultado_2024["numeros_prediales"]:
                reporte.write(f"{codigo}\n")
            reporte.write("\n\n")

            # Consulta 2: Predios sin avaluos catastrales
            resultado_sin_avaluos_2024 = identificar_predios_sin_avaluos(ruta_archivo_2024)
            reporte.write(f"---- RESULTADOS MUNICIPIO {codigo_municipio} CON PREDIOS SIN AVALUOS CATASTRALES, PARA LA VIGENCIA 2024 ----\n")
            reporte.write(f"----    RESULTADOS {archivo_2024}:    ----\n")
            reporte.write(f"Cantidad de predios sin avaluos catastrales: {resultado_sin_avaluos_2024['conteo']}\n")
            reporte.write("Números prediales únicos:\n")
            for codigo in resultado_sin_avaluos_2024["numeros_prediales"]:
                reporte.write(f"{codigo}\n")
            reporte.write("\n\n")

            # Consulta 3: Predios NPH con avaluo igual a cero
            resultado_cero = identificar_predios_avaluo_cero_o_condiciones(ruta_archivo_2024)
            reporte.write(f"---- RESULTADOS MUNICIPIO {codigo_municipio} CON PREDIOS NPH CON AVALUOS IGUALES A CERO, PARA LA VIGENCIA 2024 ----\n")
            reporte.write(f"----    RESULTADOS {archivo_2024}:    ----\n")
            reporte.write(f"- Predios NPH con avalúo cero: {resultado_cero['conteo']}\n")
            reporte.write("Números prediales únicos:\n")
            for codigo in resultado_cero["numeros_prediales"]:
                reporte.write(f"{codigo}\n")
            reporte.write("\n\n")

        # Procesar archivos válidos 2025
        for archivo_2025 in validacion["archivos_validos_2025"]:
            ruta_archivo_2025 = os.path.join(ruta_2025, archivo_2025)
            resultado_2025 = identificar_predios_sin_interesados(ruta_archivo_2025)

            # Extraer código del municipio
            codigo_municipio = extraer_codigo_municipio(archivo_2025)
        
            # Escribir resultados en el archivo consolidado
            #CONSULTA 1 PRESIOS SIN INTERESADOS
            reporte.write(f"---- RESULTADOS MUNICIPIO {codigo_municipio} CON PREDIOS SIN INTERESADOS, PARA LA VIGENCIA 2025 ----\n")
            reporte.write(f"----    RESULTADOS {archivo_2025}:    ----\n")
            reporte.write(f"Cantidad de predios sin propietarios: {resultado_2025['conteo']}\n")
            reporte.write("Números prediales únicos:\n")
            for codigo in resultado_2025["numeros_prediales"]:
                reporte.write(f"{codigo}\n")
            reporte.write("\n\n")

            # Consulta 2: Predios sin avaluos catastrales
            resultado_sin_avaluos_2025 = identificar_predios_sin_avaluos(ruta_archivo_2025)
            reporte.write(f"---- RESULTADOS MUNICIPIO {codigo_municipio} CON PREDIOS SIN AVALUOS CATASTRALES, PARA LA VIGENCIA 2025 ----\n")
            reporte.write(f"----    RESULTADOS {archivo_2025}:    ----\n")
            reporte.write(f"Cantidad de predios sin avaluos catastrales: {resultado_sin_avaluos_2025['conteo']}\n")
            reporte.write("Números prediales únicos:\n")
            for codigo in resultado_sin_avaluos_2025["numeros_prediales"]:
                reporte.write(f"{codigo}\n")
            reporte.write("\n\n")

            # CONSULTA 3: Identificar predios con avalúo cero o condiciones
            resultado_cero = identificar_predios_avaluo_cero_o_condiciones(ruta_archivo_2025)
            reporte.write(f"---- RESULTADOS MUNICIPIO {codigo_municipio} CON PREDIOS NPH CON AVALUOS IGUALES A CERO, PARA LA VIGENCIA 2025 ----\n")
            reporte.write(f"----    RESULTADOS {archivo_2025}:    ----\n")
            reporte.write(f"- Predios NPH con avalúo cero: {resultado_cero['conteo']}\n")
            reporte.write("Números prediales únicos:\n")
            for codigo in resultado_cero["numeros_prediales"]:
                reporte.write(f"{codigo}\n")
            reporte.write("\n\n")

        print("Procesamiento completado. Resultados almacenados en el archivo consolidado.")


if __name__ == "__main__":
    # Rutas de ejemplo, actualiza según tu entorno
    ruta_2024 = r"C:\ACC\SCRIPT_13012025_COMP_MPIO_2024_2025\p_2024"
    ruta_2025 = r"C:\ACC\SCRIPT_13012025_COMP_MPIO_2024_2025\p_2025"
    ruta_resultados = r"C:\ACC\SCRIPT_13012025_COMP_MPIO_2024_2025\Script_Diferencias_Mpios_2024_2025"

    if not os.path.exists(ruta_resultados):
        os.makedirs(ruta_resultados)

    main(ruta_2024, ruta_2025, ruta_resultados)