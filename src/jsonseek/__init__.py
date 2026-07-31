"""jsonseek - Query and patch JSON/JSONL files from the command line."""

from importlib.metadata import version as _vmd, PackageNotFoundError

try:
    __version__: str = _vmd("jsonseek")
except PackageNotFoundError:
    # package not installed (e.g. running from source tree without `pip install -e .`)
    __version__ = "0.0.0+local"