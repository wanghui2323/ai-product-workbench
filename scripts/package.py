#!/usr/bin/env python3
"""Create a reproducible source/skill release ZIP and its SHA-256 checksum."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import stat
import sys
import zipfile

from install import REPO_ROOT, SOURCE, source_inventory, reject_symlink_components, ignored

VERSION = "0.2.0"
REPOSITORY = "https://github.com/wanghui2323/ai-product-workbench"
PUBLIC_DIRS = ("skills", "scripts", "tests", "examples", ".github", "docs")
PUBLIC_ROOT_FILES = ("README.md", "LICENSE", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md", ".gitignore", "VERSION")


def reject_sensitive_release_path(relative: Path) -> None:
    """Fail closed on secret-bearing paths, independently of .gitignore.

    .env.example is the sole env-file exception; its contents still require
    maintainer review to ensure that it contains placeholders only.
    """
    for part in relative.parts:
        name = part.casefold()
        if name in {"secrets", ".secrets"}:
            raise ValueError(f"Refusing a secrets path in the release: {relative}")
        if name != ".env.example" and (name == ".env" or name.startswith(".env.") or name.endswith(".env")):
            raise ValueError(f"Refusing an environment file in the release: {relative}")


def collect_files(root: Path) -> dict[str, bytes]:
    root = root.resolve()
    source_inventory(root / "skills" / "ai-dev-workbench")
    for name in ("README.md", "LICENSE"):
        if not (root / name).is_file():
            raise ValueError(f"Required release file is missing: {name}")
    paths = [root / name for name in PUBLIC_ROOT_FILES if (root / name).exists()]
    for name in PUBLIC_DIRS:
        directory = root / name
        if directory.exists():
            reject_symlink_components(directory)
            paths.extend(path for path in directory.rglob("*") if not path.is_dir() or path.is_symlink())
    result: dict[str, bytes] = {}
    for path in sorted(set(paths)):
        relative = path.relative_to(root)
        if any(ignored(Path(part)) or part == ".git" for part in relative.parts):
            continue
        reject_sensitive_release_path(relative)
        reject_symlink_components(path)
        if not stat.S_ISREG(path.stat().st_mode):
            raise ValueError(f"Non-regular release file: {relative}")
        result[relative.as_posix()] = path.read_bytes()
    return result


def release_bytes(root: Path, version: str = VERSION) -> bytes:
    import re
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?", version):
        raise ValueError("Version must look like 0.2.0 or 0.2.0-rc.1")
    files = collect_files(root)
    manifest = {
        "version": version, "repository": REPOSITORY, "license": "MIT", "skill": "ai-dev-workbench",
        "files": {name: hashlib.sha256(content).hexdigest() for name, content in sorted(files.items())},
    }
    files["RELEASE.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    prefix = f"ai-product-workbench-v{version}/"
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(prefix + name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return output.getvalue()


def write_once_or_identical(path: Path, content: bytes) -> None:
    reject_symlink_components(path)
    if path.exists():
        if path.is_file() and path.read_bytes() == content:
            return
        raise ValueError(f"Refusing to overwrite a different release artifact: {path}; use a clean output directory.")
    with path.open("xb") as handle:
        handle.write(content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "dist")
    parser.add_argument("--version", default=VERSION)
    args = parser.parse_args()
    try:
        content = release_bytes(REPO_ROOT, args.version)
        target = Path(args.output_dir).absolute()
        reject_symlink_components(target)
        target.mkdir(parents=True, exist_ok=True)
        name = f"ai-product-workbench-v{args.version}.zip"
        output = target / name
        checksum = hashlib.sha256(content).hexdigest()
        write_once_or_identical(output, content)
        write_once_or_identical(target / (name + ".sha256"), (checksum + "  " + name + "\n").encode("ascii"))
        print(output)
        print(f"SHA256 {checksum}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"Packaging not completed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
