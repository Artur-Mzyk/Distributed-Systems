import pandas as pd

from sqlalchemy import create_engine
from database_architecture import create_architecture
from database_upload import upload_data
from database_queries import DatabaseQueries

if __name__ == "__main__":
    db_string = "postgresql://postgres:postgres@localhost:5432/postgres"
    engine = create_engine(db_string)

    create_architecture(engine=engine)
    upload_data(engine=engine)

    """
    An example query for a client that retrieves information about available objects in its 
    area within a selected time window, which can be the refresh frequency of the client.
    """
    DQ = DatabaseQueries(engine=engine)
    print(DQ.select_data_for_client(client_range=250,
                                    client_location=[0, 0],
                                    time_window=pd.DateOffset(minutes=5)))
