import subprocess
import os
import re
from pathlib import Path

class CreateProjectRepository:
    def create_project(self, script_path: str, activity_type: int, speakers: int, first_line: str, second_line: str, event_date: str):
        # 1. Preparamos las respuestas simulando lo que escribiría el usuario,
        # separadas por saltos de línea (\n) para simular la tecla "Enter".
        input_data = f"{activity_type}\n{speakers}\n{first_line}\n{second_line}\n{event_date}\n"
        
        # 2. IMPORTANTE: Tu script de bash usa rutas relativas como "plantillas/...".
        # Si ejecutas el script desde otro lugar, fallará al no encontrar esa carpeta.
        # Por seguridad, extraemos el directorio donde vive el script para ejecutarlo desde allí.
        script_path_resolved = os.path.abspath(os.path.expanduser(script_path))
        script_dir = os.path.dirname(script_path_resolved) or '.'

        try:
            # 3. Ejecutamos el script inyectando los datos por stdin
            result = subprocess.run(
                ["bash", script_path_resolved],  # Comando a ejecutar
                input=input_data,       # Pasamos el string con todas las respuestas
                text=True,              # Para que input y stdout sean strings, no bytes
                capture_output=True,    # Capturamos lo que imprime el script
                cwd=script_dir,         # Ejecutamos en el directorio del script
                check=True              # Lanza CalledProcessError si el script falla (exit != 0)
            )
            
            print(f"Proyecto generado con éxito:\n{result.stdout}")

            # El script imprime: "Proyecto <dirname> creado"
            match = re.search(r"Proyecto\s+([^\s]+)\s+creado", result.stdout)
            if match:
                template_dirname = match.group(1)
                template_svg_path = Path(script_dir) / template_dirname / f"{template_dirname}.svg"
                return str(template_svg_path.resolve())

            raise RuntimeError("No se pudo determinar el directorio de plantilla generado por el script.")
            
        except subprocess.CalledProcessError as e:
            print(f"El script falló con el código {e.returncode}.")
            print(f"Salida estándar:\n{e.stdout}")
            print(f"Error estándar:\n{e.stderr}")
            return False
        except FileNotFoundError:
            print(f"No se encontró el script en la ruta: {script_path_resolved}")
            return False
        except RuntimeError as e:
            print(str(e))
            return False