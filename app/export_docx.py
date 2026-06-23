from __future__ import annotations

import io
import os
import zipfile
from datetime import datetime
from typing import Final

from .config import Config
from .docx_writer import DocBlock, DocParagraph, ImagePart, image_part, write_docx
from .models import ClassGroup, Flag, Session

EXPORT_ZIP_MIME: Final = "application/zip"


def build_classmap_export_zip(generated_at: datetime) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        classes = ClassGroup.query.order_by(ClassGroup.created_at).all()
        if not classes:
            archive.writestr(
                "ClassMap Export.docx",
                write_docx(
                    [DocParagraph("ClassMap Export", "Title"), DocParagraph("No content available.")],
                    [],
                ),
            )
        _write_class_folders(archive, classes, generated_at)
    return buffer.getvalue()


def _write_class_folders(
    archive: zipfile.ZipFile,
    classes: list[ClassGroup],
    generated_at: datetime,
) -> None:
    used_class_folders: set[str] = set()
    for class_group in classes:
        class_folder = _unique_segment(class_group.name, used_class_folders, "class")
        archive.writestr(f"{class_folder}/", "")
        used_session_folders: set[str] = set()
        map_sessions = (
            Session.query.filter_by(class_id=class_group.id)
            .order_by(Session.created_at)
            .all()
        )
        if not map_sessions:
            archive.writestr(f"{class_folder}/No sessions.txt", "No sessions.")
        for map_session in map_sessions:
            session_folder = _unique_segment(
                map_session.name,
                used_session_folders,
                "session",
            )
            session_prefix = f"{class_folder}/{session_folder}"
            archive.writestr(f"{session_prefix}/", "")
            flags = Flag.query.filter_by(session_id=map_session.id).order_by(Flag.created_at).all()
            docx_name = f"{session_folder}.docx"
            docx_bytes, attachments = _build_session_docx(
                class_group,
                map_session,
                flags,
                generated_at,
            )
            archive.writestr(f"{session_prefix}/{docx_name}", docx_bytes)
            _write_attachments(archive, session_prefix, attachments)


def _build_session_docx(
    class_group: ClassGroup,
    map_session: Session,
    flags: list[Flag],
    generated_at: datetime,
) -> tuple[bytes, list[tuple[str, str]]]:
    blocks: list[DocBlock] = [
        DocParagraph("ClassMap Export", "Title"),
        DocParagraph(f"Generated: {generated_at:%Y-%m-%d %H:%M:%S}"),
        DocParagraph(""),
        DocParagraph(
            f"Class: {class_group.name} ({_status_text(class_group.is_active)})",
            "Heading1",
        ),
        DocParagraph(
            f"Session: {map_session.name} ({_status_text(map_session.is_active)})",
            "Heading2",
        ),
    ]
    images: list[ImagePart] = []
    attachments: list[tuple[str, str]] = []
    _append_flags(blocks, images, attachments, flags)
    return write_docx(blocks, images), attachments


def _append_flags(
    blocks: list[DocBlock],
    images: list[ImagePart],
    attachments: list[tuple[str, str]],
    flags: list[Flag],
) -> None:
    if not flags:
        blocks.append(DocParagraph("No notes."))
        return

    for flag in flags:
        created = (
            flag.created_at.strftime("%Y-%m-%d %H:%M")
            if flag.created_at
            else "Unknown time"
        )
        author = flag.author_name or "Participant"
        blocks.append(
            DocParagraph(f"Note #{flag.id} - {author} ({created})", "Heading3")
        )
        if flag.x is not None and flag.y is not None:
            blocks.append(DocParagraph(f"Location: {flag.x:.4f}, {flag.y:.4f}"))
        if flag.file_path:
            attachment = _attachment(flag.file_path)
            if attachment is None:
                blocks.append(DocParagraph(f"Attachment missing: {_attachment_name(flag.file_path)}"))
            else:
                disk_path, name = attachment
                attachments.append((disk_path, name))
                blocks.append(DocParagraph(f"Attachment: {name}"))
                image = image_part(disk_path, name, len(images) + 1)
                if image is not None:
                    images.append(image)
                    blocks.append(image.image)
        if flag.text_content:
            for line in flag.text_content.splitlines():
                blocks.append(DocParagraph(line))
        blocks.append(DocParagraph(""))


def _attachment(file_path: str) -> tuple[str, str] | None:
    name = _attachment_name(file_path)
    disk_path = os.path.join(Config.UPLOAD_FOLDER, name)
    if not os.path.isfile(disk_path):
        return None
    return disk_path, name


def _write_attachments(
    archive: zipfile.ZipFile,
    session_prefix: str,
    attachments: list[tuple[str, str]],
) -> None:
    used_names: set[str] = set()
    for disk_path, name in attachments:
        archive_name = _unique_segment(name, used_names, "attachment")
        archive.write(disk_path, f"{session_prefix}/{archive_name}")


def _attachment_name(file_path: str) -> str:
    return file_path.replace("\\", "/").rsplit("/", 1)[-1]


def _status_text(is_active: bool) -> str:
    return "Active" if is_active else "Closed"


def _unique_segment(name: str, used: set[str], fallback: str) -> str:
    base = _safe_segment(name) or fallback
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base} ({suffix})"
        suffix += 1
    used.add(candidate)
    return candidate


def _safe_segment(name: str) -> str:
    invalid_chars = '<>:"/\\|?*'
    clean = "".join("_" if char in invalid_chars or ord(char) < 32 else char for char in name)
    return clean.strip().strip(".")
