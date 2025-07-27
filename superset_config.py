# Filename: superset_config.py
import os

# A function to determine the database connection URI
def get_env_variable(var_name, default_value=None):
    return os.environ.get(var_name, default_value)

# The database URI for Superset's metadata
# We will pass the credentials using environment variables from docker-compose
SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{get_env_variable('DB_USER')}:{get_env_variable('DB_PASS')}@{get_env_variable('DB_HOST')}:{get_env_variable('DB_PORT')}/{get_env_variable('DB_NAME')}"

# A new, strong secret key. This MUST be set in the environment.
SECRET_KEY = get_env_variable('SUPERSET_SECRET_KEY')

# You can add other configurations here if needed
# For example, to enable template processing in SQL Lab
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
}