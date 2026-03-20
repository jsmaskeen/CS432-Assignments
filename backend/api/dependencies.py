from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.security import decode_access_token
from db.session import get_db_session
from models.auth_credential import AuthCredential
from models.member import Member

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_member(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db_session),
) -> Member:
    subject = decode_access_token(token)
    if subject is None or not subject.isdigit():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    member_id = int(subject)
    member = db.scalar(select(Member).where(Member.MemberID == member_id))
    if member is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Member not found")

    return member


def get_current_credential(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db_session),
) -> AuthCredential:
    subject = decode_access_token(token)
    if subject is None or not subject.isdigit():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    member_id = int(subject)
    credential = db.scalar(select(AuthCredential).where(AuthCredential.MemberID == member_id))
    if credential is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credential not found")

    return credential
