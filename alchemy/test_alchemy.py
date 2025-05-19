from sqlalchemy.orm import DeclarativeBase, Mapped, Mapper, mapped_column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY


class EmptyBase(DeclarativeBase):
    __mapper_args__ = {"eager_defaults": True}
    __abstract__ = True

class DataColumnType(EmptyBase):
    """
    Represents the data type of a column.
    """

    __tablename__ = "data_column_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    test_: Mapped[str] = mapped_column(default=str)
    mapped_ardadb_types: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])




if __name__ == "__main__":
    d = DataColumnType(id=1)
    print(d.id)
    print(d.test_)
    print(d.mapped_ardadb_types)
