import subprocess
import os

class CreateProjectRepository:
    def create_project(self, script_path: str, activity_type: int, speakers: int, first_line: str, second_line: str, event_date: str):
        # 1. Preparamos las respuestas simulando lo que escribiría el usuario,
        # separadas por saltos de línea (\n) para simular la tecla "Enter".
        input_data = f"{activity_type}\n{speakers}\n{first_line}\n{second_line}\n{event_date}\n"
        
        # 2. IMPORTANTE: Tu script de bash usa rutas relativas como "plantillas/...".
        # Si ejecutas el script desde otro lugar, fallará al no encontrar esa carpeta.
        # Por seguridad, extraemos el directorio donde vive el script para ejecutarlo desde allí.
        script_dir = os.path.dirname(script_path) or '.'

        try:
            # 3. Ejecutamos el script inyectando los datos por stdin
            result = subprocess.run(
                ["bash", script_path],  # Comando a ejecutar
                input=input_data,       # Pasamos el string con todas las respuestas
                text=True,              # Para que input y stdout sean strings, no bytes
                capture_output=True,    # Capturamos lo que imprime el script
                cwd=script_dir,         # Ejecutamos en el directorio del script
                check=True              # Lanza CalledProcessError si el script falla (exit != 0)
            )
            
            print(f"Proyecto generado con éxito:\n{result.stdout}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"El script falló con el código {e.returncode}.")
            print(f"Salida estándar:\n{e.stdout}")
            print(f"Error estándar:\n{e.stderr}")
            return False
        except FileNotFoundError:
            print(f"No se encontró el script en la ruta: {script_path}")
            return False