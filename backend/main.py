import base64
import os
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from processing import parse_prebill, apply_cost_adjustment, read_master, append_to_master, validate
from pdf_generator import generate_pdf


app = FastAPI(title="Billing Summary Generator")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ValidationItem(BaseModel):
    passed: bool
    message: str


class ValidationResult(BaseModel):
    passed: bool
    items: list[ValidationItem]


class GenerateResponse(BaseModel):
    pdf_b64: str
    master_xlsx_b64: str
    validation: ValidationResult


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(
    prebill_file: UploadFile = File(...),
    master_file: UploadFile = File(...),
    agreement_number: str = Form(...),
    work_order_number: str = Form(...),
    invoice_number: int = Form(...),
    invoice_start: date = Form(...),
    invoice_end: date = Form(...),
    ecms_total: float = Form(...),
):
    prebill_bytes = await prebill_file.read()
    master_bytes = await master_file.read()

    try:
        new_rows = parse_prebill(prebill_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse Prebill Data: {e}")

    if not new_rows:
        raise HTTPException(status_code=422, detail="No data rows found in Prebill Data file.")

    try:
        new_rows = apply_cost_adjustment(new_rows, ecms_total)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        master_rows = read_master(master_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse Master Billing Summary: {e}")

    passed, items = validate(new_rows, invoice_start, invoice_end, ecms_total)

    try:
        updated_master_bytes = append_to_master(master_bytes, new_rows, invoice_number)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update Master file: {e}")

    try:
        pdf_bytes = generate_pdf(
            new_rows=new_rows,
            master_rows=master_rows,
            agreement_number=agreement_number,
            work_order_number=work_order_number,
            invoice_number=invoice_number,
            invoice_start=invoice_start,
            invoice_end=invoice_end,
            ecms_total=ecms_total,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {e}")

    return GenerateResponse(
        pdf_b64=base64.b64encode(pdf_bytes).decode(),
        master_xlsx_b64=base64.b64encode(updated_master_bytes).decode(),
        validation=ValidationResult(
            passed=passed,
            items=[ValidationItem(**i) for i in items],
        ),
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Serve React frontend for all non-API routes (production)
# ---------------------------------------------------------------------------

_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/assets", StaticFiles(directory=_static_dir / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        return FileResponse(_static_dir / "index.html")
