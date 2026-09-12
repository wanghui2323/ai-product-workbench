"""Release/install regressions; all writes are confined to TemporaryDirectory."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import install as installer
import package as pack


class InstallerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="ai-workbench-install-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / "source"
        shutil.copytree(installer.SOURCE, self.source, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.dest = self.root / "target" / installer.SKILL_NAME

    def install(self, replace=False):
        return installer.install(self.dest, replace_with_backup=replace, source=self.source)

    def test_fresh_install_contains_exact_release_files(self):
        result = self.install()
        self.assertEqual(result["status"], "installed")
        self.assertEqual(installer.inventory(self.dest), installer.source_inventory(self.source))
        self.assertEqual(len(installer.inventory(self.dest)), 13)

    def test_standalone_install_preserves_the_full_repository_mit_license(self):
        self.install()
        license_text = (self.dest / "LICENSE").read_bytes()
        self.assertEqual(license_text, (ROOT / "LICENSE").read_bytes())
        self.assertIn(b"Permission is hereby granted, free of charge", license_text)
        self.assertIn(b"THE SOFTWARE IS PROVIDED", license_text)

    def test_identical_install_is_a_noop_including_inode_and_mtime(self):
        self.install()
        before = (self.dest / "SKILL.md").stat()
        self.assertEqual(self.install()["status"], "unchanged")
        after = (self.dest / "SKILL.md").stat()
        self.assertEqual((before.st_ino, before.st_mtime_ns), (after.st_ino, after.st_mtime_ns))
        self.assertFalse(list((self.dest.parent.parent / "skill-backups").glob("*.backup-*")))

    def test_runtime_caches_are_neither_distributed_nor_a_reason_to_replace(self):
        cache = self.source / "scripts/__pycache__"
        cache.mkdir()
        (cache / "example.pyc").write_bytes(b"cache")
        self.install()
        self.assertFalse((self.dest / "scripts/__pycache__").exists())
        target_cache = self.dest / "scripts/__pycache__"
        target_cache.mkdir()
        (target_cache / "local.pyc").write_bytes(b"local cache")
        self.assertEqual(self.install()["status"], "unchanged")
        self.assertEqual((target_cache / "local.pyc").read_bytes(), b"local cache")

    def test_differing_install_refuses_and_preserves_every_old_file(self):
        self.install()
        (self.dest / "SKILL.md").write_text("local edit", encoding="utf-8")
        before = installer.inventory(self.dest)
        with self.assertRaisesRegex(installer.InstallError, "differs"):
            self.install()
        self.assertEqual(installer.inventory(self.dest), before)
        self.assertFalse(list((self.dest.parent.parent / "skill-backups").glob("*.backup-*")))

    def test_explicit_replacement_keeps_complete_backup_with_user_additions(self):
        self.install()
        (self.dest / "local-notes.txt").write_text("keep my notes", encoding="utf-8")
        old = installer.inventory(self.dest)
        result = self.install(replace=True)
        self.assertEqual(result["status"], "replaced")
        backup = Path(result["backup"])
        self.assertEqual(installer.inventory(backup), old)
        self.assertEqual(backup.parent, self.dest.parent.parent / "skill-backups")
        self.assertEqual(list(self.dest.parent.rglob("SKILL.md")), [self.dest / "SKILL.md"])
        self.assertEqual(installer.inventory(self.dest), installer.source_inventory(self.source))

    def test_backup_directory_symlink_is_refused_before_moving_old_installation(self):
        self.install()
        (self.dest / "local-notes.txt").write_text("keep", encoding="utf-8")
        old = installer.inventory(self.dest)
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / "skill-backups").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(installer.InstallError, "symbolic-link"):
            self.install(replace=True)
        self.assertEqual(installer.inventory(self.dest), old)
        self.assertEqual(list(outside.iterdir()), [])

    def test_backup_directory_overlapping_source_is_refused(self):
        for name, nested in (("equal", False), ("inside", True)):
            with self.subTest(name=name):
                case = self.root / name
                backup_root = case / "skill-backups"
                source = backup_root / "source" if nested else backup_root
                shutil.copytree(self.source, source)
                destination = case / "skills" / installer.SKILL_NAME
                installer.install(destination, source=source)
                (destination / "local-notes.txt").write_text("keep", encoding="utf-8")
                old = installer.inventory(destination)
                with self.assertRaisesRegex(installer.InstallError, "Backup directory.*nested"):
                    installer.install(destination, replace_with_backup=True, source=source)
                self.assertEqual(installer.inventory(destination), old)
                self.assertEqual(installer.inventory(source), installer.source_inventory(self.source))

    def test_backup_directory_overlapping_destination_is_refused(self):
        self.dest = self.root / "skill-backups" / installer.SKILL_NAME
        self.install()
        (self.dest / "local-notes.txt").write_text("keep", encoding="utf-8")
        old = installer.inventory(self.dest)
        with self.assertRaisesRegex(installer.InstallError, "Backup directory.*nested"):
            self.install(replace=True)
        self.assertEqual(installer.inventory(self.dest), old)

    def test_backup_directory_creation_failure_leaves_old_installation_in_place(self):
        self.install()
        (self.dest / "local-notes.txt").write_text("keep", encoding="utf-8")
        old = installer.inventory(self.dest)
        original_mkdir = Path.mkdir
        backup_root = self.dest.parent.parent / "skill-backups"

        def fail_backup_mkdir(path, *args, **kwargs):
            if path == backup_root:
                raise PermissionError("simulated backup mkdir failure")
            return original_mkdir(path, *args, **kwargs)

        with patch.object(Path, "mkdir", fail_backup_mkdir), self.assertRaisesRegex(PermissionError, "simulated"):
            self.install(replace=True)
        self.assertEqual(installer.inventory(self.dest), old)
        self.assertFalse(backup_root.exists())
        self.assertFalse(list(self.dest.parent.glob(".ai-dev-workbench.staging-*")))

    def test_failed_old_installation_move_leaves_it_in_place(self):
        self.install()
        (self.dest / "local-notes.txt").write_text("keep", encoding="utf-8")
        old = installer.inventory(self.dest)
        original_rename = Path.rename

        def fail_old_rename(path, target):
            if path == self.dest:
                raise OSError("simulated backup rename failure")
            return original_rename(path, target)

        with patch.object(Path, "rename", fail_old_rename), self.assertRaisesRegex(OSError, "simulated"):
            self.install(replace=True)
        self.assertEqual(installer.inventory(self.dest), old)
        self.assertFalse(list((self.dest.parent.parent / "skill-backups").glob("*.backup-*")))
        self.assertFalse(list(self.dest.parent.glob(".ai-dev-workbench.staging-*")))

    def test_replacement_refuses_an_unrelated_directory(self):
        self.dest.mkdir(parents=True)
        (self.dest / "important.txt").write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(installer.InstallError, "unrelated"):
            self.install(replace=True)
        self.assertEqual((self.dest / "important.txt").read_text(), "keep")

    def test_existing_file_is_never_replaced(self):
        self.dest.parent.mkdir()
        self.dest.write_text("not a directory", encoding="utf-8")
        with self.assertRaisesRegex(installer.InstallError, "not a directory"):
            self.install(replace=True)
        self.assertEqual(self.dest.read_text(), "not a directory")

    def test_symlink_destination_does_not_touch_link_target(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "important.txt").write_text("keep", encoding="utf-8")
        self.dest.parent.mkdir()
        self.dest.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(installer.InstallError, "symbolic-link"):
            self.install(replace=True)
        self.assertEqual(list(p.name for p in outside.iterdir()), ["important.txt"])
        self.assertTrue(self.dest.is_symlink())

    def test_symlink_parent_does_not_redirect_installation(self):
        outside = self.root / "outside"
        outside.mkdir()
        self.dest.parent.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(installer.InstallError, "symbolic-link"):
            self.install()
        self.assertEqual(list(outside.iterdir()), [])

    def test_nested_symlink_in_existing_skill_is_preserved_and_refused(self):
        self.install()
        outside = self.root / "outside.txt"
        outside.write_text("private", encoding="utf-8")
        (self.dest / "local-link").symlink_to(outside)
        with self.assertRaisesRegex(installer.InstallError, "symbolic link"):
            self.install(replace=True)
        self.assertTrue((self.dest / "local-link").is_symlink())
        self.assertEqual(outside.read_text(), "private")

    def test_source_symlink_is_not_followed(self):
        path = self.source / "assets/example.json"
        path.unlink()
        outside = self.root / "outside.json"
        outside.write_text("private", encoding="utf-8")
        path.symlink_to(outside)
        with self.assertRaisesRegex(installer.InstallError, "symbolic link"):
            self.install()
        self.assertFalse(self.dest.exists())

    def test_unexpected_source_file_is_not_silently_distributed(self):
        (self.source / ".env").write_text("private placeholder", encoding="utf-8")
        with self.assertRaisesRegex(installer.InstallError, "release manifest"):
            self.install()
        self.assertFalse(self.dest.exists())

    def test_equal_nested_and_ancestor_destinations_are_refused(self):
        for destination in (self.source, self.source / "nested", self.root):
            with self.subTest(destination=destination), self.assertRaisesRegex(installer.InstallError, "nested"):
                installer.install(destination, True, self.source)
        self.assertFalse((self.source / "nested").exists())
        self.assertTrue((self.source / "SKILL.md").is_file())

    def test_interrupted_final_move_restores_old_installation(self):
        self.install()
        (self.dest / "local-notes.txt").write_text("keep", encoding="utf-8")
        old = installer.inventory(self.dest)
        original_rename = Path.rename

        def fail_staging(path, target):
            if path.name.startswith(".ai-dev-workbench.staging-"):
                raise OSError("simulated final rename failure")
            return original_rename(path, target)

        with patch.object(Path, "rename", fail_staging), self.assertRaisesRegex(OSError, "simulated"):
            self.install(replace=True)
        self.assertEqual(installer.inventory(self.dest), old)
        self.assertFalse(list(self.dest.parent.glob(".ai-dev-workbench.staging-*")))
        self.assertFalse(list((self.dest.parent.parent / "skill-backups").glob("*.backup-*")))

    def test_source_change_during_copy_fails_without_creating_destination(self):
        original = installer.source_inventory

        def change_after_inventory(source):
            result = original(source)
            (source / "SKILL.md").write_text("changed during install", encoding="utf-8")
            return result

        with patch.object(installer, "source_inventory", change_after_inventory):
            with self.assertRaisesRegex(installer.InstallError, "Source changed"):
                self.install()
        self.assertFalse(self.dest.exists())
        self.assertFalse(list(self.dest.parent.glob(".ai-dev-workbench.staging-*")))

    def test_destination_change_during_staging_is_not_overwritten(self):
        self.install()
        (self.dest / "local-notes.txt").write_text("first edit", encoding="utf-8")
        original = installer.inventory

        def concurrent_edit(path):
            result = original(path)
            if path.name.startswith(".ai-dev-workbench.staging-"):
                (self.dest / "local-notes.txt").write_text("concurrent edit", encoding="utf-8")
            return result

        with patch.object(installer, "inventory", concurrent_edit):
            with self.assertRaisesRegex(installer.InstallError, "Destination changed"):
                self.install(replace=True)
        self.assertEqual((self.dest / "local-notes.txt").read_text(), "concurrent edit")
        self.assertFalse(list((self.dest.parent.parent / "skill-backups").glob("*.backup-*")))

    def test_cli_defaults_to_home_codex_skill_directory(self):
        fake_home = self.root / "home"
        fake_home.mkdir()
        with patch.object(Path, "home", return_value=fake_home), patch.dict(os.environ, {"CODEX_HOME": ""}), patch.object(sys, "argv", ["install.py"]):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(installer.main(), 0)
        self.assertTrue((fake_home / ".codex/skills/ai-dev-workbench/SKILL.md").is_file())

    def test_cli_respects_codex_home_when_set(self):
        codex_directory = self.root / "custom-codex"
        with patch.dict(os.environ, {"CODEX_HOME": str(codex_directory)}), patch.object(sys, "argv", ["install.py"]):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(installer.main(), 0)
        self.assertTrue((codex_directory / "skills/ai-dev-workbench/SKILL.md").is_file())

    def test_cli_destination_is_the_complete_skill_directory(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/install.py"), "--dest", str(self.dest)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.dest / "SKILL.md").is_file())
        self.assertFalse((self.dest / "ai-dev-workbench").exists())


class DistributionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="ai-workbench-release-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def run_cli(self, script, *args, cwd=None):
        result = subprocess.run([sys.executable, str(script), *map(str, args)], cwd=cwd or self.root,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def fixture_repo(self):
        root = self.root / "repository"
        root.mkdir()
        shutil.copytree(installer.SOURCE, root / "skills/ai-dev-workbench", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "scripts", root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        (root / "README.md").write_text("Public fixture repository.\n", encoding="utf-8")
        (root / "LICENSE").write_text("MIT test fixture; actual release requires repository LICENSE.\n", encoding="utf-8")
        return root

    def test_fictional_example_validates_links_and_builds_after_relocation(self):
        project = self.root / "unrelated path" / "document-assistant"
        shutil.copytree(ROOT / "examples/document-assistant", project)
        source = project / "docs/workbench/workbench.json"
        canonical = source.read_bytes()
        script = installer.SOURCE / "scripts/workbench.py"
        self.run_cli(script, "validate", "--project-root", project, "--data", source, "--check-links")
        self.run_cli(script, "build", "--project-root", project, "--data", source)
        self.assertEqual(source.read_bytes(), canonical)
        data = json.loads(canonical)
        self.assertIn("虚构", data["project"]["name"])
        self.assertIsNone(data["project"]["online_version"])
        self.assertFalse(data["evidence"])
        self.assertTrue(all(t["status"] in {"todo", "blocked"} for t in data["tasks"]))
        html = (source.parent / "index.html").read_text(encoding="utf-8")
        payload = html.split('<script id="workbench-data" type="application/json">', 1)[1].split("</script>", 1)[0]
        browser = json.loads(payload)
        self.assertEqual(browser["_source_file"], "docs/workbench/workbench.json")
        self.assertEqual(browser["project"]["sources"][0]["_source_href"], "SPEC.md")
        self.assertEqual(browser["project"]["sources"][0]["href"], "../../SPEC.md")
        self.assertNotIn(str(ROOT), html)
        self.assertNotIn("__WORKBENCH_DATA__", html)
        for version in data["versions"]:
            detail = (source.parent / "versions" / (version["id"] + ".html")).read_text(encoding="utf-8")
            self.assertIn('const ROOT_PREFIX = "../";', detail)

    def test_installed_skill_initializes_and_builds_an_empty_project(self):
        destination = self.root / "installed-skill"
        installer.install(destination)
        project = self.root / "empty-project"
        project.mkdir()
        script = destination / "scripts/workbench.py"
        self.run_cli(script, "init", "--project-root", project, "--name", "新产品", "--purpose", "待澄清的目标")
        source = project / "docs/workbench/workbench.json"
        self.run_cli(script, "build", "--project-root", project, "--data", source)
        self.assertTrue((source.parent / "index.html").is_file())
        data = json.loads(source.read_text(encoding="utf-8"))
        self.assertEqual(data["discovery"]["questions"], [])
        self.assertEqual(data["requirements"], [])

    def test_release_archive_is_reproducible_and_hashes_every_public_file(self):
        root = self.fixture_repo()
        (root / ".env").write_text("not a public file", encoding="utf-8")
        (root / "dist").mkdir()
        (root / "dist/private.txt").write_text("not a release input", encoding="utf-8")
        first, second = pack.release_bytes(root), pack.release_bytes(root)
        self.assertEqual(first, second)
        prefix = "ai-product-workbench-v0.2.0/"
        with zipfile.ZipFile(io.BytesIO(first)) as archive:
            names = archive.namelist()
            self.assertTrue(all(name.startswith(prefix) and ".." not in Path(name).parts for name in names))
            self.assertFalse(any("__pycache__" in name or name.endswith(".pyc") or "/dist/" in name or name.endswith("/.env") for name in names))
            manifest = json.loads(archive.read(prefix + "RELEASE.json"))
            self.assertEqual(manifest["license"], "MIT")
            self.assertEqual(manifest["skill"], "ai-dev-workbench")
            self.assertIn("scripts/install.py", manifest["files"])
            for name, digest in manifest["files"].items():
                self.assertEqual(hashlib.sha256(archive.read(prefix + name)).hexdigest(), digest)

    def test_release_archive_can_be_extracted_and_installed_without_the_repository(self):
        root = self.fixture_repo()
        content = pack.release_bytes(root)
        extracted = self.root / "download"
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            archive.extractall(extracted)
        release_root = extracted / "ai-product-workbench-v0.2.0"
        destination = self.root / "installed-from-zip"
        self.run_cli(release_root / "scripts/install.py", "--dest", destination)
        self.assertEqual(installer.inventory(destination), installer.source_inventory(installer.SOURCE))
        self.assertEqual((destination / "LICENSE").read_bytes(), (ROOT / "LICENSE").read_bytes())

    def test_packaging_rejects_symbolic_links_in_public_content(self):
        root = self.fixture_repo()
        (root / "docs").mkdir()
        secret = self.root / "private.txt"
        secret.write_text("must not be read", encoding="utf-8")
        (root / "docs/link.txt").symlink_to(secret)
        with self.assertRaisesRegex(ValueError, "symbolic-link"):
            pack.release_bytes(root)

    def test_packaging_refuses_environment_files_independently_of_gitignore(self):
        root = self.fixture_repo()
        (root / ".gitignore").write_text(".env*\n*.env\n", encoding="utf-8")
        for relative in ("examples/.env", "examples/.env.local", "docs/production.env", "docs/.ENV.PRODUCTION"):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic secret that must not ship", encoding="utf-8")
            with self.subTest(relative=relative), self.assertRaisesRegex(ValueError, "environment file"):
                pack.release_bytes(root)
            path.unlink()

    def test_packaging_refuses_secrets_directories(self):
        root = self.fixture_repo()
        for relative in ("docs/secrets/private-note.txt", "examples/.secrets/token.txt", "docs/Secrets/key.txt"):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic secret that must not ship", encoding="utf-8")
            with self.subTest(relative=relative), self.assertRaisesRegex(ValueError, "secrets path"):
                pack.release_bytes(root)
            path.unlink()

    def test_env_example_is_the_explicit_placeholder_exception(self):
        root = self.fixture_repo()
        path = root / "examples/.env.example"
        path.parent.mkdir()
        path.write_text("EXAMPLE_API_KEY=replace-with-your-key\n", encoding="utf-8")
        content = pack.release_bytes(root)
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            self.assertEqual(archive.read("ai-product-workbench-v0.2.0/examples/.env.example"), path.read_bytes())

    def test_existing_release_artifact_is_never_replaced_with_different_bytes(self):
        path = self.root / "release.zip"
        pack.write_once_or_identical(path, b"original")
        pack.write_once_or_identical(path, b"original")
        with self.assertRaisesRegex(ValueError, "overwrite"):
            pack.write_once_or_identical(path, b"different")
        self.assertEqual(path.read_bytes(), b"original")


if __name__ == "__main__":
    unittest.main(verbosity=2)
