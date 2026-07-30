"""Configuration models for scenario-driven email workflows."""

from dataclasses import dataclass


SUPPORTED_FIELD_TYPES = {"text", "textarea"}


@dataclass(frozen=True)
class ScenarioField:
    key: str
    label_zh: str
    label_en: str
    field_type: str = "text"
    required: bool = False
    placeholder: str = ""
    help_text: str = ""
    max_length: int = 600

    def __post_init__(self) -> None:
        if not self.key or not self.key.replace("_", "").isalnum():
            raise ValueError("Scenario field key must be alphanumeric snake_case")
        if self.field_type not in SUPPORTED_FIELD_TYPES:
            raise ValueError(f"Unsupported field type: {self.field_type}")
        if self.max_length <= 0:
            raise ValueError("Scenario field max_length must be positive")


@dataclass(frozen=True)
class Scenario:
    id: str
    title_zh: str
    title_en: str
    description: str
    fields: tuple[ScenarioField, ...]
    default_tone: str
    risk_policy: str
    prompt_policy: str

    def __post_init__(self) -> None:
        if not self.id or not self.fields:
            raise ValueError("Scenario id and fields are required")
        field_keys = [field.key for field in self.fields]
        if len(field_keys) != len(set(field_keys)):
            raise ValueError(f"Duplicate field key in scenario {self.id}")
        if "supplier_name" not in field_keys:
            raise ValueError("Supplier scenarios require supplier_name")
        supplier_field = next(
            field for field in self.fields if field.key == "supplier_name"
        )
        if not supplier_field.required:
            raise ValueError("Supplier name must be required")

    @property
    def required_fields(self) -> tuple[ScenarioField, ...]:
        return tuple(field for field in self.fields if field.required)
