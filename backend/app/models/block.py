from sqlalchemy.orm import Mapped, mapped_column, relationship


class Block:
    # Builder position
    pos_x: Mapped[float] = mapped_column(default=0, server_default="0")
    pos_y: Mapped[float] = mapped_column(default=0, server_default="0")