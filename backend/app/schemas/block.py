from pydantic import BaseModel


class Block(BaseModel):
    pos_x: float = 0
    pos_y: float = 0
