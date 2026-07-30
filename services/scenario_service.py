"""Validation and generation orchestration for configured email scenarios."""

from dataclasses import dataclass
from typing import Mapping, Protocol

from ai_service import EmailResult, SenderDetails
from models.scenario import Scenario


class ScenarioEmailBackend(Protocol):
    def generate_scenario_email(
        self,
        *,
        scenario_id: str,
        scenario_title: str,
        facts: Mapping[str, str],
        tone: str,
        sender: SenderDetails,
        recipient: str = "",
        country_region: str = "",
        localization_context: str = "",
    ) -> EmailResult: ...


@dataclass(frozen=True)
class ScenarioValidation:
    cleaned_facts: dict[str, str]
    errors: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_scenario_facts(
    scenario: Scenario,
    facts: Mapping[str, str],
) -> ScenarioValidation:
    cleaned: dict[str, str] = {}
    errors: list[str] = []
    for field in scenario.fields:
        value = str(facts.get(field.key, "")).strip()
        if field.required and not value:
            errors.append(f"请填写{field.label_zh}。")
        elif len(value) > field.max_length:
            errors.append(
                f"{field.label_zh}不能超过 {field.max_length} 个字符。"
            )
        if value:
            cleaned[field.key] = value
    return ScenarioValidation(cleaned_facts=cleaned, errors=tuple(errors))


class ScenarioService:
    def __init__(self, backend: ScenarioEmailBackend) -> None:
        self._backend = backend

    def generate(
        self,
        *,
        scenario: Scenario,
        facts: Mapping[str, str],
        tone: str,
        sender: SenderDetails,
        recipient: str = "",
        country_region: str = "",
        localization_context: str = "",
    ) -> EmailResult:
        validation = validate_scenario_facts(scenario, facts)
        if not validation.is_valid:
            raise ValueError(validation.errors[0])
        return self._backend.generate_scenario_email(
            scenario_id=scenario.id,
            scenario_title=f"{scenario.title_zh} / {scenario.title_en}",
            facts=validation.cleaned_facts,
            tone=tone,
            sender=sender,
            recipient=recipient.strip(),
            country_region=country_region.strip(),
            localization_context=localization_context.strip(),
        )
