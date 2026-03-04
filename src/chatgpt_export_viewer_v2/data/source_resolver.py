from __future__ import annotations

import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SourceDescriptor:
    path: Path
    source_label: str
    warnings: list[str] = field(default_factory=list)
    is_temporary: bool = False
    temporary_root: Path | None = None

    def cleanup(self) -> None:
        if self.is_temporary and self.temporary_root and self.temporary_root.exists():
            shutil.rmtree(self.temporary_root, ignore_errors=True)


class SourceResolver:
    PRIMARY_REQUIRED = {"conversations.json"}
    OPTIONAL_FILES = {"shared_conversations.json", "user.json", "chat.html"}

    def resolve(self, source_text: str) -> SourceDescriptor:
        candidate = Path(source_text).expanduser()
        if not candidate.exists():
            raise FileNotFoundError(f"Source does not exist: {candidate}")

        if candidate.is_dir():
            warnings = self._validate_dir(candidate)
            return SourceDescriptor(path=candidate, source_label=str(candidate), warnings=warnings)

        if candidate.suffix.lower() == ".zip":
            return self._resolve_zip(candidate)

        raise ValueError(f"Unsupported source type: {candidate.suffix or 'file'}")

    def _resolve_zip(self, zip_path: Path) -> SourceDescriptor:
        temp_root = Path(tempfile.mkdtemp(prefix="chatgpt_export_v2_"))
        descriptor = SourceDescriptor(
            path=temp_root,
            source_label=str(zip_path),
            warnings=[],
            is_temporary=True,
            temporary_root=temp_root,
        )

        try:
            with zipfile.ZipFile(zip_path, "r") as archive:
                archive.extractall(temp_root)

            export_root = self._find_export_root(temp_root)
            descriptor.path = export_root
            descriptor.warnings.extend(self._validate_dir(export_root))
            return descriptor
        except Exception:
            descriptor.cleanup()
            raise

    def _find_export_root(self, temp_root: Path) -> Path:
        if (temp_root / "conversations.json").exists():
            return temp_root

        for child in temp_root.iterdir():
            if child.is_dir() and (child / "conversations.json").exists():
                return child

        for match in temp_root.rglob("conversations.json"):
            return match.parent

        raise ValueError("Could not locate conversations.json in extracted zip")

    def _validate_dir(self, folder: Path) -> list[str]:
        if not folder.exists() or not folder.is_dir():
            raise ValueError(f"Invalid export folder: {folder}")

        files = {p.name for p in folder.iterdir() if p.is_file()}
        missing_primary = self.PRIMARY_REQUIRED - files
        if missing_primary:
            raise ValueError(f"Missing required files: {', '.join(sorted(missing_primary))}")

        warnings: list[str] = []
        for optional in sorted(self.OPTIONAL_FILES - files):
            warnings.append(f"Optional file missing: {optional}")
        return warnings
