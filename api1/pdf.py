import random
import string
import os
from typing import Any, Dict, List, Optional
import datetime
from decimal import Decimal
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch, A4, A3, A5
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Table,
    Spacer,
    TableStyle,
    PageBreak,
)
from reportlab.graphics.barcode import code39, code128, code93

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Group
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.rl_config import defaultPageSize

from starlette_admin.helpers import INVOICE_PDF_FOOTER_TEXT, QUOTATION_PDF_FOOTER_TEXT
from sqlalchemy import select
from sqlalchemy.orm import Session
from api1 import engine
from api1.users.model import Items_BinLocations, BinLocations_tbl

PAGE_HEIGHT = defaultPageSize[1]
PAGE_WIDTH = defaultPageSize[0]
Title = ""
pageinfo = "info example"

# =============================================================================
# GRAYSCALE COLOR PALETTE (Optimized for B&W printing)
# =============================================================================
COLOR_BLACK = colors.HexColor("#000000")           # Primary text
COLOR_DARK_GRAY = colors.HexColor("#333333")       # Secondary text, borders
COLOR_MEDIUM_GRAY = colors.HexColor("#666666")     # Tertiary text
COLOR_LIGHT_GRAY = colors.HexColor("#e0e0e0")      # Table borders
COLOR_ALT_ROW = colors.HexColor("#f5f5f5")         # Alternating row background
COLOR_HEADER_BG = colors.HexColor("#e8e8e8")       # Header background
COLOR_WHITE = colors.HexColor("#ffffff")           # White background


def myFirstPage(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Bold", 18)
    canvas.drawCentredString(PAGE_WIDTH / 2.0, PAGE_HEIGHT - 108, Title)
    canvas.setFont("Times-Roman", 11)
    canvas.drawString(inch, 0.75 * inch, "First Page / %s" % pageinfo)
    canvas.restoreState()


def myLaterPages(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 11)
    canvas.drawString(inch, 0.75 * inch, "Page %d %s" % (doc.page, pageinfo))
    canvas.restoreState()


# =============================================================================
# TYPOGRAPHY STYLES (Modern Sans-Serif Hierarchy)
# Using Helvetica family - clean, professional, universally available
# =============================================================================

# Document title style (e.g., "QUOTATION")
title_Style = ParagraphStyle(
    "DocumentTitle",
    fontName="Helvetica-Bold",
    fontSize=22,
    alignment=TA_LEFT,
    textColor=COLOR_BLACK,
    spaceAfter=2,
)

# Table header style
header_Style = ParagraphStyle(
    "TableHeader",
    fontName="Helvetica-Bold",
    fontSize=9,
    alignment=TA_CENTER,
    textColor=COLOR_BLACK,
)

# Table header style (right-aligned for Price/Amount)
header_right_Style = ParagraphStyle(
    "TableHeaderRight",
    fontName="Helvetica-Bold",
    fontSize=9,
    alignment=TA_RIGHT,
    textColor=COLOR_BLACK,
)

# Line item quantity (centered)
qty_Style = ParagraphStyle(
    "Quantity",
    fontName="Helvetica",
    fontSize=9,
    alignment=TA_CENTER,
    textColor=COLOR_BLACK,
)

# Line item description (left-aligned)
desc_Style = ParagraphStyle(
    "Description",
    fontName="Helvetica",
    fontSize=10,
    alignment=TA_LEFT,
    wordWrap=True,
    textColor=COLOR_BLACK,
)

# Line item comments (smaller, below description)
comment_Style = ParagraphStyle(
    "Comment",
    fontName="Helvetica-Oblique",
    fontSize=7,
    alignment=TA_LEFT,
    wordWrap=True,
    textColor=COLOR_MEDIUM_GRAY,
)

# Bin location style
bin_Style = ParagraphStyle(
    "BinLocation",
    fontName="Helvetica",
    fontSize=10,
    alignment=TA_CENTER,
    wordWrap=True,
    textColor=COLOR_DARK_GRAY,
)

# Price and amount style (right-aligned, slightly bold for amounts)
price_Style = ParagraphStyle(
    "Price",
    fontName="Helvetica",
    fontSize=9,
    alignment=TA_RIGHT,
    textColor=COLOR_BLACK,
)

amount_Style = ParagraphStyle(
    "Amount",
    fontName="Helvetica-Bold",
    fontSize=9,
    alignment=TA_RIGHT,
    textColor=COLOR_BLACK,
)

# Footer disclaimer text
disclaimer_Style = ParagraphStyle(
    "Disclaimer",
    fontName="Helvetica",
    fontSize=7,
    alignment=TA_LEFT,
    wordWrap=True,
    textColor=COLOR_MEDIUM_GRAY,
    leading=9,
)

# Footer total style
total_Style = ParagraphStyle(
    "Total",
    fontName="Helvetica-Bold",
    fontSize=11,
    alignment=TA_RIGHT,
    textColor=COLOR_BLACK,
)

# Address section label (e.g., "BILL TO")
address_label_Style = ParagraphStyle(
    "AddressLabel",
    fontName="Helvetica-Bold",
    fontSize=9,
    alignment=TA_LEFT,
    textColor=COLOR_DARK_GRAY,
    spaceAfter=4,
)

# Address content
address_Style = ParagraphStyle(
    "Address",
    fontName="Helvetica",
    fontSize=9,
    alignment=TA_LEFT,
    wordWrap=True,
    textColor=COLOR_BLACK,
    leading=11,
)

# Header info style (Date, Rep, Term)
info_Style = ParagraphStyle(
    "HeaderInfo",
    fontName="Helvetica",
    fontSize=9,
    alignment=TA_RIGHT,
    textColor=COLOR_BLACK,
)

info_bold_Style = ParagraphStyle(
    "HeaderInfoBold",
    fontName="Helvetica-Bold",
    fontSize=10,
    alignment=TA_RIGHT,
    textColor=COLOR_BLACK,
)

# Legacy styles (kept for backward compatibility with invoice/PO)
footer_1_Style = ParagraphStyle(
    "Titless",
    fontName="Helvetica",
    fontSize=8,
    alignment=TA_LEFT,
    wordWrap=True,
)

footer_center_style = ParagraphStyle(
    "CenterAlignValues",
    fontName="Helvetica",
    fontSize=10,
    alignment=TA_CENTER,
)

footer_2_Style = ParagraphStyle(
    "Titless",
    alignment=TA_RIGHT,
    fontName="Helvetica",
    wordWrap=True,
    fontSize=10,
)

footer_2_comm_Style = ParagraphStyle(
    "Titless",
    alignment=TA_RIGHT,
    fontName="Helvetica",
    wordWrap=True,
    fontSize=6,
    textColor=colors.white,
)

footer_3_Style = ParagraphStyle(
    "Titless",
    fontName="Helvetica",
    fontSize=10,
    alignment=TA_LEFT,
    wordWrap=True,
)

footer_3_comm_Style = ParagraphStyle(
    "Titless",
    fontName="Helvetica",
    fontSize=6,
    alignment=TA_LEFT,
    wordWrap=True,
)

footer_4_Style = ParagraphStyle(
    "Titless",
    fontName="Helvetica",
    fontSize=10,
    alignment=TA_CENTER,
    wordWrap=True,
)

menu_Style = ParagraphStyle(
    "Titless",
    alignment=TA_CENTER,
    fontName="Helvetica-Bold",
    fontSize=10,
)


def build_quotation_header(
    text_name, text_date, text_invoice_numb, barcode_value, DBname, itemID, FirstName, TermDescription, yourStyle_1
):
    """
    Modern compact header layout:
    Row 1: QUOTATION title on left, Date/Number/Rep on right
    Row 2: Barcode below title
    """
    # Barcode - readable size
    barcode128 = code128.Code128(
        barcode_value,
        barHeight=0.4 * inch,
        barWidth=1.5,
    )

    # Right content: Info block (clean, no heavy borders)
    right_content = Table(
        [
            [Paragraph(f"Date: {text_date}", info_Style)],
            [Paragraph(f"#{text_invoice_numb}", info_bold_Style)],
            [Paragraph(f"Rep: {FirstName}  •  Term: {TermDescription}", info_Style)],
        ],
        style=[
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
        ]
    )

    # Top row: Title on left, info on right
    top_row = Table(
        [[Paragraph(text_name.upper(), title_Style), right_content]],
        colWidths=[4.0 * inch, 3.5 * inch],
        style=[
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (0, 0), "LEFT"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
        ]
    )

    # Combine: top row + barcode below
    table_mix = Table(
        [
            [top_row],
            [barcode128],
        ],
        style=[
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 1), (-1, -1), 2),
        ]
    )
    return table_mix


def build_invoice_header(
    text_name, text_date, text_invoice_numb, barcode_value, DBname, itemID, FirstName, TermDescription, yourStyle_1
):
    table_header_0 = Table(
        [
            [f"Rep: {FirstName}", f"Term: {TermDescription}"],
            ["Date", f"{text_name} #"],
            [text_date, text_invoice_numb],
        ],
        style=[
            ("LINEABOVE", (0, 1), (-1, -1), 0.5, colors.black),
            ("LINEBEFORE", (0, 1), (1, -1), 0.3, colors.black),
            ("BOX", (0, 1), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (1, 0), "CENTER"),
            ("ALIGN", (0, 1), (1, -1), "CENTER"),
            ("ALIGN", (1, 1), (1, -1), "CENTER"),
        ],
    )
    table_header_0._argW[0] = 1.0 * inch
    table_header_0._argW[1] = 1.5 * inch

    barcode128 = code128.Code128(
        barcode_value,
        barHeight=0.4 * inch,
        barWidth=1.8,
    )

    table_header_barcode = Table(
        [
            [""],
            [Paragraph(text_name, yourStyle_1)],
            [""],
            [barcode128],
        ]
    )
    table_header_barcode._argW[0] = 5.0 * inch

    table_mix = Table(
        [[table_header_barcode, table_header_0]],
        style=[
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("TOPPADDING", (0, 0), (-1, -1), -90),
        ],
    )
    table_mix._argW[0] = 5.0 * inch
    return table_mix


def build_po_header(
    text_name, text_invoice_numb, text_date, yourStyle, yourStyle_small
):
    table_mix = Table(
        [
            [Paragraph(text_name, yourStyle)],
            [Paragraph(f"Order No.: {text_invoice_numb}", yourStyle_small)],
            [Paragraph(f"Order Date: {text_date}", yourStyle_small)],
            [Paragraph(f"Required Date: {text_date}", yourStyle_small)],
        ],
        style=[
            ("ALIGN", (0, 0), (2, 2), "RIGHT"),
        ],
    )
    table_mix._argW[0] = 7.5 * inch
    return table_mix


def date_number(
    text_name: str,
    doc_number: str = None,
    text_date: str = None,
    text_invoice_numb: str = None,
    barcode_value: str = None,
    number_page: str = None,
    elements: list = None,
    DBname: str = None,
    itemID: str = None,
    FirstName: str = None,
    TermDescription: str = None,
) -> list:

    styleSheet = getSampleStyleSheet()

    yourStyle = ParagraphStyle(
        "Titless",
        fontName="Helvetica-Bold",
        fontSize=21,
        parent=styleSheet["Heading2"],
        alignment=TA_RIGHT,
    )

    yourStyle_1 = ParagraphStyle(
        "Titless",
        fontName="Helvetica-Bold",
        fontSize=21,
        parent=styleSheet["Heading2"],
        alignment=TA_LEFT,
    )

    yourStyle_small = ParagraphStyle(
        "Titless",
        fontName="Helvetica",
        fontSize=11,
        parent=styleSheet["Heading2"],
        alignment=TA_RIGHT,
    )

    if text_name == "Quotation":
        return build_quotation_header(
            text_name, text_date, text_invoice_numb, barcode_value, DBname, itemID,
            FirstName, TermDescription, yourStyle_1
        )
    elif text_name == "Invoice":
        return build_invoice_header(
            text_name, text_date, text_invoice_numb, barcode_value, DBname, itemID,
            FirstName, TermDescription, yourStyle_1
        )
    elif text_name == "Purchase Order":
        return build_po_header(
            text_name, text_invoice_numb, text_date,
            yourStyle, yourStyle_small
        )

    raise ValueError(f"Unsupported document type: {text_name}")



def bill_ship(
    BusinessName: str,
    ShipContact: str,
    ShipAddress1: str,
    ShipAddress_many: str,
    ShipPhoneNo: str,
) -> list[Any]:
    """
    Modern lightweight address section.
    Uses underlined labels instead of heavy box borders.
    """
    # Build address content as single paragraph with line breaks
    address_lines = []
    if BusinessName:
        address_lines.append(f"<b>{BusinessName}</b>")
    if ShipContact:
        address_lines.append(ShipContact)
    if ShipAddress1:
        address_lines.append(ShipAddress1)
    if ShipAddress_many:
        address_lines.append(ShipAddress_many)
    if ShipPhoneNo:
        address_lines.append(ShipPhoneNo)

    address_text = "<br/>".join(address_lines)

    # Bill To section
    bill_to = Table(
        [
            [Paragraph("BILL TO", address_label_Style)],
            [Paragraph(address_text, address_Style)],
        ],
        style=[
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, COLOR_LIGHT_GRAY),
            ("TOPPADDING", (0, 0), (-1, 0), 0),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
            ("TOPPADDING", (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ]
    )
    bill_to._argW[0] = 3.5 * inch

    # Ship To section
    ship_to = Table(
        [
            [Paragraph("SHIP TO", address_label_Style)],
            [Paragraph(address_text, address_Style)],
        ],
        style=[
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, COLOR_LIGHT_GRAY),
            ("TOPPADDING", (0, 0), (-1, 0), 0),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
            ("TOPPADDING", (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ]
    )
    ship_to._argW[0] = 3.5 * inch

    # Combine side by side with gap
    table_mix_header = Table(
        [[bill_to, ship_to]],
        colWidths=[3.75 * inch, 3.75 * inch],
        style=[
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
    )
    return table_mix_header


def footer(
    text_Subtotal: str,
    text_Total: Optional[str] = None,
    text_footer_1: str = "",
) -> list[Any]:
    """
    Modern footer with prominent total and subtle disclaimer.
    """
    if text_Total:
        total_text = Paragraph(f"TOTAL: ${text_Total}", total_Style)
    else:
        total_text = Paragraph("", total_Style)

    # Create footer table with disclaimer on left, total on right
    table_footer = Table(
        [[Paragraph(text_footer_1, disclaimer_Style), total_text]],
        colWidths=[5.5 * inch, 2.0 * inch],
        style=[
            ("LINEABOVE", (0, 0), (-1, -1), 1, COLOR_DARK_GRAY),
            ("VALIGN", (0, 0), (0, 0), "TOP"),
            ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]
    )
    return table_footer


def SPLIT_LIST_TO_LISTS_1(lst, n):
    return [lst[i : i + n] for i in range(0, len(lst), n)]


def SPLIT_LIST_TO_LISTS_2(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def create_invoice_pdf(
    list_items: list[dict],
    db_name: str,
    invoice_number: str,
    invoice_date: str,
    business_name: str,
    sales_rep: str,
    term_description: str,
    producer: str = "Fcs",
) -> str:
    name_pdf = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S_invoice.pdf")

    doc = SimpleDocTemplate(
        name_pdf,
        pagesize=A4,
        title=f"Invoice #{invoice_number}",
        author=sales_rep,
        subject="Invoice",
        producer=producer,
        creator="Fcs Web Application",
    )

    elements = []
    counter = 29  # Optimized for compact layout
    list_to_list_items_all = SPLIT_LIST_TO_LISTS_1(list_items, counter)
    text_Subtotal_all = []

    for page_index, page_items in enumerate(list_to_list_items_all, start=1):
        subtotal_page = []
        data = []
        header_row = ["Qty", "Description", "Unit Price", "Amount"]
        data.append([Paragraph(h, menu_Style) for h in header_row])

        for item in page_items:
            qty = int(item["QtyShipped"])
            desc = item["ProductDescription"]
            price_each = round(float(item["UnitPrice"]), 2)
            amount = round(float(item["ExtendedPrice"]), 2)

            subtotal_page.append(amount)

            row = [
                Paragraph(str(qty), footer_4_Style),
                Paragraph(desc, footer_3_Style),
                Paragraph(f"${price_each:.2f}", footer_center_style),
                Paragraph(f"${amount:.2f}", footer_center_style),
            ]
            data.append(row)

        for _ in range(counter - len(page_items)):
            data.append(["", "", "", ""])
        if len(list_to_list_items_all) > 1:
            invoice_display_number = f"{invoice_number}-{page_index}"
        else:
            invoice_display_number = invoice_number

        elements.append(
            date_number(
                "Invoice",
                invoice_number,
                invoice_date,
                invoice_display_number,
                invoice_number,
                str(page_index),
                elements,
                db_name,
                invoice_number,
                sales_rep,
                term_description,
            )
        )
        elements.append(Spacer(1, 0.2 * inch))

        ShipContact = list_items[0].get("ShipContact", "")
        ShipAddress1 = list_items[0].get("ShipAddress1", "")
        ShipCity = list_items[0].get("ShipCity", "")
        ShipState = list_items[0].get("ShipState", "")
        ShipZipCode = list_items[0].get("ShipZipCode", "")
        ShipPhoneNo = list_items[0].get("ShipPhoneNo", "")

        ShipAddress_many = f"{ShipCity}, {ShipState} {ShipZipCode}"
        ShipPhoneNo_str = f"Tel: {ShipPhoneNo}"

        elements.append(
            bill_ship(
                business_name,
                ShipContact,
                ShipAddress1,
                ShipAddress_many,
                ShipPhoneNo_str,
            )
        )
        elements.append(Spacer(1, 0.2 * inch))

        table = Table(
            data,
            colWidths=[0.7 * inch, 4.8 * inch, 1 * inch, 1 * inch],
            style=[
                ("LINEABOVE", (0, 0), (3, 0), 1, colors.black),
                ("LINEBEFORE", (1, 0), (3, -1), 0.5, colors.black),
                ("LINEABOVE", (0, 0), (3, 1), 1, colors.black),
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("ALIGN", (0, 1), (1, -1), "LEFT"),
                ("ALIGN", (2, 1), (-1, -1), "CENTER"),
                ("ALIGN", (2, 1), (3, -1), "CENTER"),
            ],
        )
        elements.append(table)

        total_page = sum(subtotal_page)
        text_Subtotal_all.extend(subtotal_page)

        if page_index == len(list_to_list_items_all):
            total_all = sum(text_Subtotal_all)
            elements.append(footer(
                f"{total_page:.2f}", f"{total_all:.2f}",
                text_footer_1=INVOICE_PDF_FOOTER_TEXT
            ))
        else:
            elements.append(footer(
                f"{total_page:.2f}",
                text_footer_1=INVOICE_PDF_FOOTER_TEXT
            ))
            elements.append(PageBreak())

    doc.build(elements)
    return name_pdf


def get_bin_locations(product_upc: str) -> str:
    """
    Get bin locations for a product from DB1 (main inventory).
    Returns up to 2 bin locations sorted alphabetically, with '+' if more than 2 exist.
    Returns '-' if no bin locations found.
    """
    if not product_upc:
        return "-"

    try:
        with Session(engine["DB1"]) as session:
            query = (
                select(BinLocations_tbl.BinLocation)
                .join(
                    Items_BinLocations,
                    BinLocations_tbl.BinLocationID == Items_BinLocations.BinLocationID
                )
                .where(Items_BinLocations.ProductUPC == product_upc)
                .order_by(BinLocations_tbl.BinLocation.asc())
            )
            results = session.execute(query).scalars().all()

            if not results:
                return "-"
            elif len(results) == 1:
                return results[0] or "-"
            elif len(results) == 2:
                return f"{results[0]}, {results[1]}"
            else:
                return f"{results[0]}, {results[1]} +"
    except Exception:
        # If DB1 doesn't exist or query fails, return dash
        return "-"


def create_pdf_1(
    text_name: str,
    list_items: list[dict[Any]],
    DBname: str,
    *adata,
):
    name_pdf = f'{datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")}_form.pdf'
    doc = SimpleDocTemplate(
        name_pdf,
        pagesize=A4,
        title=adata[2],
        author=adata[1],
        subject=adata[0],
        producer=adata[3],
        creator="Fcs Web Application",
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch,
    )
    elements = []
    available_height = doc.height
    if text_name == "Quotation":
        counter = 30  # Optimized for reduced margins with compact layout
        for i_list_items in list_items:
            if i_list_items["Comments"]:
                counter = counter - 1
        list_to_list_items_all = SPLIT_LIST_TO_LISTS_1(list_items, counter)
        QuotationID = str(list_items[0]["QuotationID"])
    elif text_name == "Invoice":
        counter = 29  # Optimized for compact layout
        list_to_list_items_all = SPLIT_LIST_TO_LISTS_1(list_items, counter)
        InvoiceID = str(list_items[0]["InvoiceID"])
    elif text_name == "Purchase Order":
        list_to_list_items_all = SPLIT_LIST_TO_LISTS_1(list_items, 22)
    text_Subtotal_all: list[float] = list()
    data_temp_cycle_empty: list = list()
    for key0, value0 in enumerate(list_to_list_items_all):
        counter1 = 30  # Optimized for compact layout
        for i_value0 in value0:
            if i_value0.get("Comments"):
                counter1 = counter1 - 1
        key0 = key0 + 1
        text_Subtotal_temp: list[float] = list()
        data: list = list()
        data_temp: list = list()
        number_page = f"{key0}"
        if text_name == "Quotation":
            FirstName = adata[4]
            TermDescription = adata[5]
            text_footer_1 = QUOTATION_PDF_FOOTER_TEXT
            # Modern header row with new styles
            data_temp.append(Paragraph("Qty", header_Style))
            data_temp.append(Paragraph("Description", header_Style))
            data_temp.append(Paragraph("Bin", header_Style))
            data_temp.append(Paragraph("Price", header_right_Style))
            data_temp.append(Paragraph("Amount", header_right_Style))
            data.append(data_temp)
            BusinessName = list_items[0]["BusinessName"]
            ShipContact = list_items[0]["ShipContact"]
            ShipAddress1 = list_items[0]["ShipAddress1"]
            ShipAddress_many = f"{list_items[0]['ShipCity']}, {list_items[0]['ShipState']} {list_items[0]['ShipZipCode']}"
            ShipPhoneNo = f"Tel :{list_items[0]['ShipPhoneNo']}"
            text_date = list_items[0]["QuotationDate"].strftime("%m-%d-%Y")
            doc_number = None
            quotation_number_base = f"{list_items[0]['QuotationNumber']}"
            if len(list_to_list_items_all) > 1:
                text_invoice_numb = f"{list_items[0]['QuotationNumber']}-{number_page}"
            else:
                text_invoice_numb = f"{list_items[0]['QuotationNumber']}"
            elements.append(
                date_number(
                    text_name,
                    doc_number,
                    text_date,
                    text_invoice_numb,
                    quotation_number_base,
                    number_page,
                    elements,
                    DBname,
                    QuotationID,
                    FirstName,
                    TermDescription,
                )
            )
            elements.append(Spacer(1, 0.15 * inch))
            elements.append(
                bill_ship(
                    BusinessName,
                    ShipContact,
                    ShipAddress1,
                    ShipAddress_many,
                    ShipPhoneNo,
                )
            )
            elements.append(Spacer(1, 0.12 * inch))
            for key, value in enumerate(value0):
                text_items_Quantity = value["Qty"]
                text_items = value["ProductDescription"]
                text_items_Bin = value.get("BinLocation", "-")
                text_comm = value["Comments"]
                text_items_Price_Each = round(value["UnitPrice"], 2)
                # Fixed: Added .2f for consistent decimal formatting
                amount_value = round(float(text_items_Quantity) * float(text_items_Price_Each), 2)
                text_items_Amount = f"{amount_value:.2f}"
                text_Subtotal_temp.append(amount_value)
                data_temp_cycle: list = list()
                if text_comm:
                    # Row with comment - stacked content
                    data_temp_cycle.append(
                        (
                            Paragraph(f"{int(text_items_Quantity)}", qty_Style),
                            Paragraph("", comment_Style),
                        )
                    )
                    data_temp_cycle.append(
                        (
                            Paragraph(text_items, desc_Style),
                            Paragraph(text_comm, comment_Style),
                        ),
                    )
                    data_temp_cycle.append(
                        (
                            Paragraph(text_items_Bin, bin_Style),
                            Paragraph("", comment_Style),
                        )
                    )
                    data_temp_cycle.append(
                        (
                            Paragraph(f"${text_items_Price_Each:.2f}", price_Style),
                            Paragraph("", comment_Style),
                        )
                    )
                    data_temp_cycle.append(
                        (
                            Paragraph(f"${text_items_Amount}", amount_Style),
                            Paragraph("", comment_Style),
                        )
                    )
                else:
                    # Regular row without comment
                    data_temp_cycle.append(
                        Paragraph(f"{int(text_items_Quantity)}", qty_Style)
                    )
                    data_temp_cycle.append(
                        Paragraph(text_items, desc_Style),
                    )
                    data_temp_cycle.append(
                        Paragraph(text_items_Bin, bin_Style),
                    )
                    data_temp_cycle.append(
                        Paragraph(f"${text_items_Price_Each:.2f}", price_Style),
                    )
                    data_temp_cycle.append(
                        Paragraph(f"${text_items_Amount}", amount_Style),
                    )
                data.append(data_temp_cycle)
            # Fill remaining rows to maintain consistent page layout
            for count, _ in enumerate(range(counter1 - len(value0))):
                data.append(data_temp_cycle_empty)

            # Build modern table style
            table_style = [
                # Header row styling
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_BLACK),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("LINEBELOW", (0, 0), (-1, 0), 1, COLOR_DARK_GRAY),

                # Outer border (subtle)
                ("BOX", (0, 0), (-1, -1), 0.5, COLOR_DARK_GRAY),

                # NO vertical lines - cleaner modern look

                # Light horizontal lines between data rows
                ("LINEBELOW", (0, 1), (-1, -2), 0.25, COLOR_LIGHT_GRAY),

                # Alignment
                ("ALIGN", (0, 0), (2, 0), "CENTER"),    # Qty, Description, Bin headers centered
                ("ALIGN", (3, 0), (-1, 0), "RIGHT"),    # Price & Amount headers right-aligned
                ("ALIGN", (0, 1), (0, -1), "CENTER"),   # Qty column centered
                ("ALIGN", (1, 1), (1, -1), "LEFT"),     # Description left
                ("ALIGN", (2, 1), (2, -1), "CENTER"),   # Bin centered
                ("ALIGN", (3, 1), (-1, -1), "RIGHT"),   # Price & Amount right

                # Balanced padding for readability
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),

                # Vertical alignment
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]

            # Add alternating row backgrounds for easy visual tracking
            for row_idx in range(2, len(data), 2):
                table_style.append(("BACKGROUND", (0, row_idx), (-1, row_idx), COLOR_ALT_ROW))

            table_items = Table(
                data,
                colWidths=[0.5 * inch, 4.3 * inch, 1.3 * inch, 0.75 * inch, 0.65 * inch],
                style=table_style,
            )
            elements.append(table_items)
            for i in text_Subtotal_temp:
                text_Subtotal_all.append(i)
            if key0 == len(list_to_list_items_all):
                text_Total = sum(text_Subtotal_all)
                elements.append(
                    footer(
                        "{:.2f}".format(sum(text_Subtotal_temp)),
                        "{:.2f}".format(text_Total),
                        text_footer_1=text_footer_1,
                    )
                )
            else:
                elements.append(
                    footer(
                        "{:.2f}".format(sum(text_Subtotal_temp)),
                        text_footer_1=text_footer_1,
                    )
                )
                elements.append(PageBreak())
        elif text_name == "Purchase Order":
            [
                data_temp.append(Paragraph(i, menu_Style))
                for i in ["Qty", "UPC", "Unit", "Description", "Unit Price", "Amount"]
            ]
            data.append(data_temp)
            BusinessName = list_items[0]["BusinessName"]
            ShipContact = list_items[0]["ShipContact"]
            ShipAddress1 = list_items[0]["ShipAddress1"]
            ShipAddress_many = f"{list_items[0]['ShipCity']}, {list_items[0]['ShipState']} {list_items[0]['ShipZipCode']}"
            ShipPhoneNo = f"Tel :{list_items[0]['ShipPhoneNo']}"
            doc_number = list_items[0]["PoNumber"]
            text_date = list_items[0]["PoDate"].strftime("%m/%d/%Y")
            if len(list_to_list_items_all) > 1:
                text_invoice_numb = f"{list_items[0]['PoNumber']}-{number_page}"
            else:
                text_invoice_numb = f"{list_items[0]['PoNumber']}"
            elements.append(
                date_number(
                    text_name,
                    doc_number,
                    text_date,
                    text_invoice_numb,
                    number_page,
                    elements,
                    DBname,
                )
            )
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(
                bill_ship(
                    BusinessName,
                    ShipContact,
                    ShipAddress1,
                    ShipAddress_many,
                    ShipPhoneNo,
                )
            )
            elements.append(Spacer(1, 0.2 * inch))
            for key, value in enumerate(value0):
                text_items_Quantity = value["QtyOrdered"]
                text_items_ProductUPC = value["ProductUPC"]
                text_items_UnitDesc = value["UnitDesc"]
                if text_items_UnitDesc == None:
                    text_items_UnitDesc = ""
                text_items = value["ProductDescription"]
                text_items_Price_Each = round(value["UnitCost"], 2)
                text_items_Amount = f"{round(float(text_items_Quantity) * float(text_items_Price_Each), 2)}"
                text_Subtotal_temp.append(float(text_items_Amount))
                data_temp_cycle: list = list()
                data_temp_cycle.append(
                    Paragraph(f"{int(text_items_Quantity)}", footer_1_Style)
                )
                data_temp_cycle.append(Paragraph(text_items_ProductUPC, footer_1_Style))
                data_temp_cycle.append(Paragraph(text_items_UnitDesc, footer_1_Style))
                data_temp_cycle.append(Paragraph(text_items, footer_1_Style))
                data_temp_cycle.append(
                    Paragraph(f"${text_items_Price_Each}", footer_2_Style)
                )
                data_temp_cycle.append(
                    Paragraph(f"${text_items_Amount}", footer_2_Style)
                )
                data.append(data_temp_cycle)
            for _ in range(22 - len(value0)):
                data.append(data_temp_cycle_empty)
            table_items = Table(
                data,
                colWidths=[1.9 * inch] + [None] * (len(data[0]) - 1),
                style=[
                    ("LINEABOVE", (0, 0), (5, 1), 1, colors.black),
                    ("LINEBEFORE", (1, 0), (5, -1), 0.5, colors.black),
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("ALIGN", (0, 0), (5, 0), "CENTER"),
                    ("ALIGN", (0, 1), (2, -1), "CENTER"),
                    ("ALIGN", (2, 1), (3, -1), "RIGHT"),
                ],
            )
            table_items._argW[0] = 0.3 * inch
            table_items._argW[1] = 1.6 * inch
            table_items._argW[2] = 0.7 * inch
            table_items._argW[3] = 3.5 * inch
            table_items._argW[4] = 0.7 * inch
            table_items._argW[5] = 0.7 * inch
            elements.append(table_items)
            for i in text_Subtotal_temp:
                text_Subtotal_all.append(i)
            if key0 == len(list_to_list_items_all):
                text_Total = sum(text_Subtotal_all)
                elements.append(
                    footer(
                        "{:.2f}".format(sum(text_Subtotal_temp)),
                        "{:.2f}".format(text_Total),
                    )
                )
            else:
                elements.append(
                    footer(
                        "{:.2f}".format(sum(text_Subtotal_temp)),
                    )
                )
                elements.append(PageBreak())
    doc.build(elements)
    return name_pdf


def create_pdf2():
    filename = "three_tables.pdf"
    document = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    styleSheet = getSampleStyleSheet()
    x_offset = 50
    y_offset = 50
    cell_height = 50
    cell_width = 100
    multiline_text = "Invoice"
    yourStyle = ParagraphStyle(
        "Titless",
        fontName="Helvetica-Bold",
        fontSize=20,
        parent=styleSheet["Heading2"],
        alignment=TA_RIGHT,
    )
    table_header_0 = Table(
        [
            ["Date", "Invoice#"],
            ["11/6/2023", "75622 1"],
        ],
        style=[
            ("LINEABOVE", (0, 0), (3, 1), 0.5, colors.black),
            ("LINEBEFORE", (1, 0), (3, -1), 0.3, colors.black),
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (3, 0), "CENTER"),
            ("ALIGN", (0, 1), (2, -1), "CENTER"),
            ("ALIGN", (2, 1), (3, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ],
    )
    table_mix = Table(
        [
            [Paragraph(multiline_text, yourStyle), table_header_0],
        ],
        style=[
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (1, 1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 50),
        ],
    )
    table_mix._argW[0] = 2 * inch
    table_mix._argW[1] = 2 * inch
    text_items_Quantity = "2"
    text_items = "Cheyenne cigars 100's Full Flavoroijewooviv "
    text_items_Price_Each = "14.25"
    text_items_Amount = "14.25"
    footer_1_Style = ParagraphStyle(
        "Titless",
        alignment=TA_LEFT,
        wordWrap=True,
    )
    footer_2_Style = ParagraphStyle("Titless", alignment=TA_RIGHT, wordWrap=True)
    table_items = Table(
        [
            ["Quantity", "Description", "Price Each", "Amount"],
            [
                Paragraph(text_items_Quantity, footer_1_Style),
                Paragraph(text_items, footer_1_Style),
                Paragraph(f"${text_items_Price_Each}", footer_2_Style),
                Paragraph(f"${text_items_Amount}", footer_2_Style),
            ],
            [
                Paragraph(text_items_Quantity, footer_1_Style),
                Paragraph(text_items, footer_1_Style),
                Paragraph(f"${text_items_Price_Each}", footer_2_Style),
                Paragraph(f"${text_items_Amount}", footer_2_Style),
            ],
            [
                Paragraph(text_items_Quantity, footer_1_Style),
                Paragraph(text_items, footer_1_Style),
                Paragraph(f"${text_items_Price_Each}", footer_2_Style),
                Paragraph(f"${text_items_Amount}", footer_2_Style),
            ],
        ],
        spaceBefore=None,
        spaceAfter=None,
        style=[
            ("LINEABOVE", (0, 0), (3, 1), 0.5, colors.black),
            ("LINEBEFORE", (1, 0), (3, -1), 0.3, colors.black),
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (0, 0), (3, 0), "CENTER"),
            ("ALIGN", (0, 1), (2, -1), "LEFT"),
            ("ALIGN", (2, 1), (3, -1), "RIGHT"),
        ],
    )
    table_items._argW[1] = 4 * inch
    table_header_1 = Table(
        [
            ["Bill To:"],
            [
                """SUNOCO FOOD MART
RAJ
603 Broad St
NEW CASTLE , IN 47362
Tel :7656867119
"""
            ],
        ],
        style=[
            ("LINEABOVE", (0, 0), (3, 1), 0.5, colors.black),
            ("LINEBEFORE", (1, 0), (3, -1), 0.3, colors.black),
            ("BOX", (0, 0), (1, 1), 0.5, colors.black),
            ("ALIGN", (0, 0), (3, 0), "LEFT"),
            ("ALIGN", (0, 1), (2, -1), "LEFT"),
        ],
    )
    table_header_1._argW[0] = 3 * inch
    table_header_2 = Table(
        [
            ["Ship To:"],
            [
                """SUNOCO FOOD MART
RAJ
603 Broad St
NEW CASTLE , IN 47362
Tel :7656867119
"""
            ],
        ],
        style=[
            ("LINEABOVE", (0, 0), (3, 1), 0.5, colors.black),
            ("LINEBEFORE", (1, 0), (3, -1), 0.3, colors.black),
            ("BOX", (0, 0), (1, 1), 0.5, colors.black),
            ("ALIGN", (0, 0), (3, 0), "LEFT"),
            ("ALIGN", (0, 1), (2, -1), "LEFT"),
        ],
    )
    table_header_2._argW[0] = 3 * inch
    table_footer_1 = Table(
        [
            [
                Paragraph(text_footer_1, footer_1_Style),
                """
Subtotal:  $330.00
Total:  $530.00""",
            ],
        ],
        style=[
            ("LINEABOVE", (0, 0), (-1, -1), 0.5, colors.black),
            ("LINEBEFORE", (0, 0), (-1, -1), 0.3, colors.black),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
            ("ALIGN", (0, 0), (3, 0), "RIGHT"),
            ("ALIGN", (0, 1), (2, -1), "LEFT"),
        ],
    )
    table_footer_1._argW[0] = 6 * inch
    table_mix_header = Table(
        [
            [table_header_1, table_header_2],
        ],
    )

    table_mix_1 = Table(
        [[table_mix], [table_mix_header], [table_items], [table_footer_1]],
    )
    table_mix_1.wrapOn(document, 0, 0)
    table_mix_1.drawOn(document, 30, 550)
    document.save()


def create_pdf3():
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        KeepInFrame,
    )
    from reportlab.lib.styles import getSampleStyleSheet

    doc = SimpleDocTemplate("table.pdf", pagesize=letter)
    data_long_table = []
    for i in range(300):
        data_long_table.append([f"Цена {i}", f"товар {i}"])
    table = Table(data_long_table)
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), "#A9A9A9"),
            ("TEXTCOLOR", (0, 0), (-1, 0), (1, 1, 1)),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 14),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), (245 / 256, 245 / 256, 245 / 256)),
            ("TEXTCOLOR", (0, 1), (-1, -1), (0, 0, 0)),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, (0, 0, 0, 1)),
        ]
    )
    table.setStyle(style)
    story = []
    frame = KeepInFrame(doc.width, doc.height - 2 * inch, [table])
    story.append(frame)
    doc.build(story)
