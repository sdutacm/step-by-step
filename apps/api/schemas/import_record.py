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


class ImportResultSuccessItem(BaseModel):
    source: str
    username: str
    nickname: str | None = None


class ImportResultSkippedItem(BaseModel):
    source: str
    username: str
    nickname: str | None = None
    reason: str


class ImportResult(BaseModel):
    total: int
    success: int
    skipped: int
    success_list: list[ImportResultSuccessItem] = []
    skipped_list: list[ImportResultSkippedItem] = []
    errors: list[dict] = []


class ImportError(BaseModel):
    row: int
    username: str
    error: str
