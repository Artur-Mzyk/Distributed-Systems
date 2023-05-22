import pandas as pd
from datetime import datetime, timedelta
from pandas import DateOffset, DataFrame
from sqlalchemy.engine import Engine
from sqlalchemy import Table, MetaData, select, and_, DateTime, cast, insert, func
from typing import List, Dict


class DatabaseQueries:
    def __init__(self, engine: Engine):
        """
        A class for performing database queries.

        :param engine: The SQLAlchemy engine to use for connecting to the database.
        """
        self.engine = engine

        self.space_info_source = Table('space_info_source', MetaData(), autoload=True, autoload_with=engine)
        self.space_info_result = Table('space_info_result', MetaData(), autoload=True, autoload_with=engine)

    def get_space_data_in_client_range(self, client_range: int, client_location: List[int],
                                       time_window: DateOffset) -> DataFrame:
        """Retrieve selected data for a client within the given range, location, and time window.

        :param client_range: Integer representing the range around the client's location.
        :param client_location: List of two integers representing the x and y coordinates of the client's location.
        :param time_window: DateOffset object representing the time window for retrieving data.
        :return: DataFrame containing selected data for the client.
        """
        stmt = (
            select([
                self.space_info_source.columns.object_id,
                self.space_info_source.columns.x_localization,
                self.space_info_source.columns.y_localization
            ])
            .where(
                and_(
                    self.space_info_source.columns.x_localization.between(
                        client_location[0] - client_range,
                        client_location[0] + client_range
                    ),
                    self.space_info_source.columns.y_localization.between(
                        client_location[1] - client_range,
                        client_location[1] + client_range
                    ),
                    cast(self.space_info_source.columns.sample_date, DateTime).between(
                        datetime.now() - time_window,
                        datetime.now() + time_window
                    )
                )
            )
        )
        return pd.DataFrame(self.engine.execute(stmt).fetchall())

    def add_server_read_positions_info(self, data_to_upload: List[Dict]) -> None:
        """Add information about server read positions to the database.

        :param data_to_upload: A list of dictionaries containing position data.
        :return: None
        """
        stmt = (
            insert(self.space_info_result)
            .values(data_to_upload)
        )
        self.engine.execute(stmt)

    def get_grouped_information_of_objects_localization(self, time_window: DateOffset) -> List[Dict]:
        """Get grouped information of objects localization within a specified time window.

        :param time_window: The time window to consider.
        :return: List of dictionary containing the object IDs and average localization values.
        """
        stmt = select([
            self.space_info_source.columns.object_id,
            func.avg(self.space_info_source.c.x_localization).label('x_localization'),
            func.avg(self.space_info_source.c.y_localization).label('y_localization')
        ]).where(
            and_(
                cast(self.space_info_source.columns.sample_date, DateTime) >= datetime.now() - time_window,
                cast(self.space_info_source.columns.sample_date, DateTime) <= datetime.now(),
                func.sqrt(
                    func.power(
                        self.space_info_source.c.x_localization - self.space_info_source.alias().c.x_localization, 2) +
                    func.power(
                        self.space_info_source.c.y_localization - self.space_info_source.alias().c.y_localization, 2)
                ) <= 1.5 * self.space_info_source.columns.speed)
        ).group_by(
            self.space_info_source.c.object_id
        )
        return pd.DataFrame(self.engine.execute(stmt).fetchall()).to_dict(orient='records')

    def get_result(self) -> DataFrame:
        """Get the result from the space_info_result table.

        :return: DataFrame: A DataFrame containing the object IDs, x localization, and y localization.
        """
        stmt = (
            select([
                self.space_info_result.c.object_id,
                self.space_info_result.c.x_localization,
                self.space_info_result.c.y_localization
            ])
        )
        return pd.DataFrame(self.engine.execute(stmt).fetchall())
