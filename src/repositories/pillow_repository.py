class PillowRepository:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def generate_post(self, logo_path: str):
        # Aquí iría la lógica para generar una publicación usando Pillow
        print(f"Generando una publicación con el logo en: {logo_path}")