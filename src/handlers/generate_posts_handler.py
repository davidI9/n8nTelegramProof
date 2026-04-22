from ..repositories.pillow_repository import PillowRepository

class GeneratePostsHandler:
    def __init__(self, repository: PillowRepository):
        self.repository = repository

    def handle(self, logo_path: str):
        return self.repository.generate_posts_from_template(logo_path)