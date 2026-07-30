"""Local decision models for the Phase 3B reply workflow."""

from dataclasses import asdict, dataclass
from typing import Any


STANCES = (
    "accept",
    "partial",
    "decline",
    "request_info",
    "unable_to_confirm",
    "no_response",
    "custom",
)


@dataclass(frozen=True)
class ReplyItem:
    item_id: str
    item_type: str
    description: str
    deadline: str | None
    required: bool
    source_request_id: str | None
    source_question_ids: tuple[str, ...]
    uncertain: bool


@dataclass(frozen=True)
class ReplyDecision:
    item_id: str
    stance: str
    confirmed_facts: str = ""
    accepted_part: str = ""
    declined_part: str = ""
    reason: str = ""
    alternative: str = ""
    requested_information: str = ""
    next_update_time: str = ""
    custom_instruction: str = ""
    include_in_reply: bool = True
    user_notes: str = ""
    uncertain: bool = False
    no_response_confirmed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReplyDecision":
        fields = cls.__dataclass_fields__
        return cls(**{key: data[key] for key in fields if key in data})


@dataclass(frozen=True)
class DecisionValidation:
    valid: bool
    errors: tuple[str, ...]


@dataclass(frozen=True)
class DecisionSummary:
    decided: tuple[ReplyItem, ...]
    excluded: tuple[ReplyItem, ...]
    skipped_optional: tuple[ReplyItem, ...]
    undecided: tuple[ReplyItem, ...]
    ready: bool

