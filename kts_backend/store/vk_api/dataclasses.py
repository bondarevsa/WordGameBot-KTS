from dataclasses import dataclass
from typing import Optional


# Базовые структуры, для выполнения задания их достаточно,
# поэтому постарайтесь не менять их пожалуйста из-за возможных проблем с тестами
@dataclass
class Message:
    user_id: int
    text: Optional[str]
    peer_id: int
    keyboard: Optional[dict]


@dataclass
class UpdateMessage:
    from_id: int
    text: str
    payload: Optional[str]
    peer_id: int


@dataclass
class UpdateObject:
    message: UpdateMessage


@dataclass
class Update:
    type: str
    object: UpdateObject
