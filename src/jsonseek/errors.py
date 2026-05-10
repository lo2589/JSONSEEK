class JsonseekError(Exception):
    """Base exception for jsonseek."""
    pass


class PathError(JsonseekError):
    """Invalid path syntax or resolution failure."""
    pass


class FileKindError(JsonseekError):
    """Unsupported or undetectable file kind."""
    pass


class PatchError(JsonseekError):
    """Patch operation cannot be applied."""
    pass


class RecordNotFoundError(JsonseekError):
    """JSONL record index out of range or not found."""
    pass
