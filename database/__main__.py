import pandas as pd
import seaborn as sns
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
