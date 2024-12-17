from datetime import datetime
import pandas as pd
from datetime import date, timedelta
from . import configs
import time
from requests.auth import HTTPBasicAuth
import sqlite3
import requests
from decouple import config
from sqlalchemy import create_engine, Column, String, Date, Integer, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from celery import shared_task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Monkey-patch requests to disable SSL verification globally
requests.packages.urllib3.disable_warnings()
requests.Session.verify = False



# Initialize SQLAlchemy
engine = create_engine(configs.DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()


# Define the User model
class User(Base):
    __tablename__ = 'users'

    user_id = Column(String, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    phone = Column(String)
    org_unit_name = Column(String)
    org_unit_id = Column(String)
    telegram = Column(String)

# Define the alerts table using SQLAlchemy ORM
class Alert(Base):
    __tablename__ = 'alerts'
    trackedEntityInstance = Column(String, primary_key=True)
    disease_name = Column(String)
    alert_disease = Column(String)
    alert_id = Column(String)
    notificationDate = Column(Date)
    org_unit_name = Column(String)
    org_unit_id = Column(String)
    week = Column(String)
    status = Column(String)


class Location(Base):
    __tablename__ = 'locations'
    province = Column(String)
    district = Column(String)
    district_id = Column(String, primary_key=True)

# Create the table if it doesn't exist
Base.metadata.create_all(engine)

# # Create the alerts table if it doesn't exist
# def create_alert_tbl():
#     Base.metadata.create_all(engine)

# 1. Fetch users in the group
def get_users_in_group(dhis_url, username, password, user_group_id):
    url = f"{dhis_url}/api/userGroups/{user_group_id}.json?fields=users[id,displayName]"
    response = requests.get(url, auth=HTTPBasicAuth(username, password), verify=False)
    
    if response.status_code == 200:
        return response.json().get('users', [])
    else:
        print(f"Failed to fetch users. Status Code: {response.status_code}")
        return []

# 2. Get user details (org unit, phone, email, telegram)
def get_user_details(user_id, dhis_url, username, password):
    #print(f"Fetching details for user: {user_id}")
    url = f"{dhis_url}/api/users/{user_id}.json?fields=id,firstName,surname,email,phoneNumber,telegram,organisationUnits[id,displayName],attributeValues[value,attribute[name]]"
    response = requests.get(url, auth=HTTPBasicAuth(username, password), verify=False)
    
    if response.status_code == 200:
        data = response.json()

        # Extract capture org units (first assigned org unit, if multiple)
        org_unit = data.get("organisationUnits", [{}])[0]
        org_unit_name = org_unit.get("displayName", "")
        org_unit_id = org_unit.get("id", "")       

        # Prepare user information dictionary
        user_info = {
            "user_id": data.get("id"),
            "first_name": data.get("firstName"),
            "last_name": data.get("surname"),
            "email": data.get("email"),
            "phone": data.get("phoneNumber"),
            "org_unit_name": org_unit_name,
            "org_unit_id": org_unit_id,
            "telegram": data.get("telegram")
        }
        return user_info
    else:
        print(f"Failed to fetch user {user_id}. Status Code: {response.status_code}")
        return None


def get_alert_users(org_id, field):
    # Use a context manager to handle the session automatically
    logger.info(f"WE ARE HERE_________________OU:{org_id}###########")

    fefch_field = getattr(User, field)

    with Session() as session:
        # Query the users table based on the provided org_unit_id
        try:
            users = (
                session.query(User.first_name, fefch_field)
                .filter(User.org_unit_id == org_id)
                .filter(fefch_field.isnot(None))
                .all()
            )

            return users
        except Exception as e:
            logger.error(f"Error Fetching data from DB for {org_id}: {e}", exc_info=True)

    

# 3. Save or update user details in the PostgreSQL database
def save_user_to_db(user_data):
    with Session() as session:
        try:
            # Check if user already exists
            user = session.query(User).filter_by(user_id=user_data["user_id"]).first()
            
            if user:
                # Update existing user
                for key, value in user_data.items():
                    setattr(user, key, value)
            else:
                # Add new user
                user = User(**user_data)
                session.add(user)

            session.commit()
        except Exception as e:
            print(f"Failed to save user {user_data['user_id']}: {e}")
            session.rollback()


# Save or update an alert in the database
def save_alert_to_db(trackedEntityInstance, disease_name, alert_disease, alert_id, enrollmentDate, org_unit_name, org_unit_id, week):
    with Session() as session:
        alert = session.query(Alert).filter_by(trackedEntityInstance=trackedEntityInstance).first()

        # If alert exists, update it; otherwise, create a new one
        if alert:
            alert.disease_name = disease_name
            alert.alert_disease = alert_disease
            alert.alert_id = alert_id
            alert.notificationDate = enrollmentDate
            alert.org_unit_name = org_unit_name
            alert.org_unit_id = org_unit_id
            alert.week = week
        else:
            alert = Alert(
                trackedEntityInstance=trackedEntityInstance,
                disease_name=disease_name,
                alert_disease=alert_disease,
                alert_id=alert_id,
                notificationDate=enrollmentDate,
                org_unit_name=org_unit_name,
                org_unit_id=org_unit_id,
                week=week,
                status="VERIFICATION_STATUS_PENDING"
            )
            session.add(alert)        
        session.commit()

# Check if an alert exists for the given disease, org unit, and week
def check_alert_in_db(disease_name, org_unit_id, week):
    with Session() as session:
        count = session.query(func.count(Alert.trackedEntityInstance)).filter_by(
            disease_name=disease_name,
            org_unit_id=org_unit_id,
            week=week
        ).scalar()

        return count

# DATE EPI WEEK FUNCTION
def get_recent_epi_weeks(weeks: int):
    today = date.today()
    
    def get_epi_week(input_date):
        # Find the first Sunday of the year
        year_start = date(input_date.year, 1, 1)
        first_sunday = year_start + timedelta(days=(6 - year_start.weekday()))

        # Handle edge case: if the input date is before the first epi week
        if input_date < first_sunday:
            # Return the last epi week of the previous year
            dec_31 = date(input_date.year - 1, 12, 31)
            return get_epi_week(dec_31)

        days_since_first_sunday = (input_date - first_sunday).days
        epi_week = (days_since_first_sunday // 7) + 1
        epi_year = input_date.year

        # Handle the case where the date falls into the next year's first week
        if epi_week > 52:
            next_year_start = date(input_date.year + 1, 1, 1)
            next_year_first_sunday = next_year_start + timedelta(days=(6 - next_year_start.weekday()))
            if input_date >= next_year_first_sunday:
                epi_week = 1
                epi_year += 1

        return epi_year, epi_week

    def format_epi_week(year, week):
        return f"{year}W{week:02d}"

    # Calculate the last completed Sunday (end of last epi week)
    last_sunday = today - timedelta(days=(today.weekday() + 1) % 7)

    # Get the requested number of epi weeks before the current week
    epi_weeks = []
    for i in range(weeks):
        target_sunday = last_sunday - timedelta(days=i * 7)
        epi_year, epi_week = get_epi_week(target_sunday)
        epi_weeks.append(format_epi_week(epi_year, epi_week))

    # Reverse to ensure the list is in ascending order
    return epi_weeks[::-1]


def fetch_aggregated_data(api, dx, pe, ou):
    # Construct the dimensions parameter
    dx_dimension = f"dx:{','.join(dx)}" # List of DEs - Surveillance diseases
    pe_dimension = f"pe:{','.join(pe)}" # One week, multiple weeks
    ou_dimension = f"ou:{ou}" # Org unit or org unit level - District level?
    
#     print(ou_dimension)

    # Set up the parameters for the API call
    params = {
        'dimension': f"{dx_dimension},{pe_dimension},{ou_dimension}",
        'displayProperty': 'NAME',
        'includeNumDen': 'true',
        'skipMeta': 'true'
    }


    retries = 0
    while retries <= 5:
        try:
            # API call to analytics endpoint
            response = api.get('analytics', params=params)
            response.raise_for_status()
            data = response.json()
#             print(data)
            break
        except Exception as e:
            print(f"Error fetching analytics data: {e}")
            time.sleep(10)
            retries += 1
            data = None

    if not data:
        return None
    else:
        # Convert the response 'rows' to a DataFrame
        headers = [header['name'] for header in data.get('headers', [])]
        rows = data.get('rows', [])
        df = pd.DataFrame(rows, columns=headers)

        # Rename the relevant columns
        df.rename(columns={'dx': 'dataElement', 'ou': 'orgUnit'}, inplace=True)

        # Keep only the first 4 columns: dataElement, pe, orgUnit, value
        df = df[['dataElement', 'pe', 'orgUnit', 'value']]

        # df should be a table with columns: dataElement (UID), orgUnit (UID), pe (ISO format), value
        df.to_csv('./data/aggregate_data.csv', index=False)
        return df


# GET ORG UNIT, DATA ELEMENT AND CATEGORY NAMES
# Helper function to get names from API
def get_names(api, endpoint, uids):
    params = {
        'filter': f"id:in:[{','.join(uids)}]",
        'fields': 'id,name'
    }
    response = api.get_paged(endpoint, params=params,page_size=100, merge=True)
    items = response.get(endpoint, [])
    id_name_mapping = {item['id']: item['name'] for item in items}

    return id_name_mapping

# Replace UIDs of dataElement, orgUnit and categoryOptionCombo with names using API lookup
def replace_uids_with_names(api, df):    
    if 'dataElement' in df:
        # Get unique UIDs dataElement
        de_uids = df['dataElement'].unique().tolist()
        # Fetch names for dataElements, organisationUnits, categoryOptionCombos
        des = get_names(api, 'dataElements', de_uids)
        # Replace UIDs with names in the dataframe 
        df['dataElement_name'] = df['dataElement'].map(des)
        
    if 'orgUnit' in df:
        # Get unique UIDs orgUnit
        ou_uids = df['orgUnit'].unique().tolist()
        print(len(ou_uids))
        # Fetch names for dataElements, organisationUnits, categoryOptionCombos
        ous = get_names(api, 'organisationUnits', ou_uids)
        # Replace UIDs with names in the dataframe 
        df['orgUnit_name'] = df['orgUnit'].map(ous)
    
    if 'categoryOptionCombo' in df:
        # Get unique UIDs categoryOptionCombo
        coc_uids = df['categoryOptionCombo'].unique().tolist()
        # Fetch names for dataElements, organisationUnits, categoryOptionCombos
        cocs = get_names(api, 'categoryOptionCombos', coc_uids)
        # Replace UIDs with names in the dataframe 
        df['categoryOptionCombo'] = df['categoryOptionCombo'].map(cocs)    

    return df


def generate_alert_id(): 
    logger.info(f'REQUESTING TEI ID FROM: {configs.DEV_DHIS_URL}')
    DHIS2_USERNAME = configs.PROD_DHIS_USER
    DHIS2_PASSWORD = configs.PROD_DHIS_PASSWORD
    try:
        # 1. Generate Alert ID
        alert_response = requests.get(
                f"{configs.DEV_DHIS_URL}/api/trackedEntityAttributes/rfg6oQYBIKk/generate.json",
                auth=HTTPBasicAuth(DHIS2_USERNAME, DHIS2_PASSWORD), verify=False
            )
        alert_id = alert_response.json()["value"]
        logger.info(f"ALERT ID FETCHED {alert_id}....")
        return alert_id
    except requests.exceptions.RequestException as error:
        logger.error(error)

def get_dhis2Id():
    DHIS2_USERNAME = configs.PROD_DHIS_USER
    DHIS2_PASSWORD = configs.PROD_DHIS_PASSWORD
    logger.info(f'FETCHING TEI ID fron DHIS2')
    url = f'{configs.DEV_DHIS_URL}/api/system/id'
    headers = {
    'Content-type': 'application/json',
    'Accept': 'application/json'
    }

    try:
        response = requests.get(
            url,
            auth=(DHIS2_USERNAME, DHIS2_PASSWORD),
            headers=headers, verify=False
            )

        if response.status_code == 200:            
            json = response.json()
#             print(json)
            dhis2_id = json['codes'][0]
            logger.info(f"TEI UID FETCHED {dhis2_id}....")
            return dhis2_id
        else:
            logger.error(f'Could not retrive DHIS2 IDs, {response.status_code}:{response.text}')            

    except requests.exceptions.RequestException as error:
        logger.error(error)    



def post_to_alert_program(org_unit_id, org_unit_name, disease_id, week):
    DHIS2_USERNAME = configs.PROD_DHIS_USER
    DHIS2_PASSWORD = configs.PROD_DHIS_PASSWORD
    DHIS2_URL = configs.DEV_DHIS_URL
    logger.info(f'LOGGING____POST 2 DHIS: {DHIS2_URL}')

    file_path = './data/alert_conditions.csv'
    df = pd.read_csv(file_path)
    row = df[df['id'] == disease_id]

    # Assign the value to alert_disease variable if the row is found
    alert_disease = row['nmc_diagnosis'].values[0] if not row.empty else None
    disease_name = row['name'].values[0] if not row.empty else None
    
    logger.info(f"#####------------\n")
    alert_id = generate_alert_id()
    logger.info(f"DONE.......ALERT ID:{alert_id}")
    logger.info("######------------\n")
    tei_id = get_dhis2Id()     
    if tei_id: 
        logger.info(f"DONE:....TEI:{tei_id}")
        logger.info(f"DONE:....TEI:{tei_id}")    
        # Get today's date
        today = datetime.today()
        # Format the date to 'YYYY-MM-DD' DHIS2 DATE FORMAT
        enrollmentDate = today.strftime('%Y-%m-%d')

        data = {
            "trackedEntityInstance": tei_id,
            "trackedEntityType":"QH1LBzGrk5g",
            "orgUnit":org_unit_id,
            "program": "xDsAFnQMmeU",
            "attributes":[
                {"attribute": "YDUOTtNQm99", "value": enrollmentDate},
                {"attribute":"CJkJraokrXn","value":"PHEOC_WATCH"},
                {"attribute":"d1AUyuOOo62","value":"VERIFICATION_STATUS_PENDING"},
                {"attribute":"kAI5cvh9Tmd","value":alert_disease},
                {"attribute":"rfg6oQYBIKk","value":alert_id}
                ]
            }
        
        logger.info(f"TEI POST DATA......:\n{data}")
        
        #f"{configs.DEV_DHIS_URL}/api/trackedEntityInstances",

        try:
            logger.info(f'LOGGING____POST 2 DHIS: {DHIS2_URL}')
            response = requests.post(
                f"{DHIS2_URL}/api/trackedEntityInstances",
                auth=HTTPBasicAuth(DHIS2_USERNAME, DHIS2_PASSWORD),
                headers={
                    'Content-type': 'application/json',
                    'Accept': 'application/json'
                },
                data=json.dumps(data), verify=False
            )

            if response.status_code == 200:
                logger.info(f'STATUS: Posted to DHIS2 Alert Program successfully.\n {response.text}')
                logger.info(f'STARTING ENROLMENT FOR {tei_id}......')
                data_enroll = {
                    "trackedEntityInstance":tei_id,
                    "program":"xDsAFnQMmeU",
                    "status":"ACTIVE",
                    "orgUnit":org_unit_id,
                    "enrollmentDate":enrollmentDate,
                    "incidentDate":enrollmentDate
                }
                try:
                    logger.info(f"ENROLMENT POST DATA......:\n{data_enroll}")
                    logger.info(f'LOGGING____POST 2 DHIS: {DHIS2_URL}')
                    res = requests.post(
                        f"{DHIS2_URL}/api/enrollments",
                        auth=HTTPBasicAuth(DHIS2_USERNAME, DHIS2_PASSWORD),
                        headers={
                            'Content-type': 'application/json',
                            'Accept': 'application/json'
                        },
                        data=json.dumps(data_enroll), verify=False
                    )
                    if res.status_code == 201:
                        save_alert_to_db(tei_id, disease_name, alert_disease, alert_id, enrollmentDate, org_unit_name, org_unit_id, week)

                except requests.exceptions.RequestException as error:
                    print(error)        
                
                return tei_id, alert_id
            else:
                print(f'Could not CREATE TE in DHIS2: \n {response.text}')

        except requests.exceptions.RequestException as error:
            print(error)


# EMAIL BODY TEMPLATES:
@shared_task
def send_email_alert(SMTP_SERVER, port, sender_email, password, recipient_emails, subject, body_html):
    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_emails
    # msg['To'] = ', '.join(recipient_emails)
    msg['Subject'] = subject

    # Attach the HTML body
    msg.attach(MIMEText(body_html, 'html'))

    try:
        # Connect to the SMTP server and send the email
        with smtplib.SMTP_SSL(SMTP_SERVER, port) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_emails, msg.as_string())
        print(f"Email sent successfully to {recipient_emails}")
    except Exception as e:
        print('Ooh Shit!')
        print(f"Failed to send email to {recipient_emails}. Error: {e}")
        
# Function to create HTML body from a template
def create_email_body(msg, facility_df_with_names):
    # HTML template
    html_template = f"""
    <html>
    <body>
        {msg}
        <p>Please find below the list of facilities with reported cases:</p>
        <table border="1" style="border-collapse: collapse; width: 80%;">
            <thead>
                <tr>
                    <th>Facility</th>
                    <th> # Cases</th>
                </tr>
            </thead>
            <tbody>
                {"".join([f"<tr><td>{row['orgUnit_name']}</td><td>{row['value']}</td></tr>" for index, row in facility_df_with_names.iterrows()])}
            </tbody>
        </table>
        <p>Thank you for your attention to this matter.</p>

        <p> Best regards, <br /> ZNPHI SDI/SPIM Team.</p>
    </body>
    </html>
    """
    return html_template


def create_email_body1(msg):
    # HTML template
    html_template = f"""
    <html>
    <body>
        {msg}
        <p>Thank you for your attention to this matter.</p>
        <p> Best regards, <br /> ZNPHI SDI/SPIM Team.</p>
    </body>
    </html>
    """
    return html_template


@shared_task
def send_sms(phone, msg):
    logger.info('************STARTING SMS SENDING**************')
    data = {
        'username': configs.SMS_USER,
        'phone_number': f'[{phone}]',
        'message': msg,
        'message_type': "2",
        'certificate': configs.SMS_CERT
    }

    headers = {}

    response = requests.request("POST", configs.SMS_URL, headers=headers, data=data)
    logger.info(response.status_code)
    logger.info(response.text)

