import pytest
from pydantic import ValidationError

from app.schemas.state_transition import (
    EvidenceSupport,
    StateClaim,
    TransitionRecord,
    TransitionStatus,
)


VALID_CLAIM = {
    "claim_id": "claim-001",
    "side": "AS_IS",
    "statement": "Premium refunds above the threshold require administrator approval.",
    "baseline_id": "baseline-shop",
    "baseline_version": "v1",
    "support_status": "SUPPORTED",
    "evidence_refs": [{"evidence_id": "ev-001", "locator": "rules.md#refunds"}],
}

VALID_TRANSITION = {
    "transition_id": "transition-001",
    "change_request_id": "change-001",
    "baseline_id": "baseline-shop",
    "baseline_version": "v1",
    "as_is_claim_ids": ["claim-001"],
    "to_be_claim_ids": ["claim-002"],
    "status": "AMBIGUOUS_TRANSITION",
    "reason_codes": ["INTENT_UNCLEAR"],
}


def test_valid_supported_state_claim_fixture():
    claim = StateClaim.model_validate(VALID_CLAIM)

    assert claim.schema_version == "0.1.0"
    assert claim.evidence_refs[0].evidence_id == "ev-001"
    assert claim.support_status is EvidenceSupport.SUPPORTED


def test_insufficient_claim_may_have_no_evidence():
    claim = StateClaim.model_validate(
        {
            **VALID_CLAIM,
            "support_status": "INSUFFICIENT",
            "evidence_refs": [],
        }
    )

    assert claim.evidence_refs == []


@pytest.mark.parametrize("support_status", ["SUPPORTED", "CONTRADICTED"])
def test_supported_or_contradicted_claim_requires_evidence(support_status):
    with pytest.raises(ValidationError, match="must reference at least one evidence item"):
        StateClaim.model_validate(
            {**VALID_CLAIM, "support_status": support_status, "evidence_refs": []}
        )


def test_claim_rejects_unknown_fields():
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        StateClaim.model_validate({**VALID_CLAIM, "made_up_field": "ignored?"})


def test_claim_rejects_unknown_enum_value():
    with pytest.raises(ValidationError):
        StateClaim.model_validate({**VALID_CLAIM, "support_status": "MAYBE"})


def test_claim_rejects_duplicate_evidence_ids():
    with pytest.raises(ValidationError, match="duplicate evidence_id"):
        StateClaim.model_validate(
            {
                **VALID_CLAIM,
                "evidence_refs": [
                    {"evidence_id": "ev-001"},
                    {"evidence_id": "ev-001"},
                ],
            }
        )


def test_valid_transition_fixture():
    transition = TransitionRecord.model_validate(VALID_TRANSITION)

    assert transition.schema_version == "0.1.0"
    assert transition.status is TransitionStatus.AMBIGUOUS_TRANSITION
    assert transition.as_is_claim_ids == ["claim-001"]


def test_valid_transition_status_does_not_require_reason_code():
    transition = TransitionRecord.model_validate(
        {**VALID_TRANSITION, "status": "VALID", "reason_codes": []}
    )

    assert transition.status is TransitionStatus.VALID


def test_non_valid_transition_requires_reason_code():
    with pytest.raises(ValidationError, match="must include at least one reason_code"):
        TransitionRecord.model_validate({**VALID_TRANSITION, "reason_codes": []})


def test_transition_requires_at_least_one_claim_on_each_side():
    with pytest.raises(ValidationError):
        TransitionRecord.model_validate({**VALID_TRANSITION, "as_is_claim_ids": []})
    with pytest.raises(ValidationError):
        TransitionRecord.model_validate({**VALID_TRANSITION, "to_be_claim_ids": []})


def test_transition_claim_id_groups_must_be_disjoint():
    with pytest.raises(ValidationError, match="must be disjoint"):
        TransitionRecord.model_validate(
            {**VALID_TRANSITION, "to_be_claim_ids": ["claim-001"]}
        )


def test_transition_rejects_duplicate_claim_ids():
    with pytest.raises(ValidationError, match="must not contain duplicates"):
        TransitionRecord.model_validate(
            {**VALID_TRANSITION, "as_is_claim_ids": ["claim-001", "claim-001"]}
        )


def test_transition_rejects_unknown_status():
    with pytest.raises(ValidationError):
        TransitionRecord.model_validate({**VALID_TRANSITION, "status": "MAYBE"})
