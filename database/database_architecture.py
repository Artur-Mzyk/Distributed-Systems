from sqlalchemy import Column, Integer, DateTime, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.engine import Engine

Base = declarative_base()


class SpaceDataGenerator(Base):
    """
    Class representing space information table in the database. Client get information from this serwer.
    """

    __tablename__ = 'space_data_generator'

    index = Column(Integer, primary_key=True)
    object_id = Column(Integer)
    speed = Column(Float)
    direction = Column(Float)
    x_localization = Column(Integer)
    y_localization = Column(Integer)
    sample_date = Column(DateTime)

    def __repr__(self):
        """
        Return a string representation of the SpaceInfo object.
        """
        return "<SpaceDataGenerator(index={0}, object_id={1}, speed={2}, direction={3}, x_localization={4}, y_localization={5}, sample_date={6})>".format(
            self.index,
            self.object_id,
            self.speed,
            self.direction,
            self.x_localization,
            self.y_localization,
            self.sample_date
        )


class DataCollector(Base):
    """
    Class representing space information table in the database. Serwer store information on this table.
    """

    __tablename__ = 'data_collector'

    index = Column(Integer, primary_key=True)
    object_id = Column(Integer)
    speed = Column(Float)
    x_localization = Column(Integer)
    y_localization = Column(Integer)
    receive_date = Column(DateTime)

    def __repr__(self):
        """
        Return a string representation of the SpaceInfo object.
        """
        return "<DataCollector(index={0}, object_id={1}, speed={2}, x_localization={3}, y_localization={4}, receive_date={5})>".format(
            self.index,
            self.object_id,
            self.speed,
            self.x_localization,
            self.y_localization,
            self.receive_date
        )


class FilteredResults(Base):
    """
    Class representing space information table in the database. Serwer store information on this table.
    """

    __tablename__ = 'filtered_results'

    index = Column(Integer, primary_key=True)
    object_id = Column(Integer)
    speed = Column(Float)
    x_localization = Column(Integer)
    y_localization = Column(Integer)
    receive_date = Column(DateTime)

    def __repr__(self):
        """
        Return a string representation of the SpaceInfo object.
        """
        return "<FilteredResults(index={0}, object_id={1}, speed={2}, x_localization={3}, y_localization={4}, receive_date={5})>".format(
            self.index,
            self.object_id,
            self.speed,
            self.x_localization,
            self.y_localization,
            self.receive_date
        )


def create_architecture(engine: Engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
