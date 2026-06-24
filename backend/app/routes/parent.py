from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app import schemas, models
from backend.app.database import get_db

router = APIRouter(prefix="/api/parent", tags=["parent"])

@router.post("/login", response_model=schemas.ParentLoginResponse)
def parent_login(req: schemas.ParentLoginRequest, db: Session = Depends(get_db)):
    """
    Parent Login. Auto-registers alphanumeric password on first run for developer comfort!
    """
    parent = db.query(models.ParentAccount).first()
    if not parent:
        # First-time run: save this password as canonical, default to password-free
        new_parent = models.ParentAccount(password_hash=req.password, password_auth_required=False)
        db.add(new_parent)
        db.commit()
        return {"success": True, "token": "ccmed_parent_session_active"}
    
    # Bypass password verification if disabled by parent
    if not parent.password_auth_required:
        return {"success": True, "token": "ccmed_parent_session_active"}
    
    if parent.password_hash == req.password:
        return {"success": True, "token": "ccmed_parent_session_active"}
    
    raise HTTPException(status_code=401, detail="Invalid parent alphanumeric password.")
