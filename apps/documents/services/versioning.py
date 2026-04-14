from __future__ import annotations

import json
import subprocess
from pathlib import Path

from django.conf import settings
from django.db.models import Max

from apps.documents.models import DocumentVersionSnapshot
from apps.documents.services.exporters import DocumentExportService


COMMON_GIT_PATHS = [
    Path("C:/Program Files/Git/cmd/git.exe"),
    Path("C:/Program Files/Git/bin/git.exe"),
    Path("C:/Program Files (x86)/Git/cmd/git.exe"),
]


class DocumentVersioningService:
    def create_snapshot(self, document, source_event: str, note: str = ""):
        payload = document.assembled_content or {}
        preview_pages = payload.get("preview_pages", [])
        rendered_html = ""
        if preview_pages:
            rendered_html = DocumentExportService().render_html(document, preview_pages)

        latest = document.version_snapshots.aggregate(max_version=Max("version_number"))["max_version"] or 0
        snapshot = DocumentVersionSnapshot.objects.create(
            document=document,
            version_number=latest + 1,
            source_event=source_event,
            note=note,
            generation_request=payload.get("generation_request", ""),
            snapshot_payload=payload,
            rendered_html=rendered_html,
        )

        sync_result = GitHubSyncService().sync_snapshot(snapshot)
        snapshot.sync_status = sync_result["status"]
        snapshot.sync_message = sync_result["message"]
        snapshot.sync_commit_hash = sync_result.get("commit_hash", "")
        snapshot.sync_repo_path = sync_result.get("repo_path", "")
        snapshot.save(update_fields=["sync_status", "sync_message", "sync_commit_hash", "sync_repo_path", "updated_at"])
        return snapshot


class GitHubSyncService:
    def sync_snapshot(self, snapshot: DocumentVersionSnapshot) -> dict:
        repo_path = Path(getattr(settings, "GITHUB_SYNC_REPO_PATH", settings.BASE_DIR))
        repo_path.mkdir(parents=True, exist_ok=True)

        snapshot_dir = repo_path / "document_versions" / f"document-{snapshot.document_id}" / f"v{snapshot.version_number:03d}"
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "document_id": snapshot.document_id,
            "document_title": snapshot.document.title,
            "version_number": snapshot.version_number,
            "source_event": snapshot.source_event,
            "note": snapshot.note,
            "generation_request": snapshot.generation_request,
            "created_at": snapshot.created_at.isoformat(),
            "preview_meta": snapshot.snapshot_payload.get("preview_meta", {}),
        }
        (snapshot_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        (snapshot_dir / "snapshot_payload.json").write_text(
            json.dumps(snapshot.snapshot_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if snapshot.rendered_html:
            (snapshot_dir / "preview.html").write_text(snapshot.rendered_html, encoding="utf-8")

        git_executable = self._git_executable()
        if not getattr(settings, "GITHUB_SYNC_ENABLED", True):
            return {
                "status": DocumentVersionSnapshot.SyncStatus.PENDING_SETUP,
                "message": "GitHub sync is disabled in settings.",
                "repo_path": str(repo_path),
            }

        if not git_executable:
            return {
                "status": DocumentVersionSnapshot.SyncStatus.PENDING_SETUP,
                "message": "Git executable was not found. Install Git and set GITHUB_SYNC_GIT_EXECUTABLE to enable GitHub sync.",
                "repo_path": str(repo_path),
            }

        if not (repo_path / ".git").exists():
            return {
                "status": DocumentVersionSnapshot.SyncStatus.PENDING_SETUP,
                "message": "Git repository was not found at the configured path. Clone or initialize the project repo before enabling GitHub sync.",
                "repo_path": str(repo_path),
            }

        try:
            self._run_git(git_executable, repo_path, "add", ".")
            commit_message = f"Document {snapshot.document_id} version v{snapshot.version_number:03d}"
            commit_result = self._run_git(
                git_executable,
                repo_path,
                "commit",
                "-m",
                commit_message,
                allow_empty_commit=True,
            )
            commit_hash = self._current_commit_hash(git_executable, repo_path)

            remote_url = getattr(settings, "GITHUB_SYNC_REMOTE_URL", "")
            should_push = getattr(settings, "GITHUB_SYNC_PUSH", False)
            if remote_url:
                self._ensure_remote(git_executable, repo_path, remote_url)
            if remote_url and should_push:
                branch = getattr(settings, "GITHUB_SYNC_BRANCH", "main")
                remote_name = getattr(settings, "GITHUB_SYNC_REMOTE_NAME", "origin")
                self._run_git(git_executable, repo_path, "push", "-u", remote_name, branch)
                return {
                    "status": DocumentVersionSnapshot.SyncStatus.SYNCED,
                    "message": "Version snapshot committed and pushed to GitHub.",
                    "commit_hash": commit_hash,
                    "repo_path": str(repo_path),
                }

            return {
                "status": DocumentVersionSnapshot.SyncStatus.COMMITTED_LOCAL,
                "message": "Version snapshot committed locally. Set GITHUB_SYNC_REMOTE_URL and enable GITHUB_SYNC_PUSH to push to GitHub.",
                "commit_hash": commit_hash,
                "repo_path": str(repo_path),
            }
        except Exception as exc:
            return {
                "status": DocumentVersionSnapshot.SyncStatus.FAILED,
                "message": str(exc),
                "repo_path": str(repo_path),
            }

    def _git_executable(self):
        configured = getattr(settings, "GITHUB_SYNC_GIT_EXECUTABLE", "")
        if configured and Path(configured).exists():
            return str(Path(configured))
        for candidate in COMMON_GIT_PATHS:
            if candidate.exists():
                return str(candidate)
        return None

    def _ensure_remote(self, git_executable: str, repo_path: Path, remote_url: str):
        remote_name = getattr(settings, "GITHUB_SYNC_REMOTE_NAME", "origin")
        result = self._run_git(git_executable, repo_path, "remote", allow_failure=True)
        remotes = result.stdout.split() if result else []
        if remote_name not in remotes:
            self._run_git(git_executable, repo_path, "remote", "add", remote_name, remote_url)

    def _current_commit_hash(self, git_executable: str, repo_path: Path) -> str:
        result = self._run_git(git_executable, repo_path, "rev-parse", "HEAD")
        return result.stdout.strip()

    def _run_git(self, git_executable: str, repo_path: Path, *args, allow_failure: bool = False, allow_empty_commit: bool = False):
        command = [git_executable, *args]
        result = subprocess.run(
            command,
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            stdout = (result.stdout or "").strip()
            stderr = (result.stderr or "").strip()
            message = stderr or stdout or f"git {' '.join(args)} failed"
            if allow_empty_commit and "nothing to commit" in message.lower():
                return result
            if allow_failure:
                return result
            raise RuntimeError(message)
        return result
