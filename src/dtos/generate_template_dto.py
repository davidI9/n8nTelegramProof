from dataclasses import dataclass
from datetime import date 

@dataclass(frozen=True)
class GenerateTemplateDTO:
    template_path: str
    activity_type: int
    speakers: int
    first_line: str
    second_line: str
    event_date: date