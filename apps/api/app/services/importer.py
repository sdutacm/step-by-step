import io
import json
from dataclasses import dataclass, field

import openpyxl
from sqlalchemy.orm import Session

from db.models import GroupUser, ImportRecord, SourceUser, User
from db.models.group_user import GroupRole
from sources import sources


@dataclass
class ImportRow:
    source: str
    username: str
    nickname: str | None = None


@dataclass
class ImportError:
    row: int
    username: str
    error: str


@dataclass
class ImportResult:
    total: int = 0
    success: int = 0
    skipped: int = 0
    success_list: list = field(default_factory=list)
    skipped_list: list = field(default_factory=list)
    errors: list = field(default_factory=list)


VALID_SOURCES = {s.source for s in sources}


def parse_excel(file_content: bytes) -> list[ImportRow]:
    if not file_content:
        raise ValueError("File content is empty")

    if file_content[:2] == b"PK":
        wb = openpyxl.load_workbook(io.BytesIO(file_content))
    else:
        raise ValueError(
            f"Invalid file format. Expected xlsx (starts with PK), got: {file_content[:20]}"
        )

    ws = wb.active
    rows: list[ImportRow] = []

    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if row[0] is None and row[1] is None:
            continue
        source = str(row[0]).strip() if row[0] else ""
        username = str(row[1]).strip() if row[1] else ""
        nickname = str(row[2]).strip() if row[2] and row[2] else None

        if source and username:
            rows.append(ImportRow(source=source, username=username, nickname=nickname))

    return rows


def import_oj_accounts(
    db: Session,
    group_id: int,
    imported_by: int | None,
    file_content: bytes,
) -> ImportResult:
    import_rows = parse_excel(file_content)
    result = ImportResult(total=len(import_rows))

    for idx, row in enumerate(import_rows):
        try:
            if row.source not in VALID_SOURCES:
                result.errors.append(
                    {
                        "row": idx + 2,
                        "source": row.source,
                        "username": row.username,
                        "error": f"Invalid source: {row.source}",
                    }
                )
                continue

            existing_source_user = (
                db.query(SourceUser)
                .filter(
                    SourceUser.source == row.source, SourceUser.username == row.username
                )
                .first()
            )

            if existing_source_user:
                existing_user = existing_source_user.user
                if existing_user and not existing_user.is_temp:
                    result.skipped += 1
                    result.skipped_list.append(
                        {
                            "source": row.source,
                            "username": row.username,
                            "nickname": row.nickname,
                            "reason": "Already bound to a real user",
                        }
                    )
                    continue

                if existing_user and existing_user.is_temp:
                    existing_group_user = (
                        db.query(GroupUser)
                        .filter(
                            GroupUser.group_id == group_id,
                            GroupUser.user_id == existing_user.id,
                        )
                        .first()
                    )
                    if existing_group_user:
                        result.skipped += 1
                        result.skipped_list.append(
                            {
                                "source": row.source,
                                "username": row.username,
                                "nickname": row.nickname,
                                "reason": "Already in this group",
                            }
                        )
                        continue

                    new_group_user = GroupUser(
                        group_id=group_id,
                        user_id=existing_user.id,
                        role=GroupRole.MEMBER,
                    )
                    db.add(new_group_user)
                    result.skipped += 1
                    result.skipped_list.append(
                        {
                            "source": row.source,
                            "username": row.username,
                            "nickname": row.nickname,
                            "reason": "Added to group (was ghost user)",
                        }
                    )
                    continue

            temp_user = User(
                username=f"_temp_{row.source}_{row.username}_{imported_by or 0}",
                hashed_password="",
                nickname=row.nickname,
                is_temp=True,
            )
            db.add(temp_user)
            db.flush()

            source_user = SourceUser(
                user_id=temp_user.id,
                source=row.source,
                username=row.username,
                nickname=row.nickname,
            )
            db.add(source_user)

            group_user = GroupUser(
                group_id=group_id,
                user_id=temp_user.id,
                role=GroupRole.MEMBER,
            )
            db.add(group_user)

            result.success += 1
            result.success_list.append(
                {
                    "source": row.source,
                    "username": row.username,
                    "nickname": row.nickname,
                }
            )

        except Exception as e:
            result.errors.append(
                {
                    "row": idx + 2,
                    "source": row.source,
                    "username": row.username,
                    "error": str(e),
                }
            )

    import_record = ImportRecord(
        group_id=group_id,
        imported_by=imported_by,
        source="mixed",
        total_count=result.total,
        success_count=result.success,
        skip_count=result.skipped,
        error_detail=json.dumps(
            [
                {"row": e.row, "username": e.username, "error": e.error}
                for e in result.errors
            ]
        )
        if result.errors
        else None,
    )
    db.add(import_record)
    db.commit()

    return result
