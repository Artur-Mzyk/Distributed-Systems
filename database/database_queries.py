import pandas as pd
from datetime import datetime
from pandas import DateOffset, DataFrame
from sqlalchemy.engine import Engine
from sqlalchemy import Table, MetaData, select, and_, DateTime, cast
from typing import List


class DatabaseQueries:
    def __init__(self, engine: Engine):
        """
        A class for performing database queries.

        :param engine: The SQLAlchemy engine to use for connecting to the database.
        """
        self.engine = engine

        self.space_info = Table('space_info', MetaData(), autoload=True, autoload_with=engine)

    def select_data_for_client(self, client_range: int, client_location: List[int], time_window: DateOffset) -> DataFrame:
        """Retrieve selected data for a client within the given range, location, and time window.

        :param client_range: Integer representing the range around the client's location.
        :param client_location: List of two integers representing the x and y coordinates of the client's location.
        :param time_window: DateOffset object representing the time window for retrieving data.
        :return: DataFrame containing selected data for the client.
        """
        stmt = (
            select([
                self.space_info.columns.object_id,
                self.space_info.columns.x_localization,
                self.space_info.columns.y_localization
            ])
            .where(
                and_(
                    self.space_info.columns.x_localization.between(
                        client_location[0] - client_range,
                        client_location[0] + client_range
                    ),
                    self.space_info.columns.y_localization.between(
                        client_location[1] - client_range,
                        client_location[1] + client_range
                    ),
                    cast(self.space_info.columns.sample_date, DateTime).between(
                        datetime.now() - time_window,
                        datetime.now() + time_window
                    )
                )
            )
        )
        return pd.DataFrame(self.engine.execute(stmt).fetchall())
