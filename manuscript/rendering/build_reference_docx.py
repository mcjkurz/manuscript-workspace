#!/usr/bin/env python3
"""Build a deterministic Word reference document for DOCX rendering.

This script takes the reference.docx that Quarto/pandoc generates (or a
starter created by `pandoc -o reference.docx --print-default-data-file
reference.docx`) and rewrites its styles so that the rendered manuscript
has consistent, portable paragraph and font settings. Adjust the
``STYLE_CONFIG`` and font names below to match your target journal or
press.

Usage:
    python3 build_reference_docx.py --docx manuscript/rendering/reference.docx

If ``reference.docx`` does not exist, the script creates a starter from
pandoc's default data file (requires pandoc on PATH).
"""

from __future__ import annotations

import argparse
import io
import shutil
import subprocess
import zipfile
from pathlib import Path

from lxml import etree


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
NS = {"w": W_NS}
STYLES_XML = "word/styles.xml"
DOCUMENT_XML = "word/document.xml"
DOCUMENT_RELS_XML = "word/_rels/document.xml.rels"
CONTENT_TYPES_XML = "[Content_Types].xml"
FOOTER_XML = "word/footer1.xml"
FOOTER_REL_ID = "rIdPageFooter"

# Edit these to match your target style. Sizes are in half-points; spacing
# and indents are in twips (1/20 of a point). Line spacing is in 240ths.
DEFAULT_FONT = "Times New Roman"
DEFAULT_EAST_ASIA_FONT = "SimSun"
DEFAULT_SIZE_HALF_POINTS = 24  # 12pt

STYLE_CONFIG = {
    "Normal": {"line": 480, "size_half_points": DEFAULT_SIZE_HALF_POINTS},
    "BodyText": {"line": 480, "first_line": 720},
    "FirstParagraph": {"line": 480},
    "Compact": {"line": 240, "based_on": "Normal"},
    "Abstract": {"line": 240, "before": 120, "after": 120},
    "Keywords": {"line": 240, "after": 240},
    "Heading1": {
        "line": 240,
        "after": 240,
        "alignment": "center",
        "keep_next": True,
        "size_half_points": 32,
        "bold": True,
    },
    "Heading2": {
        "line": 240,
        "before": 240,
        "after": 120,
        "keep_next": True,
        "size_half_points": 28,
        "bold": True,
    },
    "BlockText": {"line": 240, "before": 120, "after": 240, "left": 720, "right": 720},
    "FootnoteBlockText": {"line": 240, "left": 720, "right": 720, "size_half_points": 20},
    "FootnoteText": {"line": 240, "size_half_points": 20},
    "Bibliography": {"line": 240, "after": 120, "left": 720, "hanging": 720},
    "Caption": {"line": 240, "before": 120, "after": 120, "size_half_points": 22},
    "ImageCaption": {"line": 240, "before": 120, "after": 240, "size_half_points": 22},
    "TableCaption": {
        "line": 240,
        "before": 120,
        "after": 120,
        "keep_next": True,
        "size_half_points": 22,
    },
    "Epigraph": {"line": 240, "before": 120, "after": 120, "alignment": "right"},
}


def w_tag(name: str) -> str:
    return f"{{{W_NS}}}{name}"


def child(parent: etree._Element, name: str) -> etree._Element:
    result = parent.find(f"w:{name}", namespaces=NS)
    if result is None:
        result = etree.SubElement(parent, w_tag(name))
    return result


def set_val(parent: etree._Element, name: str, value: str) -> etree._Element:
    result = child(parent, name)
    result.set(w_tag("val"), value)
    return result


def style(root: etree._Element, style_id: str) -> etree._Element:
    result = root.find(f".//w:style[@w:styleId='{style_id}']", namespaces=NS)
    if result is None:
        result = etree.SubElement(
            root,
            w_tag("style"),
            {w_tag("type"): "paragraph", w_tag("styleId"): style_id},
        )
        set_val(result, "name", style_id)
    return result


def set_run_font(
    r_pr: etree._Element,
    *,
    size_half_points: int = DEFAULT_SIZE_HALF_POINTS,
    bold: bool = False,
    italic: bool = False,
) -> None:
    fonts = child(r_pr, "rFonts")
    fonts.set(w_tag("ascii"), DEFAULT_FONT)
    fonts.set(w_tag("hAnsi"), DEFAULT_FONT)
    fonts.set(w_tag("cs"), DEFAULT_FONT)
    fonts.set(w_tag("eastAsia"), DEFAULT_EAST_ASIA_FONT)
    set_val(r_pr, "sz", str(size_half_points))
    set_val(r_pr, "szCs", str(size_half_points))
    for name, enabled in (("b", bold), ("bCs", bold), ("i", italic), ("iCs", italic)):
        element = child(r_pr, name)
        element.set(w_tag("val"), "1" if enabled else "0")


def set_spacing(
    p_pr: etree._Element,
    *,
    line: int,
    before: int = 0,
    after: int = 0,
) -> None:
    spacing = child(p_pr, "spacing")
    spacing.set(w_tag("before"), str(before))
    spacing.set(w_tag("after"), str(after))
    spacing.set(w_tag("line"), str(line))
    spacing.set(w_tag("lineRule"), "auto")


def set_indent(
    p_pr: etree._Element,
    *,
    left: int = 0,
    right: int = 0,
    first_line: int = 0,
    hanging: int = 0,
) -> None:
    indent = child(p_pr, "ind")
    for name, value in (("left", left), ("right", right)):
        indent.set(w_tag(name), str(value))
    indent.attrib.pop(w_tag("firstLine"), None)
    indent.attrib.pop(w_tag("hanging"), None)
    if first_line:
        indent.set(w_tag("firstLine"), str(first_line))
    elif hanging:
        indent.set(w_tag("hanging"), str(hanging))


def configure_paragraph_style(root: etree._Element, style_id: str, config: dict) -> None:
    current = style(root, style_id)
    if "based_on" in config:
        set_val(current, "basedOn", config["based_on"])
    p_pr = child(current, "pPr")
    set_spacing(
        p_pr,
        line=config["line"],
        before=config.get("before", 0),
        after=config.get("after", 0),
    )
    set_indent(
        p_pr,
        left=config.get("left", 0),
        right=config.get("right", 0),
        first_line=config.get("first_line", 0),
        hanging=config.get("hanging", 0),
    )
    if "alignment" in config:
        set_val(p_pr, "jc", config["alignment"])
    if config.get("keep_next"):
        set_val(p_pr, "keepNext", "1")
    set_run_font(
        child(current, "rPr"),
        size_half_points=config.get("size_half_points", DEFAULT_SIZE_HALF_POINTS),
        bold=config.get("bold", False),
        italic=config.get("italic", False),
    )


def process_styles(xml_bytes: bytes) -> bytes:
    parser = etree.XMLParser(remove_blank_text=False)
    root = etree.fromstring(xml_bytes, parser=parser)

    defaults = child(child(root, "docDefaults"), "rPrDefault")
    set_run_font(child(defaults, "rPr"))

    for style_id, config in STYLE_CONFIG.items():
        configure_paragraph_style(root, style_id, config)

    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone="yes",
        pretty_print=False,
    )


def process_document(xml_bytes: bytes) -> bytes:
    parser = etree.XMLParser(remove_blank_text=False)
    root = etree.fromstring(xml_bytes, parser=parser)
    body = root.find("w:body", namespaces=NS)
    if body is None:
        raise RuntimeError("Reference document has no body")
    sect_pr = child(body, "sectPr")
    for existing in sect_pr.findall("w:footerReference", namespaces=NS):
        sect_pr.remove(existing)
    footer_reference = etree.Element(w_tag("footerReference"))
    footer_reference.set(w_tag("type"), "default")
    footer_reference.set(f"{{{R_NS}}}id", FOOTER_REL_ID)
    sect_pr.insert(0, footer_reference)
    page_size = child(sect_pr, "pgSz")
    page_size.set(w_tag("w"), "12240")
    page_size.set(w_tag("h"), "15840")
    margins = child(sect_pr, "pgMar")
    for name in ("top", "right", "bottom", "left"):
        margins.set(w_tag(name), "1440")
    margins.set(w_tag("header"), "720")
    margins.set(w_tag("footer"), "720")
    margins.set(w_tag("gutter"), "0")
    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone="yes",
        pretty_print=False,
    )


def process_relationships(xml_bytes: bytes) -> bytes:
    parser = etree.XMLParser(remove_blank_text=False)
    root = etree.fromstring(xml_bytes, parser=parser)
    for relationship in root.findall(f"{{{PKG_REL_NS}}}Relationship"):
        if relationship.get("Id") == FOOTER_REL_ID:
            root.remove(relationship)
    etree.SubElement(
        root,
        f"{{{PKG_REL_NS}}}Relationship",
        {
            "Id": FOOTER_REL_ID,
            "Type": f"{R_NS}/footer",
            "Target": "footer1.xml",
        },
    )
    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone="yes",
        pretty_print=False,
    )


def process_content_types(xml_bytes: bytes) -> bytes:
    parser = etree.XMLParser(remove_blank_text=False)
    root = etree.fromstring(xml_bytes, parser=parser)
    for override in root.findall(f"{{{CONTENT_TYPES_NS}}}Override"):
        if override.get("PartName") == "/word/footer1.xml":
            root.remove(override)
    etree.SubElement(
        root,
        f"{{{CONTENT_TYPES_NS}}}Override",
        {
            "PartName": "/word/footer1.xml",
            "ContentType": (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.footer+xml"
            ),
        },
    )
    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone="yes",
        pretty_print=False,
    )


def footer_xml() -> bytes:
    footer = etree.Element(w_tag("ftr"), nsmap={"w": W_NS, "r": R_NS})
    paragraph = etree.SubElement(footer, w_tag("p"))
    p_pr = etree.SubElement(paragraph, w_tag("pPr"))
    set_val(p_pr, "jc", "center")
    for field_type, text in (
        ("begin", None),
        (None, " PAGE "),
        ("separate", None),
        (None, "1"),
        ("end", None),
    ):
        run = etree.SubElement(paragraph, w_tag("r"))
        if field_type is not None:
            field = etree.SubElement(run, w_tag("fldChar"))
            field.set(w_tag("fldCharType"), field_type)
        elif text == " PAGE ":
            instruction = etree.SubElement(run, w_tag("instrText"))
            instruction.set(
                "{http://www.w3.org/XML/1998/namespace}space", "preserve"
            )
            instruction.text = text
        else:
            value = etree.SubElement(run, w_tag("t"))
            value.text = text
    return etree.tostring(
        footer,
        xml_declaration=True,
        encoding="UTF-8",
        standalone="yes",
        pretty_print=False,
    )


def create_starter_reference(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "pandoc",
            "-o",
            str(path),
            "--print-default-data-file",
            "reference.docx",
        ],
        capture_output=True,
    )
    if result.returncode != 0 or not path.exists():
        raise RuntimeError(
            "Could not create a starter reference.docx. Run "
            "`pandoc -o reference.docx --print-default-data-file reference.docx` "
            "manually, or place a reference DOCX at the target path."
        )


def rewrite_docx(path: Path) -> None:
    if not path.exists():
        create_starter_reference(path)
    with zipfile.ZipFile(path, "r") as source:
        updates = {
            STYLES_XML: process_styles(source.read(STYLES_XML)),
            DOCUMENT_XML: process_document(source.read(DOCUMENT_XML)),
            DOCUMENT_RELS_XML: process_relationships(
                source.read(DOCUMENT_RELS_XML)
            ),
            CONTENT_TYPES_XML: process_content_types(
                source.read(CONTENT_TYPES_XML)
            ),
            FOOTER_XML: footer_xml(),
        }
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
            for item in source.infolist():
                target.writestr(
                    item, updates.get(item.filename, source.read(item.filename))
                )
            if FOOTER_XML not in source.namelist():
                target.writestr(FOOTER_XML, updates[FOOTER_XML])
    path.write_bytes(output.getvalue())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--docx",
        type=Path,
        default=Path("manuscript/rendering/reference.docx"),
    )
    args = parser.parse_args()
    rewrite_docx(args.docx)
    print(f"Configured reference document: {args.docx}")


if __name__ == "__main__":
    main()
