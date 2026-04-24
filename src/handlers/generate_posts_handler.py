from repositories.template_repository import TemplateRepository

class GeneratePostsHandler:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    def handle(self, logo_path: str, template_path: str):
        return self.repository.generate_posts(logo_path, template_path, template_path)