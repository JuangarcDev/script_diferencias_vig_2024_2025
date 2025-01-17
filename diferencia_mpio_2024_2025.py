# -*- coding: utf-8 -*-
"""
Script para comparar archivos XML de registros catastrales entre dos vigencias.

Propósito:
- Identificar registros que cumplen ciertas condiciones en archivos XML organizados por municipios.
- Comparar los datos entre dos carpetas (vigencia ENERO 2024 y DICIEMBRE 2024).
- Generar reportes detallados con resultados de las consultas, conteos y diferencias.

Inputs:
1. Ruta de la carpeta de archivos XML para vigencia ENERO 2024.
2. Ruta de la carpeta de archivos XML para vigencia DICIEMBRE 2024.
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
import psycopg2
import xml.etree.ElementTree as ET
from decouple import config

# CONECTAR CON LA BASE DE DATOS DE TRAMITES
def connect_to_db(reporte):
    """
    Función para conectar con la DB de PostgreSQL de TRAMITES
    """
    try:
        conn = psycopg2.connect(
            host=config('DB_HOST'),
            database=config('DB_NAME'),
            user=config('DB_USER'),
            password=config('DB_PASSWORD'),
            port=config('DB_PORT')
        )
        reporte.write(f"Conexión exitosa a la Base de Datos PostgreSQL.\n\n")
        return conn
    except Exception as e:
        reporte.write(f"Error al conectar con la Base de Datos PostgreSQL: {e}")
        return None
    
# CONECTAR A LA BASE DE DATOS DE RESOLUCIONES
def connect_to_db_res(reporte):
    """
    Función para conectar con la DB de PostgreSQL de RESOLUCIONES
    """
    try:
        conn2 = psycopg2.connect(
            host2=config('DB_HOST'),
            database2=config('DB_NAME2'),
            user2=config('DB_USER'),
            password2=config('DB_PASSWORD'),
            port2=config('DB_PORT')
        )
        reporte.write(f"Conexión exitosa a la Base de Datos PostgreSQL.\n\n")
        return conn2
    except Exception as e:
        reporte.write(f"Error al conectar con la Base de Datos PostgreSQL: {e}")
        return None    

def validar_carpetas_y_archivos(ruta_enero_2024, ruta_dic_2024, reporte=None):
    """
    Valida las carpetas de entrada y verifica la estructura de los archivos XML.

    Args:
        ruta_enero_2024 (str): Ruta de la carpeta para vigencia_enero_2024.
        ruta_dic_2024 (str): Ruta de la carpeta para vigencia_diciembre_2024.
        reporte (file, optional): Archivo abierto para escribir el reporte.

    Returns:
        dict: Resultado con diferencias, archivos válidos y no válidos en ambas carpetas.
    """
    # Listar todos los archivos en las carpetas
    todos_archivos_2024 = sorted(os.listdir(ruta_enero_2024))
    todos_archivos_2025 = sorted(os.listdir(ruta_dic_2024))

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


def obtener_predios_desde_xml(ruta_archivo):
    """
    Extrae los predios de un archivo XML y estructura sus datos como diccionarios anidados.
    
    Args:
        ruta_archivo (str): Ruta del archivo XML.
        
    Returns:
        dict: Diccionario donde las claves son los códigos prediales nacionales y los valores son diccionarios con los datos del predio.
    """

    def parsear_elemento(elemento):
        """
        Convierte un elemento XML en un diccionario, manejando recursividad si hay hijos.
        Args:
            elemento (Element): Elemento XML a procesar.
        Returns:
            dict: Representación del elemento como diccionario.
        """
        parsed = {}
        for hijo in elemento:
            if len(hijo):  # Si el elemento tiene hijos, procesarlos recursivamente
                parsed[hijo.tag] = parsear_elemento(hijo)
            else:  # Si no tiene hijos, tomar el texto directamente
                parsed[hijo.tag] = hijo.text
        return parsed

    predios = {}
    try:
        tree = ET.parse(ruta_archivo)
        root = tree.getroot()
        
        # Iterar sobre cada predio
        for predio in root.findall('.//predio'):
            codigo_predial = predio.find('codigo_predial_nacional')
            if codigo_predial is not None and codigo_predial.text:
                # Parsear el contenido del predio
                predios[codigo_predial.text] = parsear_elemento(predio)
    except Exception as e:
        print(f"Error procesando {ruta_archivo}: {e}")
    return predios


def comparar_predios(predios_enero, predios_dic, reporte):
    """
    Compara los predios de dos vigencias y escribe las diferencias en el reporte,
    desglosadas por atributos e ignorando excepciones específicas.
    Args:
        predios_enero (dict): Predios de la vigencia de enero.
        predios_dic (dict): Predios de la vigencia de diciembre.
        reporte (file): Archivo para escribir el reporte.
    """
    global acumulados_comunes

    codigos_enero = set(predios_enero.keys())
    codigos_dic = set(predios_dic.keys())

    # Predios únicos en enero y diciembre
    unicos_enero = codigos_enero - codigos_dic
    unicos_dic = codigos_dic - codigos_enero

    # Reporte de predios únicos
    reporte.write("=== Predios únicos en enero ===\n")
    reporte.write("\n".join(unicos_enero) + "\n\n")
    reporte.write("=== Predios únicos en diciembre ===\n")
    reporte.write("\n".join(unicos_dic) + "\n\n")

    # Predios coincidentes
    comunes = codigos_enero & codigos_dic

    #Reportes
    reporte.write("=== Comparación de predios coincidentes ===\n")
    reporte.write("=== PREDIOS QUE CONTIENEN DIFERENCIAS ENTRE LA VIGENCIA ENERO 2024 Y DICIEMBRE DE 2024 ===\n")
    predios_con_diferencias = []

    #DESGLOCE POR ATRIBUTOS DE LA INFORMACION DEL PREDIO
    for codigo in comunes:
        diferencias = []
        predio_enero = predios_enero[codigo]
        predio_dic = predios_dic[codigo]

        for key in predio_enero.keys():
            valor_enero = predio_enero[key]
            valor_dic = predio_dic.get(key, None)

            # Regla 1: Omitir diferencias entre NULL y 0/0.0
            if (valor_enero in [None, '', 'NULL'] and valor_dic in [0, 0.0]) or \
               (valor_dic in [None, '', 'NULL'] and valor_enero in [0, 0.0]):
                continue

            # Regla 2: Ignorar cambios en <direccion> si el valor previo era "SIN DIRECCION"
            if key == 'direccion' and valor_enero == "SIN DIRECCION":
                continue

            # Regla 3: Ignorar cambios en nombres si son "DESCONOCIDO"
            if key in ['primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido'] and \
               valor_enero == "DESCONOCIDO":
                continue

            # Comparar valores si no cumplen las excepciones
            if valor_enero != valor_dic:
                diferencias.append(f"<{key}>{valor_enero}</{key}> -> <{key}>{valor_dic}</{key}>")

        # Si hay diferencias, añadir al reporte
        if diferencias:
            predios_con_diferencias.append(codigo)
            reporte.write(f"Código: {codigo}\n")
            reporte.write("\n".join(diferencias) + "\n\n")    

    # Actualizar acumulados_comunes asegurando unicidad
    acumulados_comunes.update(predios_con_diferencias)
    # Conteo de predios con diferencias
    reporte.write("\n=== Estadísticas ===\n")
    reporte.write(f"Cantidad de predios con diferencias para el municipio especifico: {len(predios_con_diferencias)}\n")
    reporte.write(f"Cantidad total de predios con diferencias acumulados para todos los municipios: {len(acumulados_comunes)}\n\n")

def procesar_carpetas(carpeta_enero, carpeta_dic, reporte):
    """
    Procesa las carpetas de enero y diciembre para comparar los archivos XML.
    Args:
        carpeta_enero (str): Ruta de la carpeta de enero.
        carpeta_dic (str): Ruta de la carpeta de diciembre.
        ruta_reporte (str): Ruta del archivo donde se guardará el reporte.
    """
    archivos_enero = {os.path.splitext(f)[0]: os.path.join(carpeta_enero, f)
                       for f in os.listdir(carpeta_enero) if f.endswith('.xml')}
    archivos_dic = {os.path.splitext(f)[0]: os.path.join(carpeta_dic, f)
                     for f in os.listdir(carpeta_dic) if f.endswith('.xml')}

    # Archivos comunes
    archivos_comunes = set(archivos_enero.keys()) & set(archivos_dic.keys())

    if reporte:
        for archivo in archivos_comunes:
            reporte.write(f"\n=== Comparando archivo {archivo} ===\n")
            ruta_enero = archivos_enero[archivo]
            ruta_dic = archivos_dic[archivo]

            predios_enero = obtener_predios_desde_xml(ruta_enero)
            predios_dic = obtener_predios_desde_xml(ruta_dic)
            comparar_predios(predios_enero, predios_dic, reporte)

        reporte.write("\n=== Proceso completado ===\n")

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

def extract_land_data(db_connection, reporte):
    """
    Función para extraer el atributo 'land' de la consulta definida.

    Args:
        db_connection: Conexión activa a la base de datos PostgreSQL.
        reporte: Objeto archivo para escribir el reporte.

    Returns:
        conjunto_land (set): Conjunto de valores únicos del atributo 'land'.
    """
    query = """
    SELECT t2.land
    FROM data.tramite t1
    JOIN data.land_tansacts_tracking t2
    ON t2.transact = t1.id
    WHERE t2.transact IS NOT NULL 
    AND t1.estado_actual_fecha_inicio >= '2024-02-01 00:00:00'
    AND t1.estado_actual_fecha_inicio <= '2024-12-31 23:59:59'
    AND t1.estado_actual = 8;
    """
    try:
        cursor = db_connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()

        # Extraer valores únicos
        conjunto_land = set(row[0] for row in results if row[0] is not None)

        # Reportar conteo y primeros 10 registros
        reporte.write(f"Total de registros encontrados: {len(conjunto_land)}\n")
        reporte.write("Primeros 10 registros:\n")
        for land in list(conjunto_land)[:10]:
            reporte.write(f"{land}\n")
        reporte.write("\n")

        return conjunto_land

    except Exception as e:
        reporte.write(f"Error al ejecutar la consulta: {e}\n")
        return set()

def main(ruta_enero_2024, ruta_dic_2024, ruta_resultados):
    """
    Función principal para ejecutar el script.

    Args:
        ruta_enero_2024 (str): Ruta de la carpeta de vigencia_enero_2024.
        ruta_dic_2024 (str): Ruta de la carpeta de vigencia_diciembre_2024.
        ruta_resultados (str): Carpeta donde guardar los reportes.

    Returns:
        None
    """


    # Archivo consolidado de resultados
    ruta_reporte_consolidado = os.path.join(ruta_resultados, "Reporte_Consolidado.txt")

    with open(ruta_reporte_consolidado, "w") as reporte:
        reporte.write("Reporte consolidado de validación de archivos\n")
        reporte.write("------------------------------------------------\n\n")

        # CONEXION A LA DB:
        db_connection = connect_to_db(reporte)
        if not db_connection:
            reporte.write("Conexión a la DB fallida. Terminando el script.")
            return

        # Validar carpetas y escribir resultados en el reporte
        validacion = validar_carpetas_y_archivos(ruta_enero_2024, ruta_dic_2024, reporte)

        # CONSULTA 0
        procesar_carpetas(ruta_enero_2024, ruta_dic_2024, reporte)

        # Procesar archivos válidos 2024
        for archivo_2024 in validacion["archivos_validos_2024"]:
            ruta_archivo_2024 = os.path.join(ruta_enero_2024, archivo_2024)
            resultado_2024 = identificar_predios_sin_interesados(ruta_archivo_2024)

            # Extraer código del municipio
            codigo_municipio = extraer_codigo_municipio(archivo_2024)

            #ESPACIO PARA CONSULTA 0, DIFERENCIA ENTRE PREDIOS ENERO 2024 VS DICIEMBRE 2024


            # Escribir resultados en el archivo consolidado
            #CONSULTA 1 PREDIOS SIN INTERESADOS
            reporte.write(f"---- RESULTADOS MUNICIPIO {codigo_municipio} CON PREDIOS SIN INTERESADOS, PARA LA vigencia_enero_2024 ----\n")
            reporte.write(f"----    RESULTADOS {archivo_2024}:    ----\n")
            reporte.write(f"Cantidad de predios sin propietarios: {resultado_2024['conteo']}\n")
            reporte.write("Números prediales únicos:\n")
            for codigo in resultado_2024["numeros_prediales"]:
                reporte.write(f"{codigo}\n")
            reporte.write("\n\n")

            # Consulta 2: Predios sin avaluos catastrales
            resultado_sin_avaluos_2024 = identificar_predios_sin_avaluos(ruta_archivo_2024)
            reporte.write(f"---- RESULTADOS MUNICIPIO {codigo_municipio} CON PREDIOS SIN AVALUOS CATASTRALES, PARA LA vigencia_enero_2024 ----\n")
            reporte.write(f"----    RESULTADOS {archivo_2024}:    ----\n")
            reporte.write(f"Cantidad de predios sin avaluos catastrales: {resultado_sin_avaluos_2024['conteo']}\n")
            reporte.write("Números prediales únicos:\n")
            for codigo in resultado_sin_avaluos_2024["numeros_prediales"]:
                reporte.write(f"{codigo}\n")
            reporte.write("\n\n")

            # Consulta 3: Predios NPH con avaluo igual a cero
            resultado_cero = identificar_predios_avaluo_cero_o_condiciones(ruta_archivo_2024)
            reporte.write(f"---- RESULTADOS MUNICIPIO {codigo_municipio} CON PREDIOS NPH CON AVALUOS IGUALES A CERO, PARA LA vigencia_enero_2024 ----\n")
            reporte.write(f"----    RESULTADOS {archivo_2024}:    ----\n")
            reporte.write(f"- Predios NPH con avalúo cero: {resultado_cero['conteo']}\n")
            reporte.write("Números prediales únicos:\n")
            for codigo in resultado_cero["numeros_prediales"]:
                reporte.write(f"{codigo}\n")
            reporte.write("\n\n")

        # Procesar archivos válidos 2025
        for archivo_2025 in validacion["archivos_validos_2025"]:
            ruta_archivo_2025 = os.path.join(ruta_dic_2024, archivo_2025)
            resultado_2025 = identificar_predios_sin_interesados(ruta_archivo_2025)

            # Extraer código del municipio
            codigo_municipio = extraer_codigo_municipio(archivo_2025)

            # Escribir resultados en el archivo consolidado
            #CONSULTA 1 PRESIOS SIN INTERESADOS
            reporte.write(f"---- RESULTADOS MUNICIPIO {codigo_municipio} CON PREDIOS SIN INTERESADOS, PARA LA vigencia_diciembre_2024 ----\n")
            reporte.write(f"----    RESULTADOS {archivo_2025}:    ----\n")
            reporte.write(f"Cantidad de predios sin propietarios: {resultado_2025['conteo']}\n")
            reporte.write("Números prediales únicos:\n")
            for codigo in resultado_2025["numeros_prediales"]:
                reporte.write(f"{codigo}\n")
            reporte.write("\n\n")

            # Consulta 2: Predios sin avaluos catastrales
            resultado_sin_avaluos_2025 = identificar_predios_sin_avaluos(ruta_archivo_2025)
            reporte.write(f"---- RESULTADOS MUNICIPIO {codigo_municipio} CON PREDIOS SIN AVALUOS CATASTRALES, PARA LA vigencia_diciembre_2024 ----\n")
            reporte.write(f"----    RESULTADOS {archivo_2025}:    ----\n")
            reporte.write(f"Cantidad de predios sin avaluos catastrales: {resultado_sin_avaluos_2025['conteo']}\n")
            reporte.write("Números prediales únicos:\n")
            for codigo in resultado_sin_avaluos_2025["numeros_prediales"]:
                reporte.write(f"{codigo}\n")
            reporte.write("\n\n")

            # CONSULTA 3: Identificar predios con avalúo cero o condiciones
            resultado_cero = identificar_predios_avaluo_cero_o_condiciones(ruta_archivo_2025)
            reporte.write(f"---- RESULTADOS MUNICIPIO {codigo_municipio} CON PREDIOS NPH CON AVALUOS IGUALES A CERO, PARA LA vigencia_diciembre_2024 ----\n")
            reporte.write(f"----    RESULTADOS {archivo_2025}:    ----\n")
            reporte.write(f"- Predios NPH con avalúo cero: {resultado_cero['conteo']}\n")
            reporte.write("Números prediales únicos:\n")
            for codigo in resultado_cero["numeros_prediales"]:
                reporte.write(f"{codigo}\n")
            reporte.write("\n\n")

        # CONSULTA 0 A LA DB DE TRAMITES
        if db_connection:
            # Llamar a la función de extracción de datos
            conjunto_land = extract_land_data(db_connection, reporte)
            reporte.write(f"Valores únicos extraídos: {len(conjunto_land)}\n")
        else:
            reporte.write("No se pudo establecer la conexión con la base de datos.\n")

        # HACE LA DIFERENCIA ENTRE AMBOS CONJUNTOS DE DATOS, PARA IDENTIFICAR LOS PREDIOS QUE TIENEN MODIFICACIONES EN LA VIGENCIA Y NO TIENEN TRAMITE ASOCIADO
        # Realizar la diferencia de conjuntos
        predios_modificaciones_sin_tramite = acumulados_comunes - conjunto_land

        # Reportar los resultados
        reporte.write("=== Predios con modificaciones en el rango sin trámite ===\n")
        for predio in predios_modificaciones_sin_tramite:
            reporte.write(f"{predio}\n")

        # Conteo total de predios
        reporte.write("\n=== Estadísticas ===\n")
        reporte.write(f"Cantidad total de predios con modificaciones sin trámite: {len(predios_modificaciones_sin_tramite)}\n")
        print("Procesamiento completado. Resultados almacenados en el archivo consolidado.")


if __name__ == "__main__":
    # Lista global para acumular los números prediales totales
    acumulados_comunes = set()

    # Rutas de ejemplo, actualiza según tu entorno
    ruta_enero_2024 = r"C:\ACC\SCRIPT_13012025_COMP_MPIO_2024_2025\Registros_2024_feb"
    ruta_dic_2024 = r"C:\ACC\SCRIPT_13012025_COMP_MPIO_2024_2025\Registros_2024_dic"
    ruta_resultados = r"C:\ACC\SCRIPT_13012025_COMP_MPIO_2024_2025\Script_Diferencias_Mpios_2024_2025"

    if not os.path.exists(ruta_resultados):
        os.makedirs(ruta_resultados)

    main(ruta_enero_2024, ruta_dic_2024, ruta_resultados)