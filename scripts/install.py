#!/usr/bin/env python3
"""Install the bundled skill without silently overwriting an existing installation.

Python 3.10+, standard library only. --dest is the complete skill directory.
The default destination is $CODEX_HOME/skills/ai-dev-workbench when CODEX_HOME is
set, otherwise ~/.codex/skills/ai-dev-workbench. Replacement backups live outside
the skill scan root, at <destination-parent-parent>/skill-backups/.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile
import uuid

SKILL_NAME = "ai-dev-workbench"
REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "skills" / SKILL_NAME
RELEASE_FILES = (
    "LICENSE",
    "SKILL.md",
    "agents/openai.yaml",
    "assets/example.json",
    "assets/workbench.html",
    "references/ai-product-method.md",
    "references/blueprint-contract.md",
    "references/data-contract.md",
    "references/discovery-contract.md",
    "references/governance-contract.md",
    "references/workbench-design.md",
    "scripts/test_workbench.py",
    "scripts/workbench.py",
)
IGNORED_NAMES = {"__pycache__", ".DS_Store", ".pytest_cache"}


class InstallError(ValueError):
    """An installation that must not proceed without changing its inputs."""


def absolute(path: Path) -> Path:
    """Normalize dots without following links we still need to inspect."""
    return Path(os.path.abspath(os.path.expanduser(str(path))))


def reject_symlink_components(path: Path) -> None:
    for item in reversed([path, *path.parents]):
        if item.is_symlink():
            raise InstallError(f"Refusing a symbolic-link path component: {item}")
        if item != path and item.exists() and not item.is_dir():
            raise InstallError(f"Parent path is not a directory: {item}")


def ignored(path: Path) -> bool:
    return path.name in IGNORED_NAMES or path.suffix in {".pyc", ".pyo"}


def inventory(directory: Path) -> dict[str, str]:
    """Hash all non-cache files, rejecting links and non-regular filesystem nodes."""
    reject_symlink_components(directory)
    if not directory.is_dir():
        raise InstallError(f"Not a directory: {directory}")
    result: dict[str, str] = {}
    for root, dirs, files in os.walk(directory, followlinks=False):
        base = Path(root)
        for name in dirs + files:
            path = base / name
            if path.is_symlink():
                raise InstallError(f"Refusing a symbolic link inside the skill: {path}")
        dirs[:] = sorted(name for name in dirs if not ignored(base / name))
        for name in sorted(files):
            path = base / name
            if ignored(path):
                continue
            if not stat.S_ISREG(path.stat().st_mode):
                raise InstallError(f"Refusing a non-regular file: {path}")
            result[path.relative_to(directory).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def source_inventory(source: Path) -> dict[str, str]:
    result = inventory(source)
    if set(result) != set(RELEASE_FILES):
        missing, extra = sorted(set(RELEASE_FILES) - set(result)), sorted(set(result) - set(RELEASE_FILES))
        raise InstallError(f"Bundled skill does not match the release manifest. Missing: {missing}; extra: {extra}")
    return result


def check_destination(source: Path, destination: Path) -> None:
    reject_symlink_components(destination)
    if source == destination or source.is_relative_to(destination) or destination.is_relative_to(source):
        raise InstallError("Source and destination must not be equal, nested, or ancestors of each other.")
    if destination in {Path(destination.anchor), Path.home().resolve()}:
        raise InstallError("Refusing to replace a filesystem root or home directory.")
    if destination.exists() and not destination.is_dir():
        raise InstallError(f"Destination exists and is not a directory: {destination}")


def is_existing_skill(destination: Path, existing: dict[str, str]) -> bool:
    if not existing:
        return True  # An empty destination is safe to back up with explicit replacement.
    entry = destination / "SKILL.md"
    if not entry.is_file():
        return False
    text = entry.read_text(encoding="utf-8")
    return bool(re.search(r"(?m)^name:\s*[\"']?ai-dev-workbench[\"']?\s*$", text))


def check_backup_directory(source: Path, destination: Path, directory: Path) -> None:
    reject_symlink_components(directory)
    for protected in (source, destination):
        if directory == protected or directory.is_relative_to(protected) or protected.is_relative_to(directory):
            raise InstallError("Backup directory and source or destination must not be equal, nested, or ancestors of each other.")
    if directory.exists() and not directory.is_dir():
        raise InstallError(f"Backup path is not a directory: {directory}")


def install(destination: Path, replace_with_backup: bool = False, source: Path = SOURCE) -> dict[str, str]:
    source, destination = absolute(source), absolute(destination)
    reject_symlink_components(source)
    check_destination(source, destination)
    wanted = source_inventory(source)
    existing = inventory(destination) if destination.exists() else None
    if existing == wanted:
        return {"status": "unchanged", "destination": str(destination)}
    if existing is not None and not replace_with_backup:
        raise InstallError("Destination differs. Nothing changed. Use --replace-with-backup to retain the old installation before replacing it.")
    if existing is not None and not is_existing_skill(destination, existing):
        raise InstallError("Destination is not an ai-dev-workbench installation. Refusing to replace an unrelated directory.")

    backup: Path | None = None
    if existing is not None:
        backup_directory = destination.parent.parent / "skill-backups"
        check_backup_directory(source, destination, backup_directory)
        backup_directory.mkdir(parents=True, exist_ok=True)
        check_backup_directory(source, destination, backup_directory)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = backup_directory / f"{destination.name}.backup-{stamp}-{uuid.uuid4().hex[:8]}"
        reject_symlink_components(backup)
        if backup.exists():
            raise InstallError(f"Backup already exists: {backup}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    reject_symlink_components(destination.parent)
    staging = Path(tempfile.mkdtemp(prefix=f".{SKILL_NAME}.staging-", dir=destination.parent))
    moved_old = False
    try:
        for name in RELEASE_FILES:
            path = source / name
            reject_symlink_components(path)
            content = path.read_bytes()
            if hashlib.sha256(content).hexdigest() != wanted[name]:
                raise InstallError(f"Source changed while installing: {name}")
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            target.chmod(0o644)
        if inventory(staging) != wanted:
            raise InstallError("Staging verification failed; the installed skill was left unchanged.")
        check_destination(source, destination)
        current = inventory(destination) if destination.exists() else None
        if current != existing:
            raise InstallError("Destination changed during installation; refusing to overwrite it.")
        if backup is not None:
            check_backup_directory(source, destination, backup.parent)
            reject_symlink_components(backup)
            if backup.exists():
                raise InstallError(f"Backup already exists: {backup}")
            destination.rename(backup)
            moved_old = True
        try:
            staging.rename(destination)
        except OSError:
            if moved_old and backup is not None and not destination.exists():
                backup.rename(destination)
                moved_old = False
            raise
        result = {"status": "replaced" if moved_old else "installed", "destination": str(destination)}
        if moved_old and backup is not None:
            result["backup"] = str(backup)
        return result
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    codex_directory = Path(os.environ["CODEX_HOME"]).expanduser() if os.environ.get("CODEX_HOME") else Path.home() / ".codex"
    parser.add_argument("--dest", type=Path, default=codex_directory / "skills" / SKILL_NAME,
                        help="Complete destination skill directory; not its parent.")
    parser.add_argument("--replace-with-backup", action="store_true",
                        help="Back up a differing existing skill before replacing it.")
    args = parser.parse_args()
    try:
        result = install(args.dest, args.replace_with_backup)
        print(f"{result['status']}: {result['destination']}")
        if "backup" in result:
            print(f"Previous installation preserved at: {result['backup']}")
        return 0
    except (OSError, UnicodeError, InstallError) as exc:
        print(f"Installation not completed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
