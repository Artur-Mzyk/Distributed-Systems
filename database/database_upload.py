import pandas as pd
import numpy as np
from datetime import datetime
from random import uniform, randint
from sqlalchemy.engine import Engine
from src.config import SPACE_RANGE


class DatabaseUpload:
    def __init__(self, engine: Engine):
        """A class for performing database sample data uploading.

        :param engine: SQLAlchemy Engine object representing the database connection.
        """
        self.engine = engine
        self.data_to_upload = pd.DataFrame(
            columns=['object_id', 'speed', 'x_localization', 'y_localization', 'sample_date'])

    def upload_data(self):
        """Upload the generated data to the database."""
        self.generate_data_to_upload()
        self.refactor_data_to_upload()
        self.data_to_upload.to_sql('space_info_source', con=self.engine, if_exists='append', index=True)

    def refactor_data_to_upload(self):
        """Refactor the data to be uploaded.

        Round the 'speed' column to two decimal places and convert 'x_localization' and 'y_localization'
        columns to integers.
        """
        self.data_to_upload['speed'] = np.round(self.data_to_upload['speed'], 2)
        self.data_to_upload['x_localization'] = self.data_to_upload['x_localization'].astype('int')
        self.data_to_upload['y_localization'] = self.data_to_upload['y_localization'].astype('int')

    def generate_data_to_upload(self, objects_number: int = 10):
        """Generate dataframes with trajectory points for uploading.

        :param objects_number: Number of objects for which trajectories are generated.
        """
        dataframes = [generate_trajectory_points(_) for _ in range(objects_number)]
        self.data_to_upload = pd.concat(dataframes, ignore_index=True)


def generate_random_trajectory_endpoints():
    """ Generate a straight line between two points within the specified rectangle."""
    x1, y1 = uniform(SPACE_RANGE[0], SPACE_RANGE[2]), uniform(SPACE_RANGE[1], SPACE_RANGE[3])
    x2, y2 = uniform(SPACE_RANGE[2], SPACE_RANGE[0]), uniform(SPACE_RANGE[3], SPACE_RANGE[1])

    return {'x_coords': [x1, x2], 'y_coords': [y1, y2]}


def generate_trajectory_points(object_id: int):
    """Generate trajectory points for a specific object.

    :param object_id: ID of the object.
    :return: DataFrame containing the generated trajectory points.
    """
    number_of_sample = randint(50, 100)
    endpoints = generate_random_trajectory_endpoints()
    x_location = np.linspace(start=endpoints['x_coords'][0], stop=endpoints['x_coords'][1], num=number_of_sample)
    y_location = np.linspace(start=endpoints['y_coords'][0], stop=endpoints['y_coords'][1], num=number_of_sample)

    x_diff = np.max(endpoints['x_coords']) - np.min(endpoints['x_coords'])
    y_diff = np.max(endpoints['y_coords']) - np.min(endpoints['y_coords'])
    speed = np.sqrt(x_diff ** 2 + y_diff ** 2) / number_of_sample

    start_date = datetime.now()
    datetime_array = pd.date_range(start=start_date,
                                   end=start_date + pd.DateOffset(seconds=speed * number_of_sample / 10),
                                   periods=number_of_sample)

    generated_data = pd.DataFrame({'object_id': object_id,
                                   'speed': speed,
                                   'x_localization': x_location,
                                   'y_localization': y_location,
                                   'sample_date': datetime_array})
    return generated_data


def upload_data(engine: Engine):
    DatabaseUpload(engine).upload_data()
