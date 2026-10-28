"""The anonymiser agent and the gateway guardrail must agree on what personal data is, or a text anonymised by hand
keeps values the gateway would have masked."""

import re
from pathlib import Path

import pytest
import yaml

from swiss_ai_hub.core.generative_ai.anonymisation.anonymisation_vocabulary import AnonymisationVocabulary

REPO_ROOT = Path(__file__).resolve().parents[7]
GATEWAY_CONFIG = REPO_ROOT / "infra/configs/litellm/litellm-config.infomaniak.latest.yml"
GUARDRAIL = REPO_ROOT / "infra/deployment/templates/litellm_functions/pii_anonymisation_guardrail.py"


@pytest.fixture(scope="module")
def gateway_guardrail() -> dict:
    config = yaml.safe_load(GATEWAY_CONFIG.read_text(encoding="utf-8"))
    (guardrail,) = [entry for entry in config["guardrails"] if entry["guardrail_name"] == "pii-anonymisation"]
    return guardrail["litellm_params"]


def test_should_detect_the_entities_the_gateway_masks(gateway_guardrail: dict) -> None:
    assert list(AnonymisationVocabulary.ENTITIES) == list(gateway_guardrail["pii_entities_config"])


def test_should_allow_the_words_the_gateway_allows(gateway_guardrail: dict) -> None:
    assert list(AnonymisationVocabulary.ALLOW_LIST) == gateway_guardrail["pii_allow_list"]


def test_should_allow_the_same_numbered_labels_as_the_gateway() -> None:
    assert f'NUMBERED_LABEL_SUFFIX = r"{AnonymisationVocabulary.NUMBERED_LABEL_SUFFIX}"' in GUARDRAIL.read_text(
        encoding="utf-8"
    )


@pytest.mark.parametrize("span", ["Sie", "first name", "Position 2", "Art. 5", "numéro AVS", "AHV-Nr. 12a"])
def test_should_leave_labels_and_pronouns_unmasked(span: str) -> None:
    assert re.search(AnonymisationVocabulary.allow_list_pattern(), span, re.IGNORECASE | re.MULTILINE)


@pytest.mark.parametrize("span", ["Sie\nAnna Muster", "Anna Muster", "Position 12345", "Telefon 044 123 45 67"])
def test_should_mask_spans_that_only_start_with_an_allowed_word(span: str) -> None:
    assert not re.search(AnonymisationVocabulary.allow_list_pattern(), span, re.IGNORECASE | re.MULTILINE)
