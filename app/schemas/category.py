from pydantic import BaseModel

from ..models.receipt import Category as DBCategory


class CategoryBase(BaseModel):
    name: str
    description: str


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    name: str | None = None
    description: str | None = None


class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True
        model = DBCategory
