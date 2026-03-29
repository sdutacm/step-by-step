from datetime import datetime

from pydantic import BaseModel


class ImportRecordResponse(BaseModel):
    id: int
    group_id: int
    imported_by: int | None
    source: str
    total_count: int
    success_count: int
    skip_count: int
    error_detail: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ImportRecordListResponse(BaseModel):
    items: list[ImportRecordResponse]


class ImportResult(BaseModel):
    total: int
    success: int
    skipped: int
    errors: list[dict] = []


class ImportError(BaseModel):
    row: int
    username: str
    error: str
