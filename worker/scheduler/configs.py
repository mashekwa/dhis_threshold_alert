from decouple import config

# SMTP SERVER SETTINGS
SMTP_SERVER = config("SMTP_SERVER")
SMTP_PORT = config("SMTP_PORT")
SMTP_SENDER_EMAIL= config("SMTP_EMAIL") 
SMTP_PASSWORD = config("SMTP_PASSWORD")

# TELEGRAM SETTINGS
TELEGRAM_TOKEN = config("TELEGRAM_TOKEN")
TELE_GROUP = config("TELEGRAM_GROUP_ID")

# PROD eIDSR CREDENTIALS
PROD_DHIS_USER = config('DHIS2_USERNAME')
PROD_DHIS_PASSWORD= config('DHIS2_PASSWORD')
PROD_DHIS_URL = config('DHIS2_BASE_URL')
ROOT_ORGS = config('PARENT_ORG_UNITS') # Root Org Unit UID (COUNTRY)
DATASET = config('DATASET') # UID of IDSR DATASET
DEV_DHIS_URL = config('DEV_DHIS2_BASE_URL')
DATA_PULL_WEEKS = config('LAST_N_WEEKS')
ORG_UNIT_LEVEL = config('ORG_UNIT_LEVEL')
DATA_ELEMENTS = config('DATA_ELEMENTS')
DHIS_USERGROUP = config('DHIS_USERGROUP')

# SMS CONFIGS
SMS_URL= config('SMS_URL')
SMS_USER= config('SMS_USER')
SMS_CERT= config('SMS_CERT')

# Load the PostgreSQL connection string from the .env file
DB_URL = config('db')

one_suspected_diseases = config('one_suspected_diseases')
doubling_cases_diseases = config('doubling_cases_diseases')
increase_1_5x_diseases = config('increase_1_5x_diseases')
cluster_of_diseases = config('cluster_of_diseases')



