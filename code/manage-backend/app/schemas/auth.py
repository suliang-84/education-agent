from pydantic import BaseModel, Field


class LoginReq(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class TokenResp(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒
    admin: "AdminInfo"


class AdminInfo(BaseModel):
    id: int
    username: str
    display_name: str
    role: str


TokenResp.model_rebuild()
