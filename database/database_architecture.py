from sqlalchemy import Column, Integer, DateTime, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.engine import Engine

Base = declarative_base()


class SpaceInfo(Base):
    """
    Class representing space information table in the database.
    """

    __tablename__ = 'space_info'

    index = Column(Integer, primary_key=True)
    object_id = Column(Integer)
    speed = Column(Float)
    x_localization = Column(Integer)
    y_localization = Column(Integer)
    sample_date = Column(DateTime)

    def __repr__(self):
        """
        Return a string representation of the SpaceInfo object.
        """
        return "<SpaceInfo(index={0}, object_id={1}, speed={2}, x_localization={3}, y_localization={4}, sample_date={5})>".format(
            self.index,
            self.object_id,
            self.speed,
            self.x_localization,
            self.y_localization,
            self.sample_date
        )


def create_architecture(engine: Engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)