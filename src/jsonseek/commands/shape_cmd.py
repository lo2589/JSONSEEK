import argparse
from typing import Any, Dict, List, Optional, Set

from ..detect import detect_file_kind
from ..io.json_file import load_json_file
from ..io.jsonl_file import load_jsonl_sample
from ..types import ShapeNode, NodeKind
from ..value_utils import infer_node_kind, stable_type_name
from ..formatters import format_shape_result
from ..errors import JsonseekError


def handle_shape(args: argparse.Namespace) -> int:
    try:
        kind = detect_file_kind(args.file, kind_hint=getattr(args, "kind", None))
        max_depth = getattr(args, "max_depth", None)
        array_mode = getattr(args, "array_mode", "sample")
        if kind == "jsonl":
            shape = build_shape_tree_from_jsonl(
                args.file,
                sample_size=getattr(args, "sample_size", 100),
                max_depth=max_depth,
                array_mode=array_mode,
            )
        else:
            data = load_json_file(args.file)
            shape = build_shape_tree(
                data,
                base_path="",
                max_depth=max_depth,
                array_mode=array_mode,
            )
        print(format_shape_result(shape, output=getattr(args, "output", "pretty")))
        return 0
    except JsonseekError as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return 1


def build_shape_tree(
    data: Any,
    *,
    base_path: str = "",
    max_depth: Optional[int] = None,
    array_mode: str = "sample",
) -> ShapeNode:
    node_kind = infer_node_kind(data)
    children: List[ShapeNode] = []

    if max_depth is not None and max_depth <= 0:
        pass
    elif isinstance(data, dict):
        for key, value in data.items():
            child_path = f"{base_path}.{key}" if base_path else key
            child = build_shape_tree(
                value,
                base_path=child_path,
                max_depth=max_depth - 1 if max_depth is not None else None,
                array_mode=array_mode,
            )
            children.append(child)
    elif isinstance(data, list):
        if array_mode == "sample" and data:
            sample = data[0]
            child_path = f"{base_path}[*]" if base_path else "[*]"
            child = build_shape_tree(
                sample,
                base_path=child_path,
                max_depth=max_depth - 1 if max_depth is not None else None,
                array_mode=array_mode,
            )
            child.count = len(data)
            types: Set[str] = set()
            for item in data[:20]:
                types.add(stable_type_name(item))
            child.sample_types = sorted(types)
            children.append(child)
        elif array_mode == "full":
            for idx, item in enumerate(data):
                child_path = f"{base_path}[{idx}]" if base_path else f"[{idx}]"
                child = build_shape_tree(
                    item,
                    base_path=child_path,
                    max_depth=max_depth - 1 if max_depth is not None else None,
                    array_mode=array_mode,
                )
                children.append(child)

    return ShapeNode(
        path=base_path,
        node_kind=node_kind,
        children=children,
    )


def build_shape_tree_from_jsonl(
    path: str,
    *,
    sample_size: int,
    max_depth: Optional[int],
    array_mode: str,
) -> ShapeNode:
    records = load_jsonl_sample(path, limit=sample_size)
    if not records:
        return ShapeNode(path="(root)", node_kind="array", children=[])

    # Merge shapes from sampled records
    root = ShapeNode(path="(root)", node_kind="array", children=[])
    # Collect all keys seen across records
    all_keys: Set[str] = set()
    key_types: Dict[str, Set[str]] = {}
    key_children: Dict[str, list] = {}

    for record in records:
        if not isinstance(record.data, dict):
            continue
        for key, value in record.data.items():
            all_keys.add(key)
            t = stable_type_name(value)
            key_types.setdefault(key, set()).add(t)
            # Build representative child shape from first occurrence
            if key not in key_children:
                child_path = key
                child = build_shape_tree(
                    value,
                    base_path=child_path,
                    max_depth=max_depth - 1 if max_depth is not None else None,
                    array_mode=array_mode,
                )
                key_children[key] = child

    for key in sorted(all_keys):
        child = key_children[key]
        child.sample_types = sorted(key_types[key])
        child.count = None
        root.children.append(child)

    return root
