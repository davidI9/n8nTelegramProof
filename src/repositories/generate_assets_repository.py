import subprocess
from pathlib import Path


class GenerateAssetsRepository:
    def execute_generate_script(self, generate_script_path: str) -> bool:
        script_path = Path(generate_script_path).expanduser().resolve()

        if not script_path.is_file():
            raise FileNotFoundError(f"No existe el script de generación: {script_path}")

        try:
            result = subprocess.run(
                ["bash", str(script_path)],
                text=True,
                capture_output=True,
                cwd=str(script_path.parent),
                check=True,
            )
            print(f"Assets generados correctamente:\n{result.stdout}")
            return True
        except subprocess.CalledProcessError as error:
            print(f"Error ejecutando generate.sh (código {error.returncode}).")
            print(f"Salida estándar:\n{error.stdout}")
            print(f"Error estándar:\n{error.stderr}")
            return False
