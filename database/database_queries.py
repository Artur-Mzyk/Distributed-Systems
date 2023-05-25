import pandas as pd
from datetime import datetime, timedelta
from pandas import DateOffset, DataFrame
from sqlalchemy.engine import Engine
from sqlalchemy import Table, MetaData, select, and_, DateTime, cast, insert, func
from typing import List, Dict
from random import randint
from src.config import MIN_NOISE_VAL, MAX_NOISE_VAL


class DatabaseQueries:
    def __init__(self, engine: Engine):
        """
        A class for performing database queries.

        :param engine: The SQLAlchemy engine to use for connecting to the database.
        """
        self.engine = engine

        self.space_data_generator = Table('space_data_generator', MetaData(), autoload=True, autoload_with=engine)
        self.data_collector = Table('data_collector', MetaData(), autoload=True, autoload_with=engine)
        self.filtered_results = Table('filtered_results', MetaData(), autoload=True, autoload_with=engine)

    def get_space_data_in_client_range(self, client_range: int, client_location: List[int],
                                       time_window: DateOffset) -> DataFrame:
        """Retrieve selected data for a client within the given range, location, and time window.

        :param client_range: Integer representing the range around the client's location.
        :param client_location: List of two integers representing the x and y coordinates of the client's location.
        :param time_window: DateOffset object representing the time window for retrieving data.
        :return: DataFrame containing selected data for the client with a noise in localization coordinates.
        """
        stmt = (
            select([
                self.space_data_generator.c.object_id,
                self.space_data_generator.c.speed,
                self.space_data_generator.c.direction,
                (self.space_data_generator.c.x_localization + randint(MIN_NOISE_VAL, MAX_NOISE_VAL)).label('x_localization'),
                (self.space_data_generator.c.y_localization + randint(MIN_NOISE_VAL, MAX_NOISE_VAL)).label('y_localization'),
                self.space_data_generator.c.sample_date.label('receive_date')
            ])
            .where(
                and_(
                    self.space_data_generator.columns.x_localization.between(
                        client_location[0] - client_range,
                        client_location[0] + client_range
                    ),
                    self.space_data_generator.columns.y_localization.between(
                        client_location[1] - client_range,
                        client_location[1] + client_range
                    ),
                    cast(self.space_data_generator.columns.sample_date, DateTime).between(
                        datetime.now() - time_window,
                        datetime.now()
                    )
                )
            )
        )
        data_in_client_range = pd.DataFrame(self.engine.execute(stmt).fetchall())
        if len(data_in_client_range) > 0:
            data_in_client_range.columns = ['object_id', 'speed', 'direction', 'x_localization', 'y_localization', 'receive_date']
        return data_in_client_range

    def add_server_read_positions_info(self, client_receive_data_to_upload: List[Dict]) -> None:
        """Add information about server read positions to the database.
        The data_collector connect all result for different source - clients

        :param client_receive_data_to_upload: A list of dictionaries containing position data.
        :return: None
        """
        stmt = (
            insert(self.data_collector)
            .values(client_receive_data_to_upload)
        )
        self.engine.execute(stmt)

    def grouped_information_of_objects_localization(self, time_window: DateOffset) -> None:
        """grouped information of objects localization within a specified time window and send to filtered_results.

        :param time_window: The time window to connect all the values in temporary table data_collector.
        :return: None
        """
        grouped_stmt = (
            select([
                self.data_collector.columns.object_id,
                func.avg(self.data_collector.c.x_localization).label('x_localization'),
                func.avg(self.data_collector.c.y_localization).label('y_localization')
            ])
            .where(
                and_(
                    cast(self.data_collector.columns.sample_date, DateTime) >= datetime.now() - time_window,
                    cast(self.data_collector.columns.sample_date, DateTime) <= datetime.now(),
                    func.hypot(
                        (self.data_collector.c.x_localization - self.data_collector.alias().c.x_localization),
                        (self.data_collector.c.y_localization - self.data_collector.alias().c.y_localization))
                    <= 1.5 * self.data_collector.columns.speed)
            )
            .group_by(
                self.data_collector.c.object_id
            )
        )

        upload_stmt = (
            insert(self.filtered_results)
            .values(pd.DataFrame(self.engine.execute(grouped_stmt).fetchall()).to_dict(orient='records'))
        )
        self.engine.execute(upload_stmt)

    def get_result(self) -> DataFrame:
        """Get the result from the filtered_results table.

        :return: DataFrame: A DataFrame containing the object IDs, x localization, and y localization.
        """
        # stmt = (
        #     select([
        #         self.filtered_results.columns.object_id,
        #         self.filtered_results.columns.x_localization,
        #         self.filtered_results.columns.y_localization
        #     ])
        # )
        stmt = (
            select([
                self.data_collector.columns.object_id,
                self.data_collector.columns.x_localization,
                self.data_collector.columns.y_localization
            ])
        )
        return pd.DataFrame(self.engine.execute(stmt).fetchall())
