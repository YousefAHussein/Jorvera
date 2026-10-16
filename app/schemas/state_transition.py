

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


SchemaVersion = Literal["0.1.0"]


class StrictSchema(BaseModel):
    """Base contract: reject undeclared fields instead of silently dropping them."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ClaimSide(StrEnum):
    AS_IS = "AS_IS"
    TO_BE = "TO_BE"


class EvidenceSupport(StrEnum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT = "INSUFFICIENT"


class TransitionStatus(StrEnum):
    VALID = "VALID"
    INVALID_CONFLICT = "INVALID_CONFLICT"
    INVALID_VERSION = "INVALID_VERSION"
    REQUIRES_SUPERSESSION = "REQUIRES_SUPERSESSION"
    REQUIRES_EXCEPTION_APPROVAL = "REQUIRES_EXCEPTION_APPROVAL"
    AMBIGUOUS_TRANSITION = "AMBIGUOUS_TRANSITION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class EvidenceReference(StrictSchema):
    """Reference to an immutable evidence item; content/provenance live at source."""

    evidence_id: str = Field(min_length=1, description="Stable ID of the evidence item")
    locator: str | None = Field(
        default=None,
        min_length=1,
        description="Optional locator within the source, such as page/section/segment",
    )

    @field_validator("evidence_id", "locator")
    @classmethod
    def reject_whitespace_only(cls, value: str | None) -> str | None:
        if value is not None and not value:
            raise ValueError("must not be empty or whitespace-only")
        return value


class StateClaim(StrictSchema):
    """An atomic assertion about the product in the current or proposed state."""

    schema_version: SchemaVersion = "0.1.0"
    claim_id: str = Field(min_length=1, description="Stable, unique claim ID")
    side: ClaimSide
    statement: str = Field(min_length=1, description="One atomic product-state assertion")
    baseline_id: str = Field(min_length=1, description="Approved baseline identifier")
    baseline_version: str = Field(min_length=1, description="Frozen baseline version")
    support_status: EvidenceSupport
    evidence_refs: list[EvidenceReference] = Field(default_factory=list)

    @field_validator("claim_id", "statement", "baseline_id", "baseline_version")
    @classmethod
    def reject_whitespace_only(cls, value: str) -> str:
        if not value:
            raise ValueError("must not be empty or whitespace-only")
        return value

    @model_validator(mode="after")
    def validate_evidence_support(self) -> "StateClaim":
        evidence_ids = [ref.evidence_id for ref in self.evidence_refs]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("evidence_refs must not contain duplicate evidence_id values")
        if self.support_status in {EvidenceSupport.SUPPORTED, EvidenceSupport.CONTRADICTED} and not evidence_ids:
            raise ValueError(
                "SUPPORTED and CONTRADICTED claims must reference at least one evidence item"
            )
        return self


class TransitionRecord(StrictSchema):
    """A proposed/assessed transition from AS-IS claims to TO-BE claims."""

    schema_version: SchemaVersion = "0.1.0"
    transition_id: str = Field(min_length=1, description="Stable, unique transition ID")
    change_request_id: str = Field(min_length=1, description="ID of the initiating change request")
    baseline_id: str = Field(min_length=1, description="Approved baseline identifier")
    baseline_version: str = Field(min_length=1, description="Frozen baseline version used")
    as_is_claim_ids: list[str] = Field(min_length=1, description="Claim IDs describing current state")
    to_be_claim_ids: list[str] = Field(min_length=1, description="Claim IDs describing target state")
    status: TransitionStatus
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Machine-readable explanations for a non-VALID status",
    )

    @field_validator(
        "transition_id", "change_request_id", "baseline_id", "baseline_version"
    )
    @classmethod
    def reject_whitespace_only(cls, value: str) -> str:
        if not value:
            raise ValueError("must not be empty or whitespace-only")
        return value

    @field_validator("as_is_claim_ids", "to_be_claim_ids", "reason_codes")
    @classmethod
    def validate_string_lists(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("list values must not be empty or whitespace-only")
        return [value.strip() for value in values]

    @model_validator(mode="after")
    def validate_transition_links(self) -> "TransitionRecord":
        if len(self.as_is_claim_ids) != len(set(self.as_is_claim_ids)):
            raise ValueError("as_is_claim_ids must not contain duplicates")
        if len(self.to_be_claim_ids) != len(set(self.to_be_claim_ids)):
            raise ValueError("to_be_claim_ids must not contain duplicates")
        if set(self.as_is_claim_ids) & set(self.to_be_claim_ids):
            raise ValueError("AS-IS and TO-BE claim IDs must be disjoint")
        if self.status is not TransitionStatus.VALID and not self.reason_codes:
            raise ValueError("non-VALID transitions must include at least one reason_code")
        return self
