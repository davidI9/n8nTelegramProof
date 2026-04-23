from ..dtos.generate_template_dto import GenerateTemplateDTO
from ..repositories.create_project_repository import CreateProjectRepository

class GenerateTemplateHandler:
    def __init__(self, repository: CreateProjectRepository):
        self.repository = repository

    def handle(self, dto: GenerateTemplateDTO):
        return self.repository.create_project(
            script_path=dto.script_path,
            activity_type=dto.activity_type,
            speakers=dto.speakers,
            first_line=dto.first_line,
            second_line=dto.second_line,
            event_date=dto.event_date
        )