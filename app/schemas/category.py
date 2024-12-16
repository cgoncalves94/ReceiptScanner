from pydantic import BaseModel

from ..models.receipt import Category as DBCategory


class CategoryBase(BaseModel):
    name: str
    description: str


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True
        model = DBCategory
