from fastapi import APIRouter, Request, status

router = APIRouter()


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(request: Request):
    """Create new user. (Not implemented)"""
    return {"message": "Not implemented"}


@router.post("/login/access-token")
async def login_access_token(request: Request):
    """OAuth2 token login. (Not implemented)"""
    return {"message": "Not implemented"}
