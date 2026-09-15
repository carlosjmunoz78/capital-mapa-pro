from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import json
import re

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class SectionRef:
    section_id: str
    level: int
    title: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class RepositoryIndex:
    domain: str
    source_file: str
    source_sha256: str
    source_bytes: int
    line_count: int
    sections: tuple[SectionRef, ...]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["sections"] = [asdict(x) for x in self.sections]
        return data


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_index(domain: str, path: Path, expected_sha256: str | None = None) -> RepositoryIndex:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(path)
    raw = path.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    if expected_sha256 and actual_sha != expected_sha256:
        raise ValueError("source hash mismatch")
    text = raw.decode("utf-8", errors="strict")
    lines = text.splitlines()
    headings: list[tuple[int, int, str]] = []
    for lineno, line in enumerate(lines, 1):
        m = HEADING_RE.match(line)
        if m:
            headings.append((lineno, len(m.group(1)), m.group(2).strip()))

    sections: list[SectionRef] = []
    for idx, (lineno, level, title) in enumerate(headings):
        end_line = len(lines)
        for next_lineno, next_level, _ in headings[idx + 1:]:
            if next_level <= level:
                end_line = next_lineno - 1
                break
        sections.append(
            SectionRef(
                section_id=f"{domain}:{lineno}",
                level=level,
                title=title,
                start_line=lineno,
                end_line=end_line,
            )
        )

    return RepositoryIndex(
        domain=domain,
        source_file=path.name,
        source_sha256=actual_sha,
        source_bytes=len(raw),
        line_count=len(lines),
        sections=tuple(sections),
    )


def write_index(index: RepositoryIndex, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(index.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def extract_section_text(path: Path, section: SectionRef) -> str:
    lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    if section.start_line < 1 or section.end_line > len(lines) or section.end_line < section.start_line:
        raise ValueError("invalid section range")
    return "\n".join(lines[section.start_line - 1:section.end_line])
