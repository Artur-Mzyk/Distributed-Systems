import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from sqlalchemy import create_engine
from database_architecture import create_architecture
from database_upload import upload_data
from database_queries import DatabaseQueries


def plot_result():
    df = DQ.get_result()
    sns.scatterplot(data=df, x='x_localization', y='y_localization', hue='object_id')
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.grid(True)
    plt.xlim(-1000, 1000)
    plt.ylim(-1000, 1000)
    plt.show()
    plt.clf()


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
    # print(DQ.get_space_data_in_client_range(client_range=250,
    #                                         client_location=[0, 0],
    #                                         time_window=pd.DateOffset(minutes=5)))

    for i in range(10):
        plt.pause(0.5)
        data_to_upload = DQ.get_grouped_information_of_objects_localization(time_window=pd.DateOffset(seconds=0.5))
        DQ.add_server_read_positions_info(data_to_upload)
        print(i, '\t', data_to_upload)
        plot_result()
