from dataclasses import dataclass
from typing import Any, List, Literal, Optional, Union

FileKind = Literal["json", "jsonl"]
NodeKind = Literal["object", "array", "string", "number", "boolean", "null"]
MatchType = Literal["key", "value"]


@dataclass(frozen=True)
class KeyToken:
    key: str


@dataclass(frozen=True)
class IndexToken:
    index: int


PathToken = Union[KeyToken, IndexToken]


@dataclass
class ShapeNode:
    path: str
    node_kind: NodeKind
    children: List["ShapeNode"]
    sample_types: Optional[List[str]] = None
    count: Optional[int] = None


@dataclass
class FieldStat:
    field: str
    paths: List[str]
    types: List[str]
    count: Optional[int] = None          # JSON 用
    record_count: Optional[int] = None   # JSONL 用
    coverage: Optional[float] = None     # JSONL 用


@dataclass
class QueryHit:
    path: str
    match_type: MatchType
    matched_on: str
    value: Any
    record_index: Optional[int] = None
    line_number: Optional[int] = None
    record_id: Optional[str] = None
    preview: Optional[str] = None


@dataclass
class JsonlRecord:
    record_index: int
    line_number: int
    data: Any


@dataclass
class PatchPlan:
    op: Literal["add", "append", "del", "set"]
    target_path: str
    value: Optional[Any] = None
    create_missing: bool = False
