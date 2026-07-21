#!/usr/bin/env python3
"""Post-process generated manuscript DOCX formatting.

Adjusts:
1. Table cell paragraphs -> single spacing, no extra space before/after.
2. Image paragraphs -> centered with no paragraph indentation.
3. The manual reference list -> the Word "Bibliography" style.
4. Duplicate paragraph-property nodes -> valid, portable OOXML.

Edit ``TABLE_RATIOS`` to set fixed column proportions for specific tables,
keyed by the table number that appears in the caption (e.g. "Table 1.").
Leave a ratio list as ``None`` to skip width-fixing for that table.
"""

from __future__ import annotations

import argparse
import io
import zipfile
from pathlib import Path

from lxml import etree


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NSMAP = {"w": W_NS}

DOC_XML = "word/document.xml"

# Fixed column proportions (must sum to 1.0) for tables whose caption begins
# with the given number. Set to {} to disable width-fixing entirely.
TABLE_RATIOS: dict[str, list[float] | None] = {}
DATA_CELL_PADDING_TWIPS = 60


def w_tag(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def child(parent: etree._Element, tag: str) -> etree._Element:
    elem = parent.find(f"w:{tag}", namespaces=NSMAP)
    if elem is None:
        elem = etree.SubElement(parent, w_tag(tag))
    return elem


def parse_twips(value: str | None, default: int = 9000) -> int:
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def set_table_col_widths(
    tbl: etree._Element, ratios: list[float] | None = None
) -> None:
    grid = tbl.find("w:tblGrid", namespaces=NSMAP)
    if grid is None:
        return

    cols = grid.findall("w:gridCol", namespaces=NSMAP)
    if ratios is None or len(cols) != len(ratios):
        return

    current_widths = [parse_twips(c.get(w_tag("w"))) for c in cols]
    total = sum(current_widths)
    if total <= 0:
        total = 9000

    new_widths = [int(total * r) for r in ratios]
    new_widths[-1] += total - sum(new_widths)

    for col, width in zip(cols, new_widths):
        col.set(w_tag("w"), str(width))

    tbl_pr = child(tbl, "tblPr")
    layout = child(tbl_pr, "tblLayout")
    layout.set(w_tag("type"), "fixed")
    cell_margins = child(tbl_pr, "tblCellMar")
    for side in ("top", "left", "bottom", "right"):
        margin = child(cell_margins, side)
        margin.set(w_tag("type"), "dxa")
        margin.set(w_tag("w"), str(DATA_CELL_PADDING_TWIPS))
    borders = child(tbl_pr, "tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border = child(borders, side)
        border.set(w_tag("val"), "single")
        border.set(w_tag("sz"), "4")
        border.set(w_tag("space"), "0")
        border.set(w_tag("color"), "auto")

    for tr in tbl.findall(".//w:tr", namespaces=NSMAP):
        tc_list = tr.findall("w:tc", namespaces=NSMAP)
        if len(tc_list) != len(ratios):
            continue
        for tc, width in zip(tc_list, new_widths):
            tc_pr = child(tc, "tcPr")
            tc_w = child(tc_pr, "tcW")
            tc_w.set(w_tag("type"), "dxa")
            tc_w.set(w_tag("w"), str(width))


def set_paragraph_single_spacing(paragraph: etree._Element) -> None:
    p_pr = child(paragraph, "pPr")
    spacing = child(p_pr, "spacing")
    p_style = p_pr.find("w:pStyle", namespaces=NSMAP)
    style_id = p_style.get(w_tag("val")) if p_style is not None else ""
    spacing.set(w_tag("before"), "0")
    spacing.set(w_tag("after"), "240" if style_id == "ImageCaption" else "0")
    spacing.set(w_tag("line"), "240")
    spacing.set(w_tag("lineRule"), "auto")
    indent = child(p_pr, "ind")
    indent.set(w_tag("left"), "0")
    indent.set(w_tag("right"), "0")
    indent.set(w_tag("firstLine"), "0")
    indent.attrib.pop(w_tag("hanging"), None)
    jc = child(p_pr, "jc")
    jc.set(w_tag("val"), "left")


def deindent_paragraph(paragraph: etree._Element) -> None:
    p_pr = child(paragraph, "pPr")
    ind = child(p_pr, "ind")
    ind.set(w_tag("left"), "0")
    ind.set(w_tag("firstLine"), "0")
    ind.set(w_tag("hanging"), "0")


def paragraph_text(paragraph: etree._Element) -> str:
    return "".join(paragraph.itertext()).strip()


def set_paragraph_style(paragraph: etree._Element, style_id: str) -> None:
    p_pr = child(paragraph, "pPr")
    p_style = child(p_pr, "pStyle")
    p_style.set(w_tag("val"), style_id)


def center_paragraph(paragraph: etree._Element) -> None:
    p_pr = child(paragraph, "pPr")
    jc = child(p_pr, "jc")
    jc.set(w_tag("val"), "center")


def merge_duplicate_paragraph_properties(paragraph: etree._Element) -> None:
    properties = paragraph.findall("w:pPr", namespaces=NSMAP)
    if len(properties) < 2:
        return
    primary = properties[0]
    existing_tags = {element.tag for element in primary}
    for duplicate in properties[1:]:
        for element in list(duplicate):
            if element.tag not in existing_tags:
                duplicate.remove(element)
                primary.append(element)
                existing_tags.add(element.tag)
        paragraph.remove(duplicate)


def apply_body_semantics(root: etree._Element) -> dict[etree._Element, list[float]]:
    body = root.find(".//w:body", namespaces=NSMAP)
    if body is None:
        return {}

    in_references = False
    pending_ratios: list[float] | None = None
    space_before_next_paragraph = False
    table_ratios: dict[etree._Element, list[float]] = {}

    for element in body:
        if element.tag == w_tag("p"):
            text = paragraph_text(element)
            if space_before_next_paragraph and text:
                p_pr = child(element, "pPr")
                spacing = child(p_pr, "spacing")
                spacing.set(w_tag("before"), "240")
                space_before_next_paragraph = False
            style = element.find("w:pPr/w:pStyle", namespaces=NSMAP)
            style_id = style.get(w_tag("val")) if style is not None else ""
            if text == "References" and style_id == "Heading2":
                in_references = True
                continue
            if text.startswith("Table ") and "." in text[:10]:
                number = text.split()[1].rstrip(".")
                ratios = TABLE_RATIOS.get(number)
                if ratios:
                    pending_ratios = ratios
                    set_paragraph_style(element, "TableCaption")
                    in_references = False
                continue
            if in_references and text:
                set_paragraph_style(element, "Bibliography")
        elif element.tag == w_tag("tbl") and pending_ratios is not None:
            table_ratios[element] = pending_ratios
            pending_ratios = None
            space_before_next_paragraph = True

    return table_ratios


def process_document_xml(xml_bytes: bytes) -> bytes:
    parser = etree.XMLParser(remove_blank_text=False)
    root = etree.fromstring(xml_bytes, parser=parser)

    for paragraph in root.findall(".//w:p", namespaces=NSMAP):
        merge_duplicate_paragraph_properties(paragraph)

    table_ratios = apply_body_semantics(root)

    for tbl in root.findall(".//w:tbl", namespaces=NSMAP):
        set_table_col_widths(tbl, table_ratios.get(tbl))
        for paragraph in tbl.findall(".//w:tc//w:p", namespaces=NSMAP):
            set_paragraph_single_spacing(paragraph)

    for paragraph in root.findall(".//w:p", namespaces=NSMAP):
        has_drawing = paragraph.find(".//w:drawing", namespaces=NSMAP) is not None
        if has_drawing:
            deindent_paragraph(paragraph)
            center_paragraph(paragraph)

    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone="yes",
        pretty_print=False,
    )


def postprocess_docx(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"DOCX not found: {path}")

    with zipfile.ZipFile(path, "r") as zin:
        if DOC_XML not in zin.namelist():
            raise RuntimeError(f"Missing {DOC_XML} in {path}")
        doc_xml = zin.read(DOC_XML)
        updated_doc_xml = process_document_xml(doc_xml)

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = (
                    updated_doc_xml
                    if item.filename == DOC_XML
                    else zin.read(item.filename)
                )
                zout.writestr(item, data)

    path.write_bytes(buf.getvalue())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Post-process manuscript DOCX layout.")
    parser.add_argument(
        "--docx",
        type=Path,
        default=Path("manuscript/output/article.docx"),
        help="Path to generated DOCX file (default: manuscript/output/article.docx)",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    postprocess_docx(args.docx)
    print(f"Post-processed DOCX: {args.docx}")


if __name__ == "__main__":
    main()
