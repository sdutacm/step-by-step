import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from loguru import logger
from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.dependencies.permissions import require_group_admin
from app.services.importer import import_oj_accounts
from db.models import Group, ImportRecord, User
from db.session import get_db
from schemas.import_record import (
    ImportRecordListResponse,
    ImportRecordResponse,
    ImportResult,
)

router = APIRouter(prefix="/api/groups", tags=["group-import"])


@router.post(
    "/{group_id}/import",
    response_model=ImportResult,
    status_code=status.HTTP_201_CREATED,
)
async def import_oj_accounts_to_group(
    group_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_group_admin),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Import OJ accounts: group_id={group_id}, user={current_user.username}"
    )

    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be Excel format (.xlsx or .xls)",
        )

    file_content = await file.read()

    try:
        result = import_oj_accounts(
            db=db,
            group_id=group_id,
            imported_by=current_user.id,
            file_content=file_content,
        )
    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Import failed: {str(e)}",
        )

    return ImportResult(
        total=result.total,
        success=result.success,
        skipped=result.skipped,
        success_list=result.success_list,
        skipped_list=result.skipped_list,
        errors=result.errors,
    )


@router.get("/{group_id}/import-templates", status_code=status.HTTP_200_OK)
async def download_import_template(
    group_id: int,
    current_user: User = Depends(require_group_admin),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Download import template: group_id={group_id}, user={current_user.username}"
    )

    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    wb = Workbook()
    ws = wb.active
    ws.title = "OJ Accounts"

    headers = ["source", "username", "nickname"]
    ws.append(headers)

    example_data = [
        ["vj", "example_user_1", "张三"],
        ["sdut", "example_user_2", ""],
    ]
    for row in example_data:
        ws.append(row)

    for col in ws.columns:
        for cell in col:
            if cell.row == 1:
                cell.font = cell.font.copy(bold=True)

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=import_template.xlsx"},
    )


@router.get("/{group_id}/import-records", response_model=ImportRecordListResponse)
async def list_import_records(
    group_id: int,
    current_user: User = Depends(require_group_admin),
    db: Session = Depends(get_db),
):
    logger.info(
        f"List import records: group_id={group_id}, user={current_user.username}"
    )

    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    records = (
        db.query(ImportRecord)
        .filter(ImportRecord.group_id == group_id)
        .order_by(ImportRecord.created_at.desc())
        .all()
    )

    return ImportRecordListResponse(
        items=[
            ImportRecordResponse(
                id=r.id,
                group_id=r.group_id,
                imported_by=r.imported_by,
                source=r.source,
                total_count=r.total_count,
                success_count=r.success_count,
                skip_count=r.skip_count,
                error_detail=r.error_detail,
                created_at=r.created_at,
            )
            for r in records
        ]
    )
