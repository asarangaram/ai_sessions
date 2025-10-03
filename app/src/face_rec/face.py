import base64
from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import List, Optional, Tuple

from pydantic import BaseModel, field_serializer
from sqlalchemy import Enum


class RecognitionStatus(StrEnum):
    UNCHECKED = auto()
    NOT_FOUND = auto()
    FOUND = auto()


class Face(BaseModel):
    bbox: Optional[Tuple[float, float, float, float]]
    landmarks: Optional[List[Tuple[float, float]]] = None
    status: str = field(default=RecognitionStatus.UNCHECKED)
    image: Optional[str] = None

    @field_serializer("bbox")
    def serialize_bbox(self, v: Optional[Tuple[float, float, float, float]], _info):
        if v is None:
            return None
        return [round(x, 2) for x in v]

    # Round landmarks floats to 2 decimals
    @field_serializer("landmarks")
    def serialize_landmarks(self, v: Optional[List[Tuple[float, float]]], _info):
        if v is None:
            return None
        return [[round(x, 2), round(y, 2)] for (x, y) in v]

    # Serialize status as plain string (short name only)
    @field_serializer("status")
    def serialize_status(self, v: RecognitionStatus, _info):
        return v.name


class DetectedFace(Face):
    pass


class UnknownFace(Face):
    def __post_init__(self):
        self.status = RecognitionStatus.NOT_FOUND


class RecognizedPerson(BaseModel):
    name: str
    confidence: float


class RegisteredPerson(BaseModel):
    id: int
    name: str
    keyFaceId: Optional[str]
    isHidden: int
    faces: List[str]


class RegisteredFace(BaseModel):
    id: str
    personId: int
    personName: str
