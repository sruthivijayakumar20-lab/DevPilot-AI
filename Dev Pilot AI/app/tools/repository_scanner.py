
from pathlib import Path
from collections import Counter
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = PROJECT_ROOT / "workspace"

IGNORED_DIRS = {
    ".git", ".venv", "venv", "env",
    "node_modules", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "dist", "build",
    ".next", "coverage", ".idea", ".vscode"
}

IGNORED_FILES = {
    ".env", ".env.local", ".env.production",
    "id_rsa", "id_ed25519"
}

MANIFEST_FILES = {
    "requirements.txt", "pyproject.toml", "Pipfile",
    "package.json", "pom.xml", "build.gradle",
    "Cargo.toml", "go.mod", "composer.json",
    "Gemfile", "Dockerfile", "README.md"
}

ENTRYPOINT_CANDIDATES = {
    "main.py", "app.py", "server.py", "manage.py",
    "main.js", "index.js", "server.js", "index.ts",
    "main.ts", "Program.cs", "Main.java"
}

EXTENSION_LANGUAGES = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "React JSX",
    ".tsx": "React TSX",
    ".java": "Java",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".cpp": "C++",
    ".c": "C",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".ipynb": "Jupyter Notebook"
}


def scan_repository(root: Path = WORKSPACE) -> dict:
    root = root.resolve()

    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Workspace not found: {root}")

    file_count = 0
    file_paths = []
    language_counts = Counter()
    entry_points = []
    manifests = []
    framework_hints = set()

    max_files = 5000
    max_depth = 8
    max_display_paths = 100

    for current_dir, dirs, files in __import__("os").walk(root):
        current_path = Path(current_dir)

        # Ignore generated and dependency folders.
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS)

        depth = len(current_path.relative_to(root).parts)
        if depth >= max_depth:
            dirs[:] = []

        for filename in sorted(files):
            if filename in IGNORED_FILES or filename.startswith(".env"):
                continue

            file_path = current_path / filename

            if file_path.is_symlink():
                continue

            file_count += 1
            relative_path = file_path.relative_to(root).as_posix()

            if len(file_paths) < max_display_paths:
                file_paths.append(relative_path)

            language = EXTENSION_LANGUAGES.get(file_path.suffix.lower())
            if language:
                language_counts[language] += 1

            if filename in ENTRYPOINT_CANDIDATES:
                entry_points.append(relative_path)

            if filename in MANIFEST_FILES:
                manifests.append(relative_path)

            if file_count >= max_files:
                break

        if file_count >= max_files:
            break

    # Inspect only selected, non-secret configuration files.
    for relative_path in manifests:
        path = root / relative_path

        try:
            if path.stat().st_size > 30_000:
                continue

            content = path.read_text(
                encoding="utf-8",
                errors="ignore"
            ).lower()

            checks = {
                "FastAPI": ["fastapi"],
                "Django": ["django"],
                "Flask": ["flask"],
                "Streamlit": ["streamlit"],
                "LangChain": ["langchain"],
                "React": ['"react"'],
                "Next.js": ['"next"'],
                "Express": ["express"],
                "Spring Boot": ["spring-boot"],
                "Docker": ["from ", "dockerfile"]
            }

            for framework, keywords in checks.items():
                if any(keyword in content for keyword in keywords):
                    framework_hints.add(framework)

        except (OSError, UnicodeError):
            continue

    return {
        "repository_root": str(root),
        "total_files_scanned": file_count,
        "file_listing_truncated": file_count > max_display_paths,
        "languages": dict(language_counts.most_common()),
        "framework_hints": sorted(framework_hints),
        "entry_point_candidates": sorted(set(entry_points))[:30],
        "configuration_files": sorted(set(manifests))[:50],
        "sample_file_paths": file_paths
    }

def scan_workspace() -> dict:
    """
    Scan the configured workspace and return repository metadata.

    Returns:
        A dictionary containing file counts, languages,
        framework hints, entry points and configuration files.
    """
    return scan_repository()

if __name__ == "__main__":
    result = scan_repository()
    print(json.dumps(result, indent=2))
