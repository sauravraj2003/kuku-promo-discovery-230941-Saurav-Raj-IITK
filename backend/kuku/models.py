from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Diagnostic(Record):
    severity: Literal["error", "warning", "info"]
    code: str
    line: int
    detail: str
    entry_ids: list[str] = Field(default_factory=list)


class Scene(Record):
    id: str
    number: int
    source_line: int
    heading: str
    start_cs: int
    end_cs: int


class Entry(Record):
    id: str
    episode: int
    scene_id: str
    source_order: int
    source_line: int
    source_end_line: int
    kind: Literal["camera", "dialogue", "action", "sound_fx"]
    raw_label: str
    speaker: str | None
    delivery: list[str]
    text: str
    raw_block: str
    start_cs: int
    end_cs: int
    start_text: str
    end_text: str


class Episode(Record):
    number: int
    source_file: str
    source_sha256: str
    parser_version: str
    raw_text: str
    logline: str
    continuity: str
    duration_cs: int
    scenes: list[Scene]
    entries: list[Entry]
    diagnostics: list[Diagnostic]


class Annotation(Record):
    entry_id: str
    roles: list[Literal["hook", "cliffhanger", "conflict", "reveal"]] = Field(min_length=1)
    evidence: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    unresolved_question: str | None = None


class AnnotationBatch(Record):
    annotations: list[Annotation]


class Segment(Record):
    episode: StrictInt
    start_cs: StrictInt
    end_cs: StrictInt
    source_sha256: str | None = None
    source_file: str | None = None
    start_text: str | None = None
    end_text: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class ValidateRequest(Record):
    segments: list[Segment]
    max_segments: StrictInt = Field(default=3, ge=1, le=20)


class DiscoveryConfig(Record):
    min_duration_cs: StrictInt = Field(default=2000, ge=2000, le=6000)
    max_duration_cs: StrictInt = Field(default=6000, ge=2000, le=6000)
    hook_lead_cs: StrictInt = Field(default=300, ge=0, le=300)
    ending_tail_cs: StrictInt = Field(default=300, ge=0, le=500)

    @model_validator(mode="after")
    def check_range(self):
        if self.min_duration_cs > self.max_duration_cs:
            raise ValueError("Minimum duration exceeds maximum")
        return self


class Candidate(Record):
    id: str
    variant_group: str
    status: Literal["needs_review"] = "needs_review"
    episode: int
    segments: list[Segment]
    duration_cs: int
    approaches: list[str]
    hook_ids: list[str]
    cliffhanger_ids: list[str]
    seed_ids: list[str]
    hook_timing: Literal["supported_by_script", "uncertain", "not_anchored"]
    annotation_provider: str
    risks: list[str]
    media_verified: bool = False
