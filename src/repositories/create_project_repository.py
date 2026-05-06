import subprocess
import os
import re
from pathlib import Path

class CreateProjectRepository:
    def create_project(self, script_path: str, activity_type: int, speakers: int, first_line: str, second_line: str, event_date: str):
        input_data = f"{activity_type}\n{speakers}\n{first_line}\n{second_line}\n{event_date}\n"
        
        script_path_resolved = os.path.abspath(os.path.expanduser(script_path))
        script_dir = os.path.dirname(script_path_resolved) or '.'

        try:
            result = subprocess.run(
                ["bash", script_path_resolved],
                input=input_data,
                text=True,
                capture_output=True,
                cwd=script_dir,
                check=True
            )
            
            print(f"Proyecto generado con éxito:\n{result.stdout}")

            match = re.search(r"Proyecto\s+([^\s]+)\s+creado", result.stdout)
            if match:
                template_dirname = match.group(1)
                project_dir = (Path(script_dir) / template_dirname).resolve()
                template_svg_path = project_dir / f"{template_dirname}.svg"
                generate_script_path = project_dir / "generate.sh"
                return {
                    "template_path": str(template_svg_path),
                    "generate_script_path": str(generate_script_path),
                }

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