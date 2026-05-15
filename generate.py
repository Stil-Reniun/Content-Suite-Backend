import os

RUTA_PROYECTO = r"C:\Users\Zuth\Desktop\Reto Técnico_Developer Gen AI Analyst Jr_Juan Solis\Backend"
ARCHIVO_SALIDA = r"C:\Users\Zuth\Desktop\Reto Técnico_Developer Gen AI Analyst Jr_Juan Solis\Backend\Fuentes_de_codigo.mm.md"

def leer_archivos_python(ruta_proyecto, archivo_salida):
    # Scan the project directory and concatenate all Python files into a single reference document.
    with open(archivo_salida, "w", encoding="utf-8") as salida:

        for root, dirs, files in os.walk(ruta_proyecto):

            dirs[:] = [
                d for d in dirs
                if d not in [
                    "__pycache__",
                    ".git",
                    ".venv",
                    "venv",
                    "node_modules"
                    ".qodo"
                ]
            ]

            for file in files:

                if file.endswith(".py"):

                    ruta_completa = os.path.join(root, file)

                    try:

                        with open(ruta_completa, "r", encoding="utf-8") as f:
                            contenido = f.read()

                        salida.write("\n")
                        salida.write("=" * 100 + "\n")
                        salida.write(f"ARCHIVO: {file}\n")
                        salida.write(f"RUTA: {ruta_completa}\n")
                        salida.write("=" * 100 + "\n\n")

                        salida.write(contenido)
                        salida.write("\n\n")
                        salida.write("-" * 60 + "\n\n")

                        print(f"Procesado: {ruta_completa}")

                    except Exception as e:
                        print(f"ERROR leyendo {ruta_completa}: {e}")

    print(f"\nArchivo generado: {archivo_salida}")

leer_archivos_python(RUTA_PROYECTO, ARCHIVO_SALIDA)
