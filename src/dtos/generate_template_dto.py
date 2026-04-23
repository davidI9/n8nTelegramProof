from dataclasses import dataclass
from datetime import date 

@dataclass(frozen=True)
class GenerateTemplateDTO:
    script_path: str
    activity_type: int
    speakers: int
    first_line: str
    second_line: str
    event_date: str