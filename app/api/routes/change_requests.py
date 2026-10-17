from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.db_models import ChangeRequest, Project
from app.schemas.database import ChangeRequestCreate, ChangeRequestRead, ChangeRequestUpdate

router = APIRouter(prefix="/api/v1/change-requests", tags=["change requests"])


@router.post("", response_model=ChangeRequestRead, status_code=status.HTTP_201_CREATED)
def create_change_request(
    payload: ChangeRequestCreate, db: Session = Depends(get_db)
) -> ChangeRequest:
    if db.get(Project, payload.project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Change request title cannot be blank.")

    item = ChangeRequest(
        project_id=payload.project_id,
        title=title,
        description=payload.description,
        status="draft",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=list[ChangeRequestRead])
def list_change_requests(
    project_id: UUID | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[ChangeRequest]:
    statement = select(ChangeRequest).order_by(ChangeRequest.created_at.desc())
    if project_id is not None:
        statement = statement.where(ChangeRequest.project_id == project_id)
    statement = statement.offset(offset).limit(limit)
    return list(db.scalars(statement).all())


@router.get("/{change_request_id}", response_model=ChangeRequestRead)
def get_change_request(
    change_request_id: UUID, db: Session = Depends(get_db)
) -> ChangeRequest:
    item = db.get(ChangeRequest, change_request_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Change request not found.")
    return item


@router.patch("/{change_request_id}", response_model=ChangeRequestRead)
def update_change_request(
    change_request_id: UUID,
    payload: ChangeRequestUpdate,
    db: Session = Depends(get_db),
) -> ChangeRequest:
    item = db.get(ChangeRequest, change_request_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Change request not found.")

    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="Provide at least one field to update.")
    for field in ("title", "status"):
        if field in changes:
            if changes[field] is None or not changes[field].strip():
                raise HTTPException(status_code=422, detail=f"{field.capitalize()} cannot be blank.")
            changes[field] = changes[field].strip()

    for field, value in changes.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{change_request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_change_request(
    change_request_id: UUID, db: Session = Depends(get_db)
) -> Response:
    item = db.get(ChangeRequest, change_request_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Change request not found.")
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
