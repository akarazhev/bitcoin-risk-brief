#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


KIT_NAME = "bitcoin-risk-brief-server-kit"
PROJECT_NAME = "bitcoin-risk-brief"
COPIED_CATEGORIES = (
    "server-kit-readme",
    "server-entrypoints",
    "server-scripts",
    "deployment-docs",
    "project-snapshot",
)
SERVER_ENTRYPOINTS = ("deploy-from-usb.sh",)
DOCS_TO_COPY = (
    "docs/operations/server-msi-cubi5-ubuntu-26.04.md",
    "docs/operations/deploy-ubuntu-cloudflare.md",
    "docs/operations/operations.md",
    "docs/operations/production-readiness.md",
    "docs/superpowers/specs/2026-07-01-usb-update-install-kit-v2-design.md",
)
REQUIRED_SERVER_SCRIPTS = (
    "01-bootstrap-host.sh",
    "02-install-cloudflared-from-usb.sh",
    "03-deploy-bitcoin-risk-brief.sh",
    "04-enable-bitcoin-risk-service.sh",
    "05-health-check.sh",
    "06-debug-bitcoin-risk-service.sh",
    "08-install-turnstile-env-from-usb.sh",
    "turnstile-env-preflight.py",
    "09-install-telegram-env-from-usb.sh",
    "telegram-env-preflight.py",
)
OPTIONAL_SERVER_SCRIPTS = (
    "07-update-bitcoin-risk-brief-from-usb.sh",
)
EXCLUDED_NAMES = {
    ".env",
    ".git",
    "backups",
    "data",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "playwright-report",
    "test-results",
    ".venv",
    ".superpowers",
    "notes",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".vite",
    ".cache",
    "__pycache__",
    ".DS_Store",
    ".idea",
    ".vscode",
    "server-kit",
}
EXCLUDED_SUFFIXES = (".pyc", ".log", ".tmp", ".tar", ".tar.gz", ".tgz", ".oci", ".img")
ALLOWED_ENV_EXAMPLES = {".env.example", ".env.production.example"}
APPLE_DOUBLE_PREFIX = "._"
FORBIDDEN_STAGED_NAMES = {".git", ".venv", ".superpowers", "notes"}


def is_forbidden_env_name(name: str) -> bool:
    return name.startswith(".env") and name not in ALLOWED_ENV_EXAMPLES


def git_ignored_paths(source_root: Path) -> set[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "--others", "--ignored", "--exclude-standard", "--directory", "-z"],
        cwd=source_root,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return {Path(relative.rstrip("/")) for relative in output.split("\0") if relative}


def is_ignored_path(relative_path: Path, ignored_paths: set[Path]) -> bool:
    return relative_path in ignored_paths or any(parent in ignored_paths for parent in relative_path.parents)


def should_exclude(path: Path, source_root: Path, ignored_paths: set[Path]) -> bool:
    if path.is_symlink():
        return True

    relative_path = path.relative_to(source_root)
    if is_ignored_path(relative_path, ignored_paths):
        return True

    relative_parts = relative_path.parts
    name = path.name
    return (
        any(part in EXCLUDED_NAMES for part in relative_parts)
        or any(is_forbidden_env_name(part) for part in relative_parts)
        or name.startswith(APPLE_DOUBLE_PREFIX)
        or any(name.endswith(suffix) for suffix in EXCLUDED_SUFFIXES)
        or "node_modules" in relative_parts
        or "playwright-report" in relative_parts
        or "test-results" in relative_parts
    )


def verify_no_forbidden_staged_files(project_dir: Path) -> None:
    forbidden: list[Path] = []
    for candidate in project_dir.rglob("*"):
        relative_parts = candidate.relative_to(project_dir).parts
        if (
            any(part in FORBIDDEN_STAGED_NAMES for part in relative_parts)
            or any(is_forbidden_env_name(part) for part in relative_parts)
            or candidate.name.startswith(APPLE_DOUBLE_PREFIX)
        ):
            forbidden.append(candidate)

    if forbidden:
        for path in forbidden:
            print(f"Forbidden staged file: {path}", file=sys.stderr)
        raise SystemExit(1)


def copy_file(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise SystemExit(f"Required file not found: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    shutil.copymode(source, destination)


def remove_apple_double_files(kit_dir: Path) -> None:
    for path in kit_dir.rglob(f"{APPLE_DOUBLE_PREFIX}*"):
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def copy_docs(source_root: Path, kit_dir: Path) -> None:
    for relative in DOCS_TO_COPY:
        copy_file(source_root / relative, kit_dir / relative)


def copy_server_readme(source_root: Path, kit_dir: Path) -> None:
    copy_file(source_root / "server-kit" / "README-RUN-ON-SERVER.md", kit_dir / "README-RUN-ON-SERVER.md")


def copy_server_entrypoints(source_root: Path, kit_dir: Path) -> None:
    for entrypoint in SERVER_ENTRYPOINTS:
        destination = kit_dir / entrypoint
        copy_file(source_root / "server-kit" / entrypoint, destination)
        destination.chmod(destination.stat().st_mode | 0o755)


def server_scripts_to_copy(source_root: Path) -> tuple[str, ...]:
    optional_scripts = tuple(
        script_name
        for script_name in OPTIONAL_SERVER_SCRIPTS
        if (source_root / "server-kit" / "scripts" / script_name).is_file()
    )
    return REQUIRED_SERVER_SCRIPTS + optional_scripts


def copy_server_scripts(source_root: Path, kit_dir: Path, script_names: tuple[str, ...]) -> None:
    scripts_dir = kit_dir / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    for script_name in script_names:
        destination = scripts_dir / script_name
        copy_file(source_root / "server-kit" / "scripts" / script_name, destination)
        destination.chmod(destination.stat().st_mode | 0o755)


def copy_project_snapshot(source_root: Path, project_dir: Path) -> None:
    ignored_paths = git_ignored_paths(source_root)
    for root, dirnames, filenames in source_root.walk():
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if not should_exclude(root / dirname, source_root, ignored_paths)
        ]

        relative_dir = root.relative_to(source_root)
        destination_dir = project_dir / relative_dir
        destination_dir.mkdir(parents=True, exist_ok=True)

        for filename in filenames:
            source_file = root / filename
            if should_exclude(source_file, source_root, ignored_paths):
                continue
            copy_file(source_file, destination_dir / filename)


def source_commit(source_root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=source_root,
        stderr=subprocess.DEVNULL,
        text=True,
    ).strip()


def write_manifest(source_root: Path, kit_dir: Path, script_names: tuple[str, ...]) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    scripts = tuple(f"scripts/{name}" for name in script_names)
    lines = (
        f"created_at_utc={now}",
        f"source_commit={source_commit(source_root)}",
        f"source_path={source_root.resolve()}",
        f"kit_path={kit_dir.resolve()}",
        f"project_snapshot=project/{PROJECT_NAME}",
        f"copied_categories={','.join(COPIED_CATEGORIES)}",
        f"entrypoints={','.join(SERVER_ENTRYPOINTS)}",
        f"docs={','.join(DOCS_TO_COPY)}",
        f"scripts={','.join(scripts)}",
    )
    (kit_dir / "manifest.txt").write_text("\n".join(lines) + "\n")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checksums(kit_dir: Path) -> None:
    checksum_path = kit_dir / "SHA256SUMS"
    lines: list[str] = []
    for path in sorted(kit_dir.rglob("*")):
        if not path.is_file() or path == checksum_path:
            continue
        relative = path.relative_to(kit_dir).as_posix()
        lines.append(f"{file_sha256(path)}  {relative}")
    checksum_path.write_text("\n".join(lines) + "\n")


def build_kit(target_dir: Path, source_root: Path) -> Path:
    source_root = source_root.resolve()
    target_dir = target_dir.resolve()
    kit_dir = target_dir / KIT_NAME
    project_dir = kit_dir / "project" / PROJECT_NAME
    script_names = server_scripts_to_copy(source_root)

    target_dir.mkdir(parents=True, exist_ok=True)
    if kit_dir.exists():
        shutil.rmtree(kit_dir)
    kit_dir.mkdir(parents=True)

    copy_server_readme(source_root, kit_dir)
    copy_server_entrypoints(source_root, kit_dir)
    copy_docs(source_root, kit_dir)
    copy_server_scripts(source_root, kit_dir, script_names)
    copy_project_snapshot(source_root, project_dir)
    remove_apple_double_files(kit_dir)

    for required in (project_dir / "podman-compose.yml", project_dir / ".env.production.example"):
        if not required.is_file():
            raise SystemExit(f"Required staged project file missing: {required}")
    verify_no_forbidden_staged_files(project_dir)

    write_manifest(source_root, kit_dir, script_names)
    remove_apple_double_files(kit_dir)
    write_checksums(kit_dir)
    remove_apple_double_files(kit_dir)
    return kit_dir


def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3):
        print("Usage: prepare_usb_kit.py <usb-target-dir> [source-repo-root]", file=sys.stderr)
        return 2

    target_dir = Path(argv[1])
    source_root = Path(argv[2]) if len(argv) == 3 else Path(__file__).resolve().parents[1]
    kit_dir = build_kit(target_dir, source_root)
    print(f"Created USB server kit: {kit_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
