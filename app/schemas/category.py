from pydantic import BaseModel


class CategoryBase(BaseModel):
    name: str
    description: str


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    name: str | None
    description: str | None


class CategoryRead(CategoryBase):
    id: int

    class Config:
        from_attributes = True
