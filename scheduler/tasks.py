import os
import json
import logging
import pandas as pd
from dhis2 import Api
from datetime import datetime, timedelta
from celery.utils.log import get_task_logger
from scheduler import celery_app
from decouple import config
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from celery import shared_task
import requests
from .alert_program import fetch_data, fetch_users_and_save_details, cluster_of_cases, one_suspected_case,check_1_5x_increase,get_double_cases

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
task_logger = get_task_logger(__name__)

# Initialize DHIS2 API
DHIS2_BASE_URL = config("DHIS2_BASE_URL")
DHIS2_USERNAME = config("DHIS2_USERNAME")
DHIS2_PASSWORD = config("DHIS2_PASSWORD")
user_group_id = "CcYgPmHP0GN"
api = Api(f'{DHIS2_BASE_URL}', DHIS2_USERNAME, DHIS2_PASSWORD)

# Configuration for data elements and organization units
DATA_ELEMENTS = json.loads(config("DATA_ELEMENTS", "{}"))
ORG_UNIT_LEVEL = "LEVEL-Dz7Sm3imvLU"
LAST_N_WEEKS = int(config("LAST_N_WEEKS", 5))
TELEGRAM_GROUP_ID = config("TELEGRAM_GROUP_ID")

def get_last_n_weeks():
    """Calculate periods for the last N weeks."""
    current_date = datetime.now()
    return [(current_date - timedelta(weeks=i)).strftime('%Y%m%d') for i in range(LAST_N_WEEKS)]


@celery_app.task(name='get_users')
def get_users():
    fetch_users_and_save_details(DHIS2_BASE_URL, DHIS2_USERNAME, DHIS2_PASSWORD, user_group_id)

@celery_app.task(name='run_alerts')
def run_alerts():
    # Import tasks within function to avoid circular imports
    from .alert_program import fetch_data   

    # Fetch data
    parquet_file = fetch_data()

    one_suspected_diseases = config('one_suspected_diseases').split(',')
    doubling_cases_diseases = config('doubling_cases_diseases').split(',')
    increase_1_5x_diseases = config('1_5x_increase_diseases').split(',')
    cluster_of_diseases = config('cluster_of_diseases').split(',')
    
    if parquet_file:
        df_with_names = pd.read_parquet(f'./data/{parquet_file}')
        if df_with_names is None:
            print("No data fetched.")
        else:
            # df_with_names.to_csv("./data/df_with_name.csv")
            logger.info(f"DATA COUNT........{len(df_with_names)}")
            # Call alert functions
            one_suspected_case(df_with_names, one_suspected_diseases)
            get_double_cases(df_with_names, doubling_cases_diseases)
            check_1_5x_increase(df_with_names, increase_1_5x_diseases)
            
            # For clusters of diseases
            for item in cluster_of_diseases:
                disease, num = item.split('_')
                cluster_of_cases(df_with_names, disease, int(num))

    else:
        logger.error("Failed to fetch data; alerts not run.")
