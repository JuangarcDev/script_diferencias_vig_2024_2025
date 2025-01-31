import os

def extraer_ultimos_caracteres(carpeta):
    try:
        # Verifica que la carpeta exista
        if not os.path.exists(carpeta):
            print(f"La carpeta {carpeta} no existe.")
            return

        # Lista todos los archivos en la carpeta
        archivos = os.listdir(carpeta)

        # Itera sobre los archivos
        for archivo in archivos:
            # Separa el nombre del archivo de su extensión
            nombre, extension = os.path.splitext(archivo)

            # Verifica que sea un archivo y no un directorio
            if os.path.isfile(os.path.join(carpeta, archivo)):
                # Extrae los últimos 5 caracteres del nombre
                ultimos_5 = nombre[-5:]
                print(f"{ultimos_5}")
    except Exception as e:
        print(f"Ocurrió un error: {e}")

# Ruta de la carpeta específica
carpeta_especifica = r"C:\ACC\SCRIPT_13012025_COMP_MPIO_2024_2025\Municipios_Aprobados"  # Cambia esta ruta por la de tu carpeta
extraer_ultimos_caracteres(carpeta_especifica)