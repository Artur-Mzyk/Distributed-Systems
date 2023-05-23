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
        self.space_receive_info = Table('space_receive_info', MetaData(), autoload=True, autoload_with=engine)
        self.space_info_result = Table('space_info_result', MetaData(), autoload=True, autoload_with=engine)

    # Każdy klient zaczytuje informację na podstawie jego parametrów
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
                self.space_info_source.columns.speed,
                self.space_info_source.columns.x_localization,
                self.space_info_source.columns.y_localization,
                self.space_info_source.columns.sample_date
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
                        datetime.now()
                    )
                )
            )
        )
        return pd.DataFrame(self.engine.execute(stmt).fetchall())

    # serwer otrzymane informację od klientów czyli to z powyższego zapytania wrzuca na bazę
    def add_server_read_positions_info(self, client_receive_data_to_upload: List[Dict]) -> None:
        """Add information about server read positions to the database.
        The space_receive_info connect all result for different source - clients

        :param client_receive_data_to_upload: A list of dictionaries containing position data.
        :return: None
        """
        stmt = (
            insert(self.space_receive_info)
            .values(client_receive_data_to_upload)
        )
        self.engine.execute(stmt)

    # po otrzymaniu informacji od klienta serwer grupuje dane na bazie i wysyła na wynikową bazę space_info_result
    def grouped_information_of_objects_localization(self, time_window: DateOffset) -> None:
        """grouped information of objects localization within a specified time window and send to space_info_result.

        :param time_window: The time window to connect all the values in temporary table space_receive_info.
        :return: None
        """
        grouped_stmt = (
            select([
                self.space_receive_info.columns.object_id,
                func.avg(self.space_receive_info.c.x_localization).label('x_localization'),
                func.avg(self.space_receive_info.c.y_localization).label('y_localization')
            ])
            .where(
                and_(
                    cast(self.space_receive_info.columns.sample_date, DateTime) >= datetime.now() - time_window,
                    cast(self.space_receive_info.columns.sample_date, DateTime) <= datetime.now(),
                    func.sqrt(
                        func.power(
                            self.space_receive_info.c.x_localization - self.space_receive_info.alias().c.x_localization,
                            2) + func.power(
                            self.space_receive_info.c.y_localization - self.space_receive_info.alias().c.y_localization,
                            2)
                    ) <= 1.5 * self.space_receive_info.columns.speed)
            )
            .group_by(
                self.space_receive_info.c.object_id
            )
        )

        upload_stmt = (
            insert(self.space_info_result)
            .values(pd.DataFrame(self.engine.execute(grouped_stmt).fetchall()).to_dict(orient='records'))
        )
        self.engine.execute(upload_stmt)

    # Wynikowe dane po zgrupowaniu są gotowe do wyświetlania na wynikowym wykresie. Moga być zaczytane w każdej chwili
    # i udostępnione klientowi w formie mapy.
    def get_result(self) -> DataFrame:
        """Get the result from the space_info_result table.

        :return: DataFrame: A DataFrame containing the object IDs, x localization, and y localization.
        """
        stmt = (
            select([
                self.space_info_result.columns.object_id,
                self.space_info_result.columns.x_localization,
                self.space_info_result.columns.y_localization
            ])
        )
        return pd.DataFrame(self.engine.execute(stmt).fetchall())
