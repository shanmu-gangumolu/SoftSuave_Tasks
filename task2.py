# Final Code
# This Code Upto --->  user_id(UUID) , first_name , last_name, email , phone_number , created_at, updated_at

from typing import Annotated
from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, select, UniqueConstraint
from pydantic import field_validator, model_validator, ConfigDict
from email_validator import validate_email, EmailNotValidError
from sqlalchemy import create_engine, BigInteger, Column
import uuid

NOW_FACTORY = datetime.now

app = FastAPI()

class CreatedUpdatedAt(SQLModel):
    created_at: datetime = Field(default_factory = NOW_FACTORY)
    updated_at: datetime = Field(default_factory = NOW_FACTORY) 
    model_config = ConfigDict(validate_assignment=True)  

    @model_validator(mode="after") 
    @classmethod
    def update_updated_at(cls, obj: "CreatedUpdatedAt") -> "CreatedUpdatedAt":
        obj.model_config["validate_assignment"] = False
        obj.updated_at = NOW_FACTORY()
        obj.model_config["validate_assignment"] = True 
        return obj 
    
# Data Models
class UserBase(SQLModel):
    first_name: str = Field(index=True)
    last_name: str = Field(index=True)
    email: str = Field(index=True, unique=True)
    ph_number: int = Field(sa_column = Column(BigInteger, unique=True,index=True)) 

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        try:
            validate_email(value)
        except EmailNotValidError:
            raise ValueError("Invalid email format")
        return value 
    
    @field_validator("ph_number")
    @classmethod
    def validate_ph_number(cls, value: int) -> int:
        if not (1000000000 <= value <= 9999999999):
            raise ValueError("Phone number must be exactly 10 digits")
        return value
    

class User(UserBase, CreatedUpdatedAt, table=True):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", "ph_number"),) 
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True) 


class UserPublic(SQLModel):
    user_id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    ph_number: int
    created_at: datetime
    updated_at: datetime

class UserCreate(UserBase):
    pass

class UserUpdate(SQLModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    ph_number: int | None = None

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        if value is not None:
            try:
                validate_email(value)
            except EmailNotValidError:
                raise ValueError("Invalid email format")
        return value
    
    @field_validator("ph_number")
    @classmethod
    def validate_ph_number(cls, value: int) -> int:
        if value is not None and not (1000000000 <= value <= 9999999999):
            raise ValueError("Phone number must be exactly 10 digits")
        return value
    

MYSQL_USER = 'root'
MYSQL_PASSWORD = '#shanmu2003'
MYSQL_HOST = 'localhost'
MYSQL_PORT = '3306'
MYSQL_DATABASE = 'fastapi_db'

mysql_url = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

engine = create_engine(mysql_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/users/", response_model=UserPublic)
def create_user(user: UserCreate, session: SessionDep):
    db_user = User(**user.dict())
    session.add(db_user)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    session.refresh(db_user)
    return db_user


@app.get("/users/", response_model=list[UserPublic])
def read_users(session: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100):
    return session.exec(select(User).offset(offset).limit(limit)).all()


@app.get("/users/{user_id}", response_model=UserPublic)
def read_user(user_id: uuid.UUID, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.patch("/users/{user_id}", response_model=UserPublic)
def update_user(user_id: uuid.UUID, hero: UserUpdate, session: SessionDep):
    user_db = session.get(User, user_id)
    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")
    hero_data = hero.dict(exclude_unset=True)
    for key, value in hero_data.items():
        setattr(user_db, key, value)
    try:
        session.add(user_db)
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    session.refresh(user_db)
    return user_db


@app.delete("/users/{user_id}") 
def delete_user(user_id: uuid.UUID, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"ok": True} 