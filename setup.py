from setuptools import setup, find_packages

setup(
    name="jsonseek",
    version="0.1.4",  # primary source of truth is pyproject.toml; keep aligned
    description="Query and patch JSON/JSONL files from the command line",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "jsonseek=jsonseek.cli:main",
        ],
    },
)