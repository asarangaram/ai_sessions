from enum import auto

from dataclasses import dataclass
from typing import Optional, Tuple
from sqlalchemy import Enum


class RecognitionStatus(Enum):
    UNCHECKED = auto()
    NOT_FOUND = auto()
    FOUND = auto()


@dataclass(kw_only=True)
class Face:
    bbox: Optional[Tuple[int, int, int, int]]
    status: str = RecognitionStatus.UNCHECKED


@dataclass(kw_only=True)
class DetectedFace(Face):
    pass


@dataclass(kw_only=True)
class UnknownFace(Face):
    def __post_init__(self):
        self.status = RecognitionStatus.NOT_FOUND


@dataclass(kw_only=True)
class KnownFace(Face):
    face_id: str
    person_id: int
    person_name: str
    confidence: float

    def __post_init__(self):
        self.status = RecognitionStatus.FOUND


@dataclass
class RegisteredPerson:
    id: int
    name: str
    key_face_id: int


@dataclass
class RegisteredFace:
    id: str
    person_id: int
    person_name: str