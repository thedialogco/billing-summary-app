import io
from datetime import date
from collections import defaultdict
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

HEADER_BLUE = colors.HexColor("#4472C4")
SUBHEADER_BLUE = colors.HexColor("#8EA9DB")
PHASE_BLUE = colors.HexColor("#D9E1F2")
WHITE = colors.white
BLACK = colors.black
LIGHT_GRAY = colors.HexColor("#F2F2F2")

FONT_BOLD = "Helvetica-Bold"
FONT_REG = "Helvetica"
FONT_SIZE = 8
SMALL = 7


def _fmt_hrs(val) -> str:
    if val is None or val == 0:
        return ""
    v = float(val)
    return str(int(v)) if v == int(v) else str(v)


def _fmt_cost(val) -> str:
    if val is None:
        return ""
    return f"${float(val):,.2f}"


def _fmt_date(d) -> str:
    if isinstance(d, date):
        return d.strftime("%-m/%-d/%y")
    return str(d)


def generate_pdf(
    new_rows: list[dict],
    master_rows: list[dict],
    agreement_number: str,
    work_order_number: str,
    invoice_number: int,
    invoice_start: date,
    invoice_end: date,
    ecms_total: float,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(letter),
        leftMargin=0.4 * inch,
        rightMargin=0.4 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch,
    )

    story = []
    story += _build_page1(
        new_rows, agreement_number, work_order_number,
        invoice_number, invoice_start, invoice_end, ecms_total
    )
    story.append(PageBreak())
    story += _build_page2(new_rows, master_rows, invoice_number)

    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Page 1 — Summary
# ---------------------------------------------------------------------------

def _build_page1(
    rows: list[dict],
    agreement: str,
    work_order: str,
    invoice_number: int,
    invoice_start: date,
    invoice_end: date,
    ecms_total: float,
) -> list:
    # Collect unique personnel sorted by last name
    personnel_set = sorted(
        {r["personnel"] for r in rows},
        key=lambda n: n.split(". ", 1)[-1]
    )

    # Aggregate by (phase, task, task_name) → {personnel: hours, adjusted_cost_total}
    task_data: dict[tuple, dict] = {}
    phase_order = []
    task_order = []

    for r in rows:
        key = (r["phase"], r["task"], r["task_name"])
        if key not in task_data:
            task_data[key] = {"hours_by_person": defaultdict(float), "total_cost": 0.0, "total_hours": 0.0}
            if r["phase"] not in phase_order:
                phase_order.append(r["phase"])
            if key not in task_order:
                task_order.append(key)
        task_data[key]["hours_by_person"][r["personnel"]] += r["hours"]
        task_data[key]["total_cost"] += r.get("adjusted_cost", r["cost"])
        task_data[key]["total_hours"] += r["hours"]

    # Sort phases: Bridge first, then Highway
    phase_order = sorted(phase_order, key=lambda p: (0 if p == "Bridge" else 1))

    # Fixed col widths
    page_w = landscape(letter)[0] - 0.8 * inch
    n_person = len(personnel_set)
    task_name_w = 2.2 * inch
    phase_w = 0.7 * inch
    task_w = 0.55 * inch
    person_w = 0.65 * inch
    total_hrs_w = 0.75 * inch
    total_amt_w = 1.0 * inch
    col_widths = [phase_w, task_w, task_name_w] + [person_w] * n_person + [total_hrs_w, total_amt_w]

    header_row1 = [
        Paragraph(
            f"<b>{agreement}, WO {work_order}&nbsp;&nbsp;&nbsp;&nbsp;"
            f"Invoice Period: {_fmt_date(invoice_start)} - {_fmt_date(invoice_end)}</b>",
            ParagraphStyle("h1", fontName=FONT_BOLD, fontSize=FONT_SIZE, textColor=WHITE)
        ),
        "", "", *[""] * n_person, "", ""
    ]
    header_row2 = [
        Paragraph(f"<b>Invoice # {invoice_number}</b>",
                  ParagraphStyle("h2", fontName=FONT_BOLD, fontSize=FONT_SIZE, textColor=WHITE)),
        "", "",
        *[""] * n_person,
        Paragraph("<b>Total Task Hours</b>",
                  ParagraphStyle("h2r", fontName=FONT_BOLD, fontSize=8, textColor=WHITE, alignment=TA_CENTER)),
        Paragraph("<b>Total Task Amount</b>",
                  ParagraphStyle("h2r", fontName=FONT_BOLD, fontSize=8, textColor=WHITE, alignment=TA_CENTER)),
    ]
    header_row3 = [
        Paragraph("<b>Phase</b>", ParagraphStyle("ch", fontName=FONT_BOLD, fontSize=FONT_SIZE, textColor=WHITE)),
        Paragraph("<b>Task</b>", ParagraphStyle("ch", fontName=FONT_BOLD, fontSize=FONT_SIZE, textColor=WHITE)),
        Paragraph("<b>Task Name</b>", ParagraphStyle("ch", fontName=FONT_BOLD, fontSize=FONT_SIZE, textColor=WHITE)),
        *[Paragraph(f"<b>{p}</b>", ParagraphStyle("ch", fontName=FONT_BOLD, fontSize=FONT_SIZE, textColor=WHITE, alignment=TA_CENTER))
          for p in personnel_set],
        Paragraph("<b>Hrs</b>", ParagraphStyle("ch", fontName=FONT_BOLD, fontSize=FONT_SIZE, textColor=WHITE, alignment=TA_CENTER)),
        "",
    ]

    table_data = [header_row1, header_row2, header_row3]
    styles = [
        # Header row 1: full-width blue
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BLUE),
        ("SPAN", (0, 0), (-1, 0)),
        # Header row 2
        ("BACKGROUND", (0, 1), (-1, 1), HEADER_BLUE),
        ("SPAN", (0, 1), (2 + n_person - 1, 1)),
        # Header row 3
        ("BACKGROUND", (0, 2), (-1, 2), HEADER_BLUE),
        ("FONTNAME", (0, 0), (-1, 2), FONT_BOLD),
        ("FONTSIZE", (0, 0), (-1, 2), FONT_SIZE),
        ("TEXTCOLOR", (0, 0), (-1, 2), WHITE),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("ALIGN", (3, 2), (-1, 2), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 2), (-1, -1), 0.5, colors.HexColor("#BFBFBF")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]

    data_start = len(table_data)

    # Grand totals accumulators
    grand_hrs_by_person: dict[str, float] = defaultdict(float)
    grand_total_hrs = 0.0
    grand_total_cost = 0.0

    for phase in phase_order:
        phase_shown = False
        phase_hrs_by_person: dict[str, float] = defaultdict(float)
        phase_total_hrs = 0.0
        phase_total_cost = 0.0

        phase_tasks = [k for k in task_order if k[0] == phase]
        for (ph, task, task_name) in phase_tasks:
            td = task_data[(ph, task, task_name)]
            person_cells = [_fmt_hrs(td["hours_by_person"].get(p)) for p in personnel_set]
            row = [
                Paragraph(f"<b>{phase}</b>", ParagraphStyle("pl", fontName=FONT_BOLD, fontSize=FONT_SIZE)) if not phase_shown else "",
                Paragraph(task, ParagraphStyle("tk", fontName=FONT_REG, fontSize=FONT_SIZE)),
                Paragraph(task_name, ParagraphStyle("tn", fontName=FONT_REG, fontSize=FONT_SIZE, wordWrap="CJK")),
                *[Paragraph(h, ParagraphStyle("hr", fontName=FONT_REG, fontSize=FONT_SIZE, alignment=TA_CENTER)) for h in person_cells],
                Paragraph(f"<b>{_fmt_hrs(td['total_hours'])}</b>",
                          ParagraphStyle("th", fontName=FONT_BOLD, fontSize=FONT_SIZE, alignment=TA_CENTER)),
                Paragraph(f"<b>{_fmt_cost(td['total_cost'])}</b>",
                          ParagraphStyle("tc", fontName=FONT_BOLD, fontSize=FONT_SIZE, alignment=TA_RIGHT)),
            ]
            table_data.append(row)
            phase_shown = True

            for p in personnel_set:
                h = td["hours_by_person"].get(p, 0)
                phase_hrs_by_person[p] += h
                grand_hrs_by_person[p] += h
            phase_total_hrs += td["total_hours"]
            phase_total_cost += td["total_cost"]
            grand_total_hrs += td["total_hours"]
            grand_total_cost += td["total_cost"]

        # Phase total row
        phase_row = [
            Paragraph(f"<b>{phase} Total</b>",
                      ParagraphStyle("pt", fontName=FONT_BOLD, fontSize=FONT_SIZE)),
            "", "",
            *[Paragraph(f"<b>{_fmt_hrs(phase_hrs_by_person.get(p))}</b>",
                        ParagraphStyle("ph", fontName=FONT_BOLD, fontSize=FONT_SIZE, alignment=TA_CENTER))
              for p in personnel_set],
            Paragraph(f"<b>{_fmt_hrs(phase_total_hrs)}</b>",
                      ParagraphStyle("pth", fontName=FONT_BOLD, fontSize=FONT_SIZE, alignment=TA_CENTER)),
            Paragraph(f"<b>{_fmt_cost(phase_total_cost)}</b>",
                      ParagraphStyle("ptc", fontName=FONT_BOLD, fontSize=FONT_SIZE, alignment=TA_RIGHT)),
        ]
        table_data.append(phase_row)
        row_idx = len(table_data) - 1
        styles += [
            ("BACKGROUND", (0, row_idx), (-1, row_idx), PHASE_BLUE),
            ("FONTNAME", (0, row_idx), (-1, row_idx), FONT_BOLD),
            ("SPAN", (0, row_idx), (2, row_idx)),
        ]

    # Grand total row
    grand_row = [
        Paragraph("<b>Grand Total</b>",
                  ParagraphStyle("gt", fontName=FONT_BOLD, fontSize=FONT_SIZE)),
        "", "",
        *[Paragraph(f"<b>{_fmt_hrs(grand_hrs_by_person.get(p))}</b>",
                    ParagraphStyle("gh", fontName=FONT_BOLD, fontSize=FONT_SIZE, alignment=TA_CENTER))
          for p in personnel_set],
        Paragraph(f"<b>{_fmt_hrs(grand_total_hrs)}</b>",
                  ParagraphStyle("gth", fontName=FONT_BOLD, fontSize=FONT_SIZE, alignment=TA_CENTER)),
        Paragraph(f"<b>{_fmt_cost(grand_total_cost)}</b>",
                  ParagraphStyle("gtc", fontName=FONT_BOLD, fontSize=FONT_SIZE, alignment=TA_RIGHT)),
    ]
    table_data.append(grand_row)
    gt_row = len(table_data) - 1
    styles += [
        ("FONTNAME", (0, gt_row), (-1, gt_row), FONT_BOLD),
        ("SPAN", (0, gt_row), (2, gt_row)),
    ]

    # Alternating row shading for data rows
    for i in range(data_start, len(table_data) - 1):
        if (i - data_start) % 2 == 1:
            # only shade if not already a phase total row
            pass  # handled above

    table = Table(table_data, colWidths=col_widths, repeatRows=3)
    table.setStyle(TableStyle(styles))

    return [table]


# ---------------------------------------------------------------------------
# Page 2 — Invoice Breakdown (full history)
# ---------------------------------------------------------------------------

def _build_page2(
    new_rows: list[dict],
    master_rows: list[dict],
    current_invoice: int,
) -> list:
    # Combine master rows with new rows (new rows added with current invoice number)
    all_rows = list(master_rows) + [
        {**r, "invoice_number": current_invoice} for r in new_rows
    ]

    # Collect all invoice numbers, sorted descending
    all_invoices = sorted(
        {r["invoice_number"] for r in all_rows if r.get("invoice_number") is not None},
        reverse=True,
    )

    # Build pivot: (phase, task, task_name) → {invoice_number: total_hours}
    pivot: dict[tuple, dict] = {}
    phase_order_keys = []
    task_order_keys = []

    for r in all_rows:
        key = (r["phase"], r["task"], r["task_name"])
        if key not in pivot:
            pivot[key] = defaultdict(float)
            if r["phase"] not in phase_order_keys:
                phase_order_keys.append(r["phase"])
            if key not in task_order_keys:
                task_order_keys.append(key)
        inv = r.get("invoice_number")
        hrs = r.get("hours") or 0
        if inv is not None:
            pivot[key][inv] += float(hrs)

    phase_order_keys = sorted(phase_order_keys, key=lambda p: (0 if p == "Bridge" else 1))

    # Column widths — dynamically fit invoice columns to page
    page_w = landscape(letter)[0] - 0.8 * inch
    phase_w = 0.65 * inch
    task_w = 0.52 * inch
    task_name_w = 2.4 * inch
    grand_w = 0.65 * inch
    fixed_w = phase_w + task_w + task_name_w + grand_w
    available_for_invs = page_w - fixed_w
    inv_w = min(0.6 * inch, max(0.38 * inch, available_for_invs / max(1, len(all_invoices))))
    inv_cols_w = [inv_w] * len(all_invoices)
    col_widths = [phase_w, task_w, task_name_w] + inv_cols_w + [grand_w]

    ps_header = ParagraphStyle("h", fontName=FONT_BOLD, fontSize=FONT_SIZE, textColor=WHITE, alignment=TA_CENTER)
    ps_header_l = ParagraphStyle("hl", fontName=FONT_BOLD, fontSize=FONT_SIZE, textColor=WHITE)

    header_row1 = [
        Paragraph("<b>Sum of Hrs</b>", ps_header_l),
        "", "",
        Paragraph("<b>Invoice</b>", ps_header),
        *[""] * (len(all_invoices) - 1),
        "",
    ]
    header_row2 = [
        Paragraph("<b>Phase Name</b>", ps_header_l),
        Paragraph("<b>Task</b>", ps_header),
        Paragraph("<b>Task Name</b>", ps_header_l),
        *[Paragraph(f"<b>{inv}</b>", ps_header) for inv in all_invoices],
        Paragraph("<b>Grand Total</b>", ps_header),
    ]

    table_data = [header_row1, header_row2]
    styles = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BLUE),
        ("BACKGROUND", (0, 1), (-1, 1), HEADER_BLUE),
        ("SPAN", (0, 0), (2, 0)),
        ("SPAN", (3, 0), (-2, 0)),
        ("TEXTCOLOR", (0, 0), (-1, 1), WHITE),
        ("FONTNAME", (0, 0), (-1, 1), FONT_BOLD),
        ("FONTSIZE", (0, 0), (-1, 1), FONT_SIZE),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (2, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 1), (-1, -1), 0.5, colors.HexColor("#BFBFBF")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]

    ps_cell = ParagraphStyle("c", fontName=FONT_REG, fontSize=FONT_SIZE)
    ps_bold = ParagraphStyle("b", fontName=FONT_BOLD, fontSize=FONT_SIZE)
    ps_num = ParagraphStyle("n", fontName=FONT_REG, fontSize=FONT_SIZE, alignment=TA_CENTER)
    ps_num_bold = ParagraphStyle("nb", fontName=FONT_BOLD, fontSize=FONT_SIZE, alignment=TA_CENTER)

    grand_totals_by_inv: dict[int, float] = defaultdict(float)
    grand_total_all = 0.0

    for phase in phase_order_keys:
        phase_shown = False
        phase_totals_by_inv: dict[int, float] = defaultdict(float)
        phase_total_all = 0.0

        phase_tasks = [k for k in task_order_keys if k[0] == phase]
        for (ph, task, task_name) in phase_tasks:
            inv_data = pivot[(ph, task, task_name)]
            row_total = sum(inv_data.values())
            row = [
                Paragraph(f"<b>{phase}</b>", ps_bold) if not phase_shown else "",
                Paragraph(task, ps_cell),
                Paragraph(task_name, ParagraphStyle("tn", fontName=FONT_REG, fontSize=FONT_SIZE)),
                *[Paragraph(_fmt_hrs(inv_data.get(inv)), ps_num) for inv in all_invoices],
                Paragraph(f"<b>{_fmt_hrs(row_total)}</b>", ps_num_bold),
            ]
            table_data.append(row)
            phase_shown = True

            for inv in all_invoices:
                h = inv_data.get(inv, 0)
                phase_totals_by_inv[inv] += h
                grand_totals_by_inv[inv] += h
            phase_total_all += row_total
            grand_total_all += row_total

        # Phase total row
        pt_row = [
            Paragraph(f"<b>{phase} Total</b>", ps_bold),
            "", "",
            *[Paragraph(f"<b>{_fmt_hrs(phase_totals_by_inv.get(inv))}</b>", ps_num_bold) for inv in all_invoices],
            Paragraph(f"<b>{_fmt_hrs(phase_total_all)}</b>", ps_num_bold),
        ]
        table_data.append(pt_row)
        row_i = len(table_data) - 1
        styles += [
            ("BACKGROUND", (0, row_i), (-1, row_i), PHASE_BLUE),
            ("SPAN", (0, row_i), (2, row_i)),
            ("FONTNAME", (0, row_i), (-1, row_i), FONT_BOLD),
        ]

    # Grand total row
    gt_row_data = [
        Paragraph("<b>Grand Total</b>", ps_bold),
        "", "",
        *[Paragraph(f"<b>{_fmt_hrs(grand_totals_by_inv.get(inv))}</b>", ps_num_bold) for inv in all_invoices],
        Paragraph(f"<b>{_fmt_hrs(grand_total_all)}</b>", ps_num_bold),
    ]
    table_data.append(gt_row_data)
    gt_i = len(table_data) - 1
    styles += [
        ("FONTNAME", (0, gt_i), (-1, gt_i), FONT_BOLD),
        ("SPAN", (0, gt_i), (2, gt_i)),
    ]

    table = Table(table_data, colWidths=col_widths, repeatRows=2)
    table.setStyle(TableStyle(styles))

    return [table]
