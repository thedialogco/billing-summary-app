import base64
import os
from datetime import date
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, get_db, Base
from models import Project, ProjectCreate, ProjectUpdate, ProjectRead, ValidationResult, ValidationItem, GenerateResponse
from processing import parse_prebill, apply_cost_adjustment, read_master, append_to_master, validate
from pdf_generator import generate_pdf

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Billing Summary Generator")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Projects (settings)
# ---------------------------------------------------------------------------

@app.get("/api/projects", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.name).all()


@app.post("/api/projects", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@app.put("/api/projects/{project_id}", response_model=ProjectRead)
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@app.delete("/api/projects/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()


# ---------------------------------------------------------------------------
# Generate billing summary
# ---------------------------------------------------------------------------

@app.post("/api/generate", response_model=GenerateResponse)
async def generate(
    prebill_file: UploadFile = File(...),
    master_file: UploadFile = File(...),
    project_id: int = Form(...),
    invoice_number: int = Form(...),
    invoice_start: date = Form(...),
    invoice_end: date = Form(...),
    ecms_total: float = Form(...),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

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
            agreement_number=project.agreement_number,
            work_order_number=project.work_order_number,
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
