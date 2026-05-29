import io
import zipfile
from datetime import date
from typing import Any
import openpyxl

# ---------------------------------------------------------------------------
# Column name aliases — keys are internal field names, values are lists of
# header strings to match (case-insensitive, whitespace-normalized).
# The first alias that matches a header cell wins.
# ---------------------------------------------------------------------------

PREBILL_ALIASES: dict[str, list[str]] = {
    "employee":   ["name", "employee / vendor / client", "employee/vendor/client", "employee",
                   "staff", "person", "vendor", "client"],
    "date":       ["date", "transaction date", "trans date", "work date", "service date"],
    "task":       ["task", "task #", "task number", "task code", "task id"],
    "org":        ["organization", "org.", "org", "department", "dept", "cost center"],
    "hours":      ["hours", "hrs", "bill", "bill hours", "billed hours", "hours billed",
                   "hrs billed", "quantity", "qty", "units"],
    "cost":       ["invoice amount", "billing extension", "bill effort", "billed amount",
                   "bill amount", "billing amount", "amount", "cost", "total cost", "extended cost"],
}

MASTER_ALIASES: dict[str, list[str]] = {
    "personnel":      ["personnel", "employee", "person", "staff", "name"],
    "phase":          ["phase name", "phase"],
    "task":           ["task", "task #", "task number", "task code"],
    "task_name":      ["task name", "task description", "description", "name"],
    "invoice_number": ["invoice #", "invoice number", "invoice no", "invoice", "inv #", "inv no", "inv"],
    "hours":          ["hours", "hrs", "quantity", "qty", "units"],
    "adjusted_cost":  ["cost adjusted to match ecms invoice", "cost adjusted", "adjusted cost",
                       "adj cost", "ecms cost", "adjusted billing"],
    "cost":           ["cost", "bill effort", "billed amount", "amount", "original cost"],
}


def _normalize(s: str) -> str:
    return " ".join(str(s).lower().split())


def _detect_columns(ws, aliases: dict[str, list[str]]) -> tuple[dict[str, int], list[str]]:
    """
    Scan the first non-empty row for header cells and map field names to
    1-based column indices. Returns (col_map, warnings).
    """
    # Find the header row — first row that has at least 3 non-empty cells
    header_row = 1
    for r in range(1, min(6, ws.max_row + 1)):
        non_empty = sum(1 for c in range(1, ws.max_column + 1) if ws.cell(r, c).value)
        if non_empty >= 3:
            header_row = r
            break

    # Build a map of normalized header text → column index
    header_map: dict[str, int] = {}
    for col in range(1, ws.max_column + 1):
        val = ws.cell(header_row, col).value
        if val is not None:
            header_map[_normalize(val)] = col

    col_map: dict[str, int] = {}
    warnings: list[str] = []

    for field, alias_list in aliases.items():
        matched = False
        for alias in alias_list:
            norm = _normalize(alias)
            if norm in header_map:
                col_map[field] = header_map[norm]
                matched = True
                break
        if not matched:
            # Try partial / contains match as a last resort
            for alias in alias_list:
                norm = _normalize(alias)
                for header_text, col_idx in header_map.items():
                    if norm in header_text or header_text in norm:
                        col_map[field] = col_idx
                        matched = True
                        break
                if matched:
                    break
        if not matched:
            warnings.append(f"Column not found for field '{field}' — tried: {alias_list[:3]}")

    return col_map, warnings, header_row


def format_name(raw: str) -> str:
    """
    'Arentz, Travis'           → 'T. Arentz'   (new Last, First format)
    '08312 - Travis C Arentz'  → 'T. Arentz'   (old NNNNN - Name format)
    """
    raw = str(raw).strip()
    if "," in raw:
        last, _, first_part = raw.partition(",")
        first_word = first_part.strip().split()[0] if first_part.strip() else ""
        if first_word:
            return f"{first_word[0]}. {last.strip()}"
        return last.strip()
    if " - " in raw:
        raw = raw.split(" - ", 1)[1]
    parts = raw.strip().split()
    if len(parts) < 2:
        return raw.strip()
    return f"{parts[0][0]}. {parts[-1]}"


def parse_task(raw: str, task_desc: dict | None = None) -> tuple[str, str]:
    """
    '0046'                           → ('0046', task_desc.get('0046', ''))
    '100.T102 - Engineering Support' → ('T102', 'Engineering Support')
    'T102 - Engineering Support'     → ('T102', 'Engineering Support')
    'T102'                           → ('T102', task_desc.get('T102', ''))
    """
    task_desc = task_desc or {}
    raw = str(raw).strip()

    # Old embedded format: contains " - " after optional numeric prefix
    if " - " in raw:
        after_dot = raw.split(".", 1)[1] if ("." in raw and not raw.replace(".", "").isdigit()) else raw
        code, _, name = after_dot.partition(" - ")
        code = code.strip()
        name = name.strip() or task_desc.get(code, "")
        return code, name

    # Strip leading numeric prefix like "100." only when followed by a letter (old format)
    if "." in raw:
        parts = raw.split(".", 1)
        if parts[0].isdigit() and parts[1] and not parts[1][0].isdigit():
            raw = parts[1]

    code = raw.strip()
    return code, task_desc.get(code, "")


def get_phase(organization: str) -> str:
    return "Bridge" if "bridge" in organization.lower() else "Highway"


def _get_sheet(wb, preferred_name: str):
    if preferred_name in wb.sheetnames:
        return wb[preferred_name]
    return wb[wb.sheetnames[0]]


def _find_best_sheet(wb, aliases: dict[str, list[str]]):
    """Return the worksheet whose headers best match the given aliases."""
    best_ws = wb[wb.sheetnames[0]]
    best_score = -1
    for name in wb.sheetnames:
        ws = wb[name]
        col_map, _, _ = _detect_columns(ws, aliases)
        if len(col_map) > best_score:
            best_score = len(col_map)
            best_ws = ws
    return best_ws


def parse_prebill(
    file_bytes: bytes,
    personnel_phase: dict | None = None,
    task_desc: dict | None = None,
) -> list[dict]:
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    ws = _find_best_sheet(wb, PREBILL_ALIASES)

    col_map, warnings, header_row = _detect_columns(ws, PREBILL_ALIASES)

    required = ["employee", "task", "hours", "cost"]
    missing = [f for f in required if f not in col_map]
    if missing:
        raise ValueError(
            f"Prebill file is missing required columns: {missing}. "
            f"Detection warnings: {warnings}"
        )

    rows = []
    for row_idx in range(header_row + 1, ws.max_row + 1):
        employee = ws.cell(row_idx, col_map["employee"]).value
        task_field = ws.cell(row_idx, col_map["task"]).value
        hours = ws.cell(row_idx, col_map["hours"]).value
        cost = ws.cell(row_idx, col_map["cost"]).value

        if not employee or not task_field:
            continue
        try:
            hours = float(hours)
            cost = float(cost)
        except (TypeError, ValueError):
            continue

        trans_date = None
        if "date" in col_map:
            raw_date = ws.cell(row_idx, col_map["date"]).value
            if raw_date is not None:
                trans_date = raw_date.date() if hasattr(raw_date, "date") else raw_date

        personnel = format_name(str(employee))

        # Phase: use personnel lookup first, fall back to org-column detection
        phase = None
        if personnel_phase:
            phase = personnel_phase.get(str(employee).lower().strip())
        if phase is None:
            org = ws.cell(row_idx, col_map["org"]).value if "org" in col_map else None
            phase = get_phase(str(org)) if org else "Highway"

        task_code, task_name = parse_task(str(task_field), task_desc)

        rows.append({
            "personnel": personnel,
            "phase": phase,
            "task": task_code,
            "task_name": task_name,
            "hours": hours,
            "cost": cost,
            "transaction_date": trans_date,
        })

    return rows


def apply_cost_adjustment(rows: list[dict], ecms_total: float) -> list[dict]:
    prebill_total = sum(r["cost"] for r in rows)
    if prebill_total == 0:
        raise ValueError("Prebill total is zero — cannot apply cost adjustment.")
    factor = ecms_total / prebill_total
    for r in rows:
        r["adjusted_cost"] = r["cost"] * factor
    return rows


def read_master(file_bytes: bytes) -> list[dict]:
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    ws = _find_best_sheet(wb, MASTER_ALIASES)

    col_map, warnings, header_row = _detect_columns(ws, MASTER_ALIASES)

    # Master is optional to read (used only for page 2 history), so warn but don't fail
    rows = []
    if "personnel" not in col_map:
        return rows

    for row_idx in range(header_row + 1, ws.max_row + 1):
        personnel = ws.cell(row_idx, col_map["personnel"]).value
        if not personnel:
            continue

        def get(field):
            return ws.cell(row_idx, col_map[field]).value if field in col_map else None

        rows.append({
            "personnel": personnel,
            "phase":          get("phase"),
            "task":           get("task"),
            "task_name":      get("task_name"),
            "invoice_number": get("invoice_number"),
            "hours":          get("hours"),
            "adjusted_cost":  get("adjusted_cost"),
            "cost":           get("cost"),
        })
    return rows


CURRENCY_FMT = '"$"#,##0.00'


def _clean_xlsx(raw: bytes) -> bytes:
    """
    Remove content that causes Excel's 'unsafe links' / repair dialog:
      - xl/externalLinks/ folder and all entries inside it
      - xl/calcChain.xml  (becomes stale after row appends)
    Also patches [Content_Types].xml and xl/_rels/workbook.xml.rels
    to remove dangling references to both.
    """
    import re

    skip_prefixes = ("xl/externalLinks/", "xl/calcChain.xml")

    with zipfile.ZipFile(io.BytesIO(raw), "r") as zin:
        names = zin.namelist()
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in names:
                if any(item.startswith(p) or item == p for p in skip_prefixes):
                    continue

                content_bytes = zin.read(item)

                if item == "[Content_Types].xml":
                    content = content_bytes.decode()
                    # Remove Override entries for calcChain and externalLinks
                    content = re.sub(
                        r'<Override[^/]*/xl/calcChain\.xml[^/]*/>', "", content)
                    content = re.sub(
                        r'<Override[^>]*/xl/externalLinks/[^>]*/>', "", content)
                    content_bytes = content.encode()

                elif item == "xl/_rels/workbook.xml.rels":
                    content = content_bytes.decode()
                    # Remove Relationship entries for externalLink and calcChain
                    content = re.sub(
                        r'<Relationship[^>]+/relationships/externalLink[^>]*/>', "", content)
                    content = re.sub(
                        r'<Relationship[^>]+/relationships/calcChain[^>]*/>', "", content)
                    content_bytes = content.encode()

                elif item == "xl/workbook.xml":
                    content = content_bytes.decode()
                    # Remove <externalReferences> block if present
                    content = re.sub(
                        r'<externalReferences>.*?</externalReferences>', "", content,
                        flags=re.DOTALL)
                    content_bytes = content.encode()

                zout.writestr(item, content_bytes)

    return out.getvalue()


def append_to_master(master_bytes: bytes, new_rows: list[dict], invoice_number: int) -> bytes:
    # keep_links=False drops external link references that openpyxl can't round-trip cleanly
    wb = openpyxl.load_workbook(io.BytesIO(master_bytes), data_only=True, keep_links=False)
    ws = _find_best_sheet(wb, MASTER_ALIASES)

    # Detect master column layout so we write into the right columns
    col_map, _, header_row = _detect_columns(ws, MASTER_ALIASES)

    # Fallback to known column positions if detection fails
    defaults = {
        "personnel": 1, "phase": 3, "task": 4, "task_name": 5,
        "invoice_number": 13, "hours": 15, "adjusted_cost": 18, "cost": 19,
    }
    for field, default_col in defaults.items():
        if field not in col_map:
            col_map[field] = default_col

    # Find first empty data row
    next_row = ws.max_row + 1
    while next_row > header_row + 1 and ws.cell(next_row - 1, col_map["personnel"]).value is None:
        next_row -= 1

    # Ensure column R header reads correctly
    ws.cell(header_row, col_map["adjusted_cost"]).value = "Cost Adjusted to Match ECMS Invoice"

    for r in new_rows:
        ws.cell(next_row, col_map["personnel"]).value      = r["personnel"]
        ws.cell(next_row, col_map["phase"]).value          = r["phase"]
        ws.cell(next_row, col_map["task"]).value           = r["task"]
        ws.cell(next_row, col_map["task_name"]).value      = r["task_name"]
        ws.cell(next_row, col_map["invoice_number"]).value = invoice_number
        ws.cell(next_row, col_map["hours"]).value          = r["hours"]

        adj_cell = ws.cell(next_row, col_map["adjusted_cost"])
        adj_cell.value         = round(r["adjusted_cost"], 2)
        adj_cell.number_format = CURRENCY_FMT

        next_row += 1

    buf = io.BytesIO()
    wb.save(buf)
    return _clean_xlsx(buf.getvalue())


def validate(
    new_rows: list[dict],
    invoice_start: date,
    invoice_end: date,
    ecms_total: float,
) -> tuple[bool, list[dict]]:
    items = []

    # 1. All dates within invoice period
    out_of_range = [
        r for r in new_rows
        if r.get("transaction_date")
        and not (invoice_start <= r["transaction_date"] <= invoice_end)
    ]
    if out_of_range:
        for r in out_of_range:
            items.append({"passed": False, "message": f"Date out of range: {r['personnel']} / {r['task']} on {r['transaction_date']}"})
    else:
        items.append({"passed": True, "message": "All transaction dates are within the invoice period."})

    # 2. No duplicate (personnel + task + date)
    seen: set[tuple[Any, Any, Any]] = set()
    dupes = []
    for r in new_rows:
        key = (r["personnel"], r["task"], r.get("transaction_date"))
        if key in seen:
            dupes.append(key)
        seen.add(key)
    if dupes:
        for d in dupes:
            items.append({"passed": False, "message": f"Duplicate entry: {d[0]} / {d[1]} on {d[2]}"})
    else:
        items.append({"passed": True, "message": "No duplicate entries detected."})

    # 3. Adjusted cost total matches ECMS total
    total_adjusted = sum(r.get("adjusted_cost", 0) for r in new_rows)
    diff = abs(total_adjusted - ecms_total)
    if diff > 0.02:
        items.append({"passed": False, "message": f"Adjusted total ${total_adjusted:,.2f} does not match ECMS total ${ecms_total:,.2f} (diff ${diff:.4f})."})
    else:
        items.append({"passed": True, "message": f"Adjusted total matches ECMS invoice total (${ecms_total:,.2f})."})

    passed = all(i["passed"] for i in items)
    return passed, items
