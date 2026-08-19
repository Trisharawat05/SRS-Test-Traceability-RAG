from dataclasses import dataclass
from typing import Optional


@dataclass
class Requirement:
    id: str
    text: str
    title: Optional[str] = None
    source_file: Optional[str] = None
    source_location: Optional[str] = None


@dataclass
class TestCase:
    id: str
    title: str
    description: str = ""
    steps: str = ""
    expected_result: str = ""
    actual_result: Optional[str] = None
    status: Optional[str] = None
    source_file: Optional[str] = None
    source_location: Optional[str] = None