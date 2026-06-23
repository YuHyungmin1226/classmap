from __future__ import annotations

import io
import os
import zipfile
from dataclasses import dataclass
from html import escape
from typing import Final, Literal, TypeAlias, assert_never

from PIL import Image, UnidentifiedImageError

EMU_PER_INCH: Final = 914400
DEFAULT_DPI: Final = 96
MAX_IMAGE_WIDTH_EMU: Final = 5486400
IMAGE_EXTENSIONS: Final = {"png", "jpg", "jpeg", "gif", "webp"}

ParagraphStyle = Literal["Title", "Heading1", "Heading2", "Heading3", "Normal"]

PARAGRAPH_STYLE_XML: Final[dict[ParagraphStyle, str]] = {
    "Title": '<w:pPr><w:pStyle w:val="Title"/></w:pPr>',
    "Heading1": '<w:pPr><w:pStyle w:val="Heading1"/></w:pPr>',
    "Heading2": '<w:pPr><w:pStyle w:val="Heading2"/></w:pPr>',
    "Heading3": '<w:pPr><w:pStyle w:val="Heading3"/></w:pPr>',
    "Normal": "",
}

CONTENT_TYPES_XML: Final = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Default Extension="jpg" ContentType="image/jpeg"/>
  <Default Extension="jpeg" ContentType="image/jpeg"/>
  <Default Extension="gif" ContentType="image/gif"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

ROOT_RELS_XML: Final = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""


@dataclass(frozen=True, slots=True)
class DocParagraph:
    text: str
    style: ParagraphStyle = "Normal"


@dataclass(frozen=True, slots=True)
class DocImage:
    relationship_id: str
    name: str
    width_emu: int
    height_emu: int


@dataclass(frozen=True, slots=True)
class ImagePart:
    image: DocImage
    archive_path: str
    data: bytes


DocBlock: TypeAlias = DocParagraph | DocImage


def write_docx(blocks: list[DocBlock], images: list[ImagePart]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        archive.writestr("_rels/.rels", ROOT_RELS_XML)
        archive.writestr("word/_rels/document.xml.rels", _document_relationships_xml(images))
        archive.writestr("word/document.xml", _document_xml(blocks))
        for image in images:
            archive.writestr(image.archive_path, image.data)
    return buffer.getvalue()


def image_part(disk_path: str, name: str, index: int) -> ImagePart | None:
    ext = _file_extension(name)
    if ext not in IMAGE_EXTENSIONS:
        return None
    try:
        with Image.open(disk_path) as image:
            width_emu, height_emu = _image_size_emu(image.width, image.height)
            data = _image_bytes(image, disk_path, ext)
    except (OSError, UnidentifiedImageError):
        return None
    doc_image = DocImage(f"rId{index}", name, width_emu, height_emu)
    return ImagePart(doc_image, f"word/media/image{index}.{_docx_image_ext(ext)}", data)


def _document_xml(blocks: list[DocBlock]) -> str:
    body = "".join(_block_xml(block) for block in blocks)
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
  <w:body>
    {body}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
    </w:sectPr>
  </w:body>
</w:document>"""


def _block_xml(block: DocBlock) -> str:
    match block:
        case DocParagraph():
            return _paragraph_xml(block)
        case DocImage():
            return _image_xml(block)
        case unreachable:
            assert_never(unreachable)


def _paragraph_xml(paragraph: DocParagraph) -> str:
    style_xml = PARAGRAPH_STYLE_XML[paragraph.style]
    text_xml = escape(paragraph.text, quote=False)
    return (
        f"<w:p>{style_xml}<w:r><w:t xml:space=\"preserve\">"
        f"{text_xml}</w:t></w:r></w:p>"
    )


def _image_bytes(image: Image.Image, disk_path: str, ext: str) -> bytes:
    match ext:
        case "png" | "jpg" | "jpeg" | "gif":
            with open(disk_path, "rb") as image_file:
                return image_file.read()
        case "webp":
            output = io.BytesIO()
            image.save(output, format="PNG")
            return output.getvalue()
        case unreachable:
            assert_never(unreachable)


def _docx_image_ext(ext: str) -> Literal["png", "jpg", "jpeg", "gif"]:
    match ext:
        case "png" | "webp":
            return "png"
        case "jpg":
            return "jpg"
        case "jpeg":
            return "jpeg"
        case "gif":
            return "gif"
        case unreachable:
            assert_never(unreachable)


def _image_size_emu(width_px: int, height_px: int) -> tuple[int, int]:
    width_emu = int(width_px / DEFAULT_DPI * EMU_PER_INCH)
    height_emu = int(height_px / DEFAULT_DPI * EMU_PER_INCH)
    if width_emu <= MAX_IMAGE_WIDTH_EMU:
        return width_emu, height_emu
    scaled_height = int(height_emu * (MAX_IMAGE_WIDTH_EMU / width_emu))
    return MAX_IMAGE_WIDTH_EMU, scaled_height


def _image_xml(image: DocImage) -> str:
    name_xml = escape(image.name, quote=True)
    return f"""<w:p><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{image.width_emu}" cy="{image.height_emu}"/><wp:docPr id="1" name="{name_xml}"/><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="{name_xml}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{image.relationship_id}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{image.width_emu}" cy="{image.height_emu}"/></a:xfrm><a:prstGeom prst="rect"/></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>"""


def _document_relationships_xml(images: list[ImagePart]) -> str:
    relationships = "".join(
        f'<Relationship Id="{image.image.relationship_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{os.path.basename(image.archive_path)}"/>'
        for image in images
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{relationships}</Relationships>"""


def _file_extension(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""
