from sqlmodel import SQLModel, Field


class SignupDto(SQLModel):
    name: str = Field(description="Name")
    username: str = Field(description="Username")
    email: str = Field(description="Email address")
    password: str = Field(description="Password")


class LoginDto(SQLModel):
    username: str = Field(description="Email address")
    password: str = Field(description="Password")
