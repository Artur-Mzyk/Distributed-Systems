import pandas as pd
import seaborn as sns
import datetime
from matplotlib import pyplot as plt

from sqlalchemy import create_engine
from database_architecture import create_architecture
from database_upload import upload_data
from database_queries import DatabaseQueries

if __name__ == "__main__":
    db_string = "postgresql://postgres:postgres@localhost:5432/postgres"
    engine = create_engine(db_string)

    create_architecture(engine=engine)
    upload_data(engine=engine)

    DQ = DatabaseQueries(engine=engine)
    i = 0
    delay_ = 0.5

    prev_anomalies = []
    while i < 1000:
        data_ = DQ.get_space_data_in_client_range(2000, client_location=[0, 0], time_window=pd.DateOffset(seconds=delay_))
        DQ.add_server_read_positions_info(data_.to_dict(orient='records'))
        DQ.grouped_information_of_objects_localization(time_window=pd.DateOffset(seconds=delay_))

        # Anomalies detection:
        anomalies = DQ.detecting_anomaly()
        if anomalies != prev_anomalies:
            detected_anomaly = list(set(anomalies) - set(prev_anomalies))
            if detected_anomaly:
                print("\n Detect anomaly: {0} at {1}".format(detected_anomaly, datetime.datetime.now()))
            prev_anomalies = anomalies
        plt.pause(delay_)
        i += 1
        print('.', end='')
