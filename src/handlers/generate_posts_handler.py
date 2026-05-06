from repositories.template_repository import TemplateRepository
from repositories.generate_assets_repository import GenerateAssetsRepository

class GeneratePostsHandler:
    def __init__(self, template_repository: TemplateRepository, assets_repository: GenerateAssetsRepository):
        self.template_repository = template_repository
        self.assets_repository = assets_repository

    def handle(self, logo_path: str, template_path: str, generate_script_path: str):
        self.template_repository.generate_posts(logo_path, template_path, template_path)
        return self.assets_repository.execute_generate_script(generate_script_path)