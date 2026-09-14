import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.dataset import Dataset, DatasetVersion
from app.services.validator import validate_dataset
from app.security.pii_detector import analyze_pii
from app.services.profiler import profile_dataset
from app.services.semantic_detector import infer_semantics
from app.services.analysis_pipeline import run_phase1_analysis
from app.services.analytics_planner import build_analytics_plan


router = APIRouter(prefix="/datasets", tags=["Datasets"])

UPLOAD_DIR = Path("storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

# upload route
# upload route

@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_id: str | None = Form(None),
    db: Session = Depends(get_db),
):
    allowed_extensions = {".csv", ".xlsx", ".xls"}

    extension = Path(file.filename).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and Excel files are supported.",
        )

    if dataset_id is None:
        dataset = Dataset(
            id=uuid.uuid4(),
            name=Path(file.filename).stem,
        )

        db.add(dataset)
        db.flush()

        version_number = 1

    else:
        try:
            dataset_uuid = uuid.UUID(dataset_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid dataset_id.",
            )

        dataset = (
            db.query(Dataset)
            .filter(Dataset.id == dataset_uuid)
            .first()
        )

        if dataset is None:
            raise HTTPException(
                status_code=404,
                detail="Dataset not found.",
            )

        latest_version = (
            db.query(DatasetVersion)
            .filter(
                DatasetVersion.dataset_id == dataset.id
            )
            .order_by(
                DatasetVersion.version_number.desc()
            )
            .first()
        )

        version_number = (
            latest_version.version_number + 1
            if latest_version
            else 1
        )

    file_id = uuid.uuid4()

    stored_filename = f"{file_id}{extension}"

    file_path = UPLOAD_DIR / stored_filename

    contents = await file.read()

    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    version = DatasetVersion(
        id=file_id,
        dataset_id=dataset.id,
        version_number=version_number,
        file_name=file.filename,
        file_path=str(file_path),
    )

    db.add(version)

    db.commit()

    return {
        "message": "Dataset uploaded successfully",
        "dataset_id": str(dataset.id),
        "dataset_version_id": str(file_id),
        "version_number": version_number,
        "file_name": file.filename,
    }

# validate route
@router.post("/{dataset_version_id}/validate")
def validate_dataset_version(
    dataset_version_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    version = (
        db.query(DatasetVersion)
        .filter(
            DatasetVersion.id == dataset_version_id
        )
        .first()
    )

    if version is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset version not found.",
        )

    try:
        validation_result = validate_dataset(
            version.file_path
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Validation failed: {str(e)}",
        )

    return {
        "dataset_version_id": str(
            dataset_version_id
        ),
        "validation": validation_result,
    }

# pii-scan route
@router.post("/{dataset_version_id}/pii-scan")
def scan_dataset_pii(
    dataset_version_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    version = (
        db.query(DatasetVersion)
        .filter(
            DatasetVersion.id == dataset_version_id
        )
        .first()
    )

    if version is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset version not found.",
        )

    try:
        pii_result = analyze_pii(
            version.file_path
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"PII scan failed: {str(e)}",
        )

    return {
        "dataset_version_id": str(
            dataset_version_id
        ),
        "pii_scan": pii_result,
    }


# Profile
@router.get("/{dataset_version_id}/profile")
def profile_dataset_version(
    dataset_version_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    version = (
        db.query(DatasetVersion)
        .filter(
            DatasetVersion.id == dataset_version_id
        )
        .first()
    )

    if version is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset version not found.",
        )

    try:
        profile = profile_dataset(
            version.file_path
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Profiling failed: {str(e)}",
        )

    return {
        "dataset_version_id": str(
            dataset_version_id
        ),
        "profile": profile,
    }

# semantics
@router.get("/{dataset_version_id}/semantics")
def detect_dataset_semantics(
    dataset_version_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    version = (
        db.query(DatasetVersion)
        .filter(
            DatasetVersion.id == dataset_version_id
        )
        .first()
    )

    if version is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset version not found.",
        )

    try:
        semantics = infer_semantics(
            version.file_path
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Semantic detection failed: {str(e)}",
        )

    return {
        "dataset_version_id": str(
            dataset_version_id
        ),
        "semantics": semantics,
    }

# analyze
# analyze
@router.post("/{dataset_version_id}/analyze")
def analyze_dataset_version(
    dataset_version_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    version = (
        db.query(DatasetVersion)
        .filter(
            DatasetVersion.id == dataset_version_id
        )
        .first()
    )

    if version is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset version not found.",
        )

    try:
        result = run_phase1_analysis(
            version.file_path,
            dataset_id=str(version.dataset_id),
            dataset_version_id=str(version.id),
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Analysis failed: {str(e)}",
        )

    return {
        "analysis_run_id": result.get("analysis_run_id"),
        "dataset_version_id": str(dataset_version_id),
        "analysis": result,
    }

#plan
@router.get("/{dataset_version_id}/plan")
def create_analytics_plan(
    dataset_version_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    version = (
        db.query(DatasetVersion)
        .filter(
            DatasetVersion.id == dataset_version_id
        )
        .first()
    )

    if version is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset version not found.",
        )

    try:
        profile = profile_dataset(
            version.file_path
        )

        semantics = infer_semantics(
            version.file_path
        )

        plan = build_analytics_plan(
            profile,
            semantics,
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Planning failed: {str(e)}",
        )

    return {
        "dataset_version_id": str(
            dataset_version_id
        ),
        "analytics_plan": plan,
    }