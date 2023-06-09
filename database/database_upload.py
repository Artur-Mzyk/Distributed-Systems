import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
from random import uniform, randint, choice
from sqlalchemy.engine import Engine
from src.config import SPACE_RANGE, GENERATED_OBJECTS_NUMBER, MIN_NUMBER_OF_SAMPLES, MAX_NUMBER_OF_SAMPLES, \
    MAX_START_TRAJECTORY_OFFSET_SECONDS, GENERATED_ANOMALY_NUMBER
from typing import List, Tuple


class DatabaseUpload:
    def __init__(self, engine: Engine):
        """A class for performing database sample data uploading.

        :param engine: SQLAlchemy Engine object representing the database connection.
        """
        self.engine = engine
        self.data_to_upload = pd.DataFrame(
            columns=['object_id', 'speed', 'direction', 'x_localization', 'y_localization', 'sample_date'])

    def upload_data(self):
        """Upload the generated data to the database."""
        self.generate_data_to_upload()
        self.refactor_data_to_upload()
        self.data_to_upload.to_sql('space_data_generator', con=self.engine, if_exists='append', index=True)

    def refactor_data_to_upload(self):
        """Refactor the data to be uploaded.

        Round the 'speed' column to two decimal places and convert 'x_localization' and 'y_localization'
        columns to integers.
        """
        self.data_to_upload['speed'] = np.round(self.data_to_upload['speed'], 2)
        self.data_to_upload['direction'] = np.round(self.data_to_upload['direction'], 2)
        self.data_to_upload['x_localization'] = self.data_to_upload['x_localization'].astype('int')
        self.data_to_upload['y_localization'] = self.data_to_upload['y_localization'].astype('int')

    def generate_data_to_upload(self) -> None:
        """Generate dataframes with trajectory points for uploading.

        :return: None
        """
        dataframes_line_trajectory = [generate_trajectory_points(_) for _ in range(GENERATED_OBJECTS_NUMBER)]
        dataframes_anomaly_trajectory = [generate_trajectory_points_anomaly(_) for _ in range(GENERATED_OBJECTS_NUMBER, GENERATED_OBJECTS_NUMBER + GENERATED_ANOMALY_NUMBER)]
        self.data_to_upload = pd.concat([*dataframes_line_trajectory, *dataframes_anomaly_trajectory], ignore_index=True)
        print(self.data_to_upload)

    def plot_uploaded_data(self, minutes_offset: int):
        """Generate a plot of uploaded data
        """
        fig, ax = plt.subplots()
        sample_date = datetime.now() + pd.DateOffset(minutes=minutes_offset)
        sns.scatterplot(data=self.data_to_upload[self.data_to_upload.sample_date <= sample_date], x='x_localization',
                        y='y_localization', hue='object_id', ax=ax)
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        ax.grid(True)
        ax.set(xlim=(SPACE_RANGE[0], SPACE_RANGE[2]),
               ylim=(SPACE_RANGE[1], SPACE_RANGE[3]),
               title='Generated space trajectory: {}'.format(sample_date.time()))
        plt.show()


def generate_trajectory_points(object_id: int):
    """Generate trajectory points for a specific object.

    :param object_id: ID of the object.
    :return: DataFrame containing the generated trajectory points.
    """
    number_of_sample = randint(MIN_NUMBER_OF_SAMPLES, MAX_NUMBER_OF_SAMPLES)
    x_location, y_location, speed, direction = generate_line_trajectory_points(number_of_sample=number_of_sample - 1)
    start_date = datetime.now() + pd.DateOffset(seconds=randint(0, MAX_START_TRAJECTORY_OFFSET_SECONDS))
    datetime_array = pd.date_range(start=start_date,
                                   end=start_date + pd.DateOffset(seconds=speed * number_of_sample / 10),
                                   periods=number_of_sample)

    generated_data = pd.DataFrame({'object_id': object_id,
                                   'speed': speed,
                                   'direction': direction,
                                   'x_localization': x_location,
                                   'y_localization': y_location,
                                   'sample_date': datetime_array})
    return generated_data


def generate_line_trajectory_endpoints() -> Tuple[int, int, int, int]:
    """Generate random line trajectory endpoints.

    :return: tuple containing start_x, start_y, end_x, end_y coordinates of the points on the line.
    """
    directions = {
        'left': lambda: (SPACE_RANGE[0], uniform(SPACE_RANGE[1], SPACE_RANGE[3]), SPACE_RANGE[2], uniform(SPACE_RANGE[1], SPACE_RANGE[3])),
        'right': lambda: (SPACE_RANGE[2], uniform(SPACE_RANGE[1], SPACE_RANGE[3]), SPACE_RANGE[0], uniform(SPACE_RANGE[1], SPACE_RANGE[3])),
        'top': lambda: (uniform(SPACE_RANGE[0], SPACE_RANGE[2]), SPACE_RANGE[3], uniform(SPACE_RANGE[0], SPACE_RANGE[2]), SPACE_RANGE[1]),
        'bottom': lambda: (uniform(SPACE_RANGE[0], SPACE_RANGE[2]), SPACE_RANGE[1], uniform(SPACE_RANGE[0], SPACE_RANGE[2]), SPACE_RANGE[3])
    }
    return directions[choice(['left', 'right', 'top', 'bottom'])]()


def generate_lines(start_x:int, start_y:int, end_x:int, end_y:int, number_of_sample: int):
    speed = np.hypot((end_x - start_x), (end_y - start_y)) / number_of_sample
    direction = np.arctan2((end_x - start_x), (end_y - start_y))

    x_shift = (end_x - start_x) / number_of_sample
    y_shift = (end_y - start_y) / number_of_sample

    x_values = [start_x + i * x_shift for i in range(number_of_sample + 1)]
    y_values = [start_y + i * y_shift for i in range(number_of_sample + 1)]

    return x_values, y_values, speed, direction


def generate_line_trajectory_points(number_of_sample: int) -> Tuple[List, List, float, float]:
    """Generate random line trajectory.

    :param number_of_sample: Number of points to generate on the line.
    :return: tuple: Two lists containing the x and y coordinates of the points on the line.
    """
    return generate_lines(*generate_line_trajectory_endpoints(), number_of_sample=number_of_sample)


def generate_anomaly_trajectory_points(number_of_sample: int) -> Tuple[List, List, List, List]:
    """Generate anomaly line trajectory.

    :param number_of_sample: Number of points to generate on the line.
    :return: tuple: Two lists containing the x and y coordinates of the points on the line.
    """

    anomaly_point_x, anomaly_point_y = (
        uniform(SPACE_RANGE[0], SPACE_RANGE[2]), uniform(SPACE_RANGE[1], SPACE_RANGE[3]))

    start_x, start_y, end_x, end_y = generate_line_trajectory_endpoints()

    line_before_anomaly = generate_lines(start_x=start_x,
                                         end_x=int(anomaly_point_x),
                                         start_y=start_y,
                                         end_y=int(anomaly_point_y),
                                         number_of_sample=number_of_sample // 2)
    line_after_anomaly = generate_lines(start_x=int(anomaly_point_x),
                                        end_x=end_x,
                                        start_y=int(anomaly_point_y),
                                        end_y=end_y,
                                        number_of_sample=number_of_sample - (number_of_sample // 2))
    return line_before_anomaly[0] + line_after_anomaly[0][1:], line_before_anomaly[1] + line_after_anomaly[1][1:], [line_before_anomaly[2], line_after_anomaly[2]], [line_before_anomaly[3], line_after_anomaly[3]]


def generate_trajectory_points_anomaly(object_id: int):
    """Generate trajectory points for a specific object.

    :param object_id: ID of the object.
    :return: DataFrame containing the generated trajectory points.
    """
    number_of_sample = randint(MIN_NUMBER_OF_SAMPLES, MAX_NUMBER_OF_SAMPLES)
    x_location, y_location, speed, direction = generate_anomaly_trajectory_points(number_of_sample=number_of_sample - 1)
    start_date = datetime.now() + pd.DateOffset(seconds=randint(0, MAX_START_TRAJECTORY_OFFSET_SECONDS))
    datetime_array = pd.date_range(start=start_date,
                                   end=start_date + pd.DateOffset(seconds=np.mean(speed) * number_of_sample / 10),
                                   periods=number_of_sample)

    generated_data1 = pd.DataFrame({'object_id': object_id,
                                    'speed': speed[0],
                                    'direction': direction[0],
                                    'x_localization': x_location[:(number_of_sample - 1) // 2],
                                    'y_localization': y_location[:(number_of_sample - 1) // 2],
                                    'sample_date': datetime_array[:(number_of_sample - 1) // 2]})

    generated_data2 = pd.DataFrame({'object_id': object_id,
                                    'speed': speed[1],
                                    'direction': direction[1],
                                    'x_localization': x_location[(number_of_sample - ((number_of_sample - 1) // 2)) - 1:],
                                    'y_localization': y_location[(number_of_sample - ((number_of_sample - 1) // 2)) - 1:],
                                    'sample_date': datetime_array[(number_of_sample - ((number_of_sample - 1) // 2)) - 1:]})
    return pd.concat([generated_data1, generated_data2], ignore_index=True)


def upload_data(engine: Engine):
    DU = DatabaseUpload(engine)
    DU.upload_data()
    DU.plot_uploaded_data(minutes_offset=10)
