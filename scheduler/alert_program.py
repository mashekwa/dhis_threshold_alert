from .utils import get_recent_epi_weeks, fetch_aggregated_data, replace_uids_with_names
from decouple import config
from datetime import datetime
import pandas as pd
from dhis2 import Api
import logging
import requests
from .utils import get_users_in_group, get_user_details, save_user_to_db, send_email_alert,create_email_body, create_email_body1, post_to_alert_program, create_alert_tbl, get_recent_epi_weeks, check_alert_in_db
from celery import shared_task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize DHIS2 API
DHIS2_BASE_URL = config("DHIS2_BASE_URL")
DHIS2_USERNAME = config("DHIS2_USERNAME")
DHIS2_PASSWORD = config("DHIS2_PASSWORD")
api = Api(f"{DHIS2_BASE_URL}", DHIS2_USERNAME, DHIS2_PASSWORD)

TELEGRAM_TOKEN = config("TELEGRAM_TOKEN")
@shared_task
def send_telegram_message(user_id, message):  
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': user_id,
        'text': message
    }

    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message. Error: {response.text}")

# 4. Fetch and print details of all users in the group
def fetch_users_and_save_details(dhis_url, username, password, user_group_id):
    users = get_users_in_group(dhis_url, username, password, user_group_id)
    for user in users:
        user_details = get_user_details(user["id"], dhis_url, username, password)
        if user_details:
            print(f"User: {user_details['first_name']} {user_details['last_name']}")
            print(f"  Email: {user_details['email']}")
            print(f"  Phone: {user_details['phone']}")
            print(f"  Org Unit: {user_details['org_unit_name']} (ID: {user_details['org_unit_id']})")
            print(f"  Telegram: {user_details['telegram']}\n")

            # Save the user details to the database
            save_user_to_db(user_details)


def fetch_data():
    logger.info("STARTING DHIS2 DATA PULL.....")
    # logger.info(f"URL.....{DHIS2_BASE_URL}")
    # logger.info(f"USERNAME.....{DHIS2_USERNAME}")
    # logger.info(f"PASSWORD.....{DHIS2_PASSWORD}")


    weeks = int(config('LAST_N_WEEKS'))

    # DISEASE LIST FROM CSV
    file_path = './data/alert_conditions.csv'
    de_df = pd.read_csv(file_path)
    dx_ids = [';'.join(de_df['id'].tolist())] # Join the 'id' column values with ';' separator for the 'dx' parameter


    pe = get_recent_epi_weeks(weeks)

    if len(pe) > 1:
        final_pe =';'.join(pe)
        pe = [final_pe]
    else:
        pe = pe

    dx_list = dx_ids
    periods = pe  # Example of relative periods 
    district_level_uid = 'LEVEL-Dz7Sm3imvLU'  # UID for the district level  
    df_analytics = fetch_aggregated_data(api, dx_list, periods, ou=district_level_uid)

    if not df_analytics.empty:
        df_with_names = replace_uids_with_names(api, df_analytics)
        df_with_names['year'] = df_with_names['pe'].str[:4]  # First 4 characters represent the year
        df_with_names['week'] = df_with_names['pe'].str[5:]  # Characters after 'W' represent the week

        # Convert the 'year' and 'week' columns to integers if necessary
        df_with_names['year'] = df_with_names['year'].astype(int)
        df_with_names['week'] = df_with_names['week'].astype(int)
        df_with_names = df_with_names.sort_values(by = ['dataElement_name','orgUnit', 'year','week'], ascending = [True,True, True, True])

        # Generate file name based on the current date
        today_str = datetime.now().strftime('%Y%m%d')
        parquet_file = f"data_{today_str}.parquet"

        # Save DataFrame to Parquet
        df_with_names.to_parquet(f'./data/{parquet_file}', index=False)
        logger.info(f"Data saved to {parquet_file}")

        return parquet_file
    
    else:
        print("No data fetched")
        return None


# DATA REFORMAT FUNCTION
def get_disease_data(df, dataElements, weeks):    
    df= df[df['dataElement'].isin(dataElements)]
    df = df[df['pe'].isin(weeks)]
    
    
    # Sort the DataFrame by orgUnit, dataElement, and week in descending order
    df_sorted = df.sort_values(by=['orgUnit', 'week'], ascending=[True, False])
    df_sorted['value'] = df_sorted['value'].astype(int)

    return df_sorted

def get_users_to_alert():
    pass


def one_suspected_case(df, dx):    
    # dataElements_list = ['lI3EMAbSqPD','zBFmdwpO2LZ']  # LIST DE ids for diseases that needs 1 case for notification
    dataElements_list = dx
    number_of_weeks = get_recent_epi_weeks(1) # 1, means just need to newest week. 1 WEEK    
    
    df_x = get_disease_data(df, dataElements_list, number_of_weeks)
    
    if not df_x.empty:        
        final_df = df_x[df_x['value'] >= 1]


        # Alert people in district
        for index, row in final_df.iterrows():
            district_uid = row['orgUnit']
            district_name = row['orgUnit_name']          
            disease_name = row['dataElement_name']
            disease_id = row['dataElement']
            period = row['pe']        
            value = row['value']

            dx = [f'{disease_id}']
            pe = [f'{period}']
            ou = f'LEVEL-MQLiogB9XBV;{district_uid}'

            logger.info(f"POSTING TO ALERT PROGRAM")
            check_record = check_alert_in_db(disease_name, district_uid, period)
            if check_record >=1:
                print(check_record)
                print('ALERT ALREADY IN DB')          
            else:
                print('CONTINUE!')
                #Post to DHIS2
                tei_id, alert_id = post_to_alert_program(district_uid, district_name, disease_id, period)
                logger.info(f"TEI:.....{tei_id}")

                # Get Facility level data
                facility_data_df = fetch_aggregated_data(api, dx, pe, ou)
                facility_df_with_names = replace_uids_with_names(api, facility_data_df)    

                
            
                # SEND TO NATIONAL LEVEL PEOPLE AS WELL
                # nationa_uid = rootOU

                #  # Check if the district UID is in the email_to_alert dictionary
                # if district_uid in email_to_alert or nationa_uid in email_to_alert:
                #     recipient_emails = email_to_alert.get(district_uid, email_to_alert.get(nationa_uid, []))
                #     print(recipient_emails)

                #     #Create the email subject and HTML body
                #     subject = f"eIDSR Alert: {value} case(s) of {disease_name} detected in {district_name}"
                #     body_html = create_email_body(district_name, disease_name, value, facility_df_with_names)

                #     # Send the email
                #     send_email_alert(
                #         smtp_server=smtp_server,
                #         port=port,
                #         sender_email=sender_email,
                #         password=password,
                #         recipient_emails=recipient_emails,
                #         subject=subject,
                #         body_html=body_html
                #     )        
                
                # else:
                #     print("district_uid does not exist in emails_to_alert")

                # # SEND TELEGRAM
                # if district_uid in telegram_to_alert or nationa_uid in telegram_to_alert:
                #     recipient_telegram = telegram_to_alert.get(district_uid, telegram_to_alert .get(nationa_uid, []))
                #     print(recipient_telegram)

                #     for id in recipient_telegram:              
                #         # Send Telegram alert
                #         telegram_message = f"eIDSR Alert: \n{value} case(s) of {disease_name} detected in {district_name}"
                #         send_telegram_message(id, telegram_message)     
                
                # else:
                #     print("district_uid does not exist in emails_to_alert")

                # TEST TELEGRAM ALERT
                tei_link = f"https://dev.eidsr.znphi.co.zm/dhis-web-tracker-capture/index.html#/dashboard?tei={tei_id}&program=xDsAFnQMmeU&ou={district_uid}"
                telegram_message = f"eIDSR Alert | {alert_id}: \n{value} case(s) of {disease_name} detected in {district_name}. \n \n{tei_link}"
                send_telegram_message.delay('-1002490743936', telegram_message)
    else:
        print(f"No Data for {dataElements_list} in Week:{number_of_weeks[0]}")



# DOUBLING OF CASES.
def get_double_cases(df, dx):
    dataElements_list = dx
    # dataElements_list = ['eDgoVyohFOK']  # LIST DE ids for diseases that need 1 case for notification
    number_of_weeks = get_recent_epi_weeks(2)  # 1 means just need the newest week. 1 WEEK

    df_x = get_disease_data(df, dataElements_list, number_of_weeks)
    logger.info(f"DF DATA......{len(df_x)}")
    
    for dis in dataElements_list:
        dz = df_x [df_x ['dataElement'] == dis].copy()
    
        if dz.empty:
            return pd.DataFrame(), "Empty dataset provided"

        # Convert 'value' column to numeric type
        dz['value'] = pd.to_numeric(dz['value'], errors='coerce')

        # Pivot the data for easier comparison
        pivot_data = dz.pivot_table(
            index=['dataElement', 'orgUnit', 'orgUnit_name', 'dataElement_name'],
            columns='week',
            values='value',
            aggfunc='sum'
        ).reset_index()

        # Ensure the weeks are sorted and only two weeks are present
        weeks = sorted(pivot_data.columns[4:])
        if len(weeks) < 2:
            return pd.DataFrame(), "Not enough weeks of data for comparison"

        earlier_week, later_week = weeks[0], weeks[-1]

        # Calculate increase and the doubling condition
        pivot_data['increase'] = pivot_data[later_week] - pivot_data[earlier_week]
        doubling_condition = pivot_data[later_week] >= 2 * pivot_data[earlier_week]

        # Filter rows with doubling cases
        doubling_cases = pivot_data[doubling_condition].copy()

        # Add a 'weeks' column containing the two weeks separated by a comma
        doubling_cases.loc[:, 'weeks'] = f"{earlier_week}, {later_week}"

        # Select relevant columns to return
        result = doubling_cases[
            ['dataElement', 'orgUnit', 'dataElement_name', 'orgUnit_name', 'weeks', 'increase']
        ]

        alert_week = get_recent_epi_weeks(1) 
        alert_week = alert_week[0]
        logger.info(f"WEEK............{alert_week}")

        if not result.empty: 
            logger.info("STARTING NOTIFIER")
            for index, row in result.iterrows():
                district_name = row['orgUnit_name']
                district_uid = row['orgUnit']        
                disease_name = row['dataElement_name']
                week_1, week_2 = result['weeks'].iloc[0].split(', ')       
                increase = row['increase']
                disease_id = row['dataElement']

                logger.info(f"POSTING TO ALERT PROGRAM...............{alert_week}")
                check_record = check_alert_in_db(disease_name, district_uid, alert_week)
                if check_record >=1:
                    print(check_record)
                    print('ALERT ALREADY IN DB')          
                else:
                    print('CONTINUE!')
                    #Post to DHIS2
                    tei_id, alert_id = post_to_alert_program(district_uid, district_name, disease_id, alert_week)
                    logger.info(f"TEI:.....{tei_id}")
                
                    tei_link = f"https://dev.eidsr.znphi.co.zm/dhis-web-tracker-capture/index.html#/dashboard?tei={tei_id}&program=xDsAFnQMmeU&ou={district_uid}"
                    msg =f'eIDSR Alert | {alert_id}: \nThere has been doubling of cases in {district_name} for {disease_name} from Week {week_1} to week {week_2}. The cases increased by {increase}. \n \n{tei_link}'

                    # nationa_uid = rootOU
                    # #if district_uid in emails_to_alert:
                    # if district_uid in email_to_alert or nationa_uid in email_to_alert:
                    #     recipient_emails = email_to_alert.get(district_uid, email_to_alert.get(nationa_uid, []))
                    #     print(recipient_emails)

                    #     #Create the email subject and HTML body
                    #     subject = f"eIDSR Alert: Doubling of cases in {district_name} for {disease_name}"
                    #     body_html = create_email_body1(msg)

                    #     # Send the email
                    #     send_email_alert(
                    #         smtp_server=smtp_server,
                    #         port=port,
                    #         sender_email=sender_email,
                    #         password=password,
                    #         recipient_emails=recipient_emails,
                    #         subject=subject,
                    #         body_html=body_html
                    #     )        
                    
                    # else:
                    #     print("district_uid does not exist in emails_to_alert")


                    # # SEND TELEGRAM
                    # if district_uid in telegram_to_alert or nationa_uid in telegram_to_alert:
                    #     recipient_telegram = telegram_to_alert.get(district_uid, telegram_to_alert .get(nationa_uid, []))
                    #     print(recipient_telegram)

                    #     for id in recipient_telegram:              
                    #         # Send Telegram alert
                    #         send_telegram_message(id, msg)         
                    
                    # else:
                    #     print("district_uid does not exist in emails_to_alert")
                    send_telegram_message.delay('-1002490743936', msg)

            return result, f"Comparison between weeks {earlier_week} and {later_week}"
        else:
            logger.info("No Disease Data to Alert")        
    
    return [], "No data found for the specified diseases."



# 1.5 TIMES vs THE BASELINE (PAST 3 WEEKS' AVERAGE)
def check_1_5x_increase(df, dx):
    dataElements_list = dx  # List of dataElement IDs for diseases requiring notification
    number_of_weeks = get_recent_epi_weeks(4)  # Get 4 weeks of data (3 for baseline, 1 to compare)

    # Filter data for relevant disease and weeks
    df_x = get_disease_data(df, dataElements_list, number_of_weeks)

    # Ensure 'value' is numeric
    df_x['value'] = pd.to_numeric(df_x['value'], errors='coerce').fillna(0)

    # Group by orgUnit and week, pivoting to get weeks as columns
    grouped = df_x.groupby(['orgUnit', 'week'])['value'].sum().unstack()

    # Ensure the weeks are sorted
    weeks = sorted(grouped.columns)
    if len(weeks) < 4:
        return pd.DataFrame(), "Not enough weeks of data for comparison (need at least 4 weeks)"

    # Calculate the baseline (average of the first 3 weeks) and multiply by 1.5
    baseline_weeks = weeks[:3]
    comparison_week = weeks[-1]
    baseline = grouped[baseline_weeks].mean(axis=1) * 1.5

    # Extract the number of cases for the comparison week
    new_week_cases = grouped[comparison_week]

    # Filter districts with new_week cases >= 1.5 times the baseline
    increased_districts = new_week_cases[new_week_cases >= baseline].index

    # Create a filtered DataFrame with relevant columns
    filtered_df = df_x[df_x['orgUnit'].isin(increased_districts)]

    # Add the baseline (1.5x) and new_week cases to the DataFrame
    filtered_df = filtered_df.assign(
        baseline=filtered_df['orgUnit'].map(baseline),  # 1.5x baseline
        new_week=filtered_df['orgUnit'].map(new_week_cases)
    )

    # Select only the required columns
    result_df = filtered_df[['dataElement', 'orgUnit', 'dataElement_name', 'orgUnit_name', 'baseline', 'new_week']].drop_duplicates()

    alert_week = get_recent_epi_weeks(1) 
    alert_week = alert_week[0]
    logger.info(f"WEEK............{alert_week}")
    if not result_df.empty: 
        for index, row in result_df.iterrows():
            district_name = row['orgUnit_name']          
            disease_name = row['dataElement_name']
            district_uid = row['orgUnit']
            disease_id = row['dataElement']

            logger.info(f"POSTING TO ALERT PROGRAM...............{alert_week}")
            check_record = check_alert_in_db(disease_name, district_uid, alert_week)
            if check_record >=1:
                print(check_record)
                print('ALERT ALREADY IN DB')          
            else:
                print('CONTINUE!')
                #Post to DHIS2
                tei_id, alert_id = post_to_alert_program(district_uid, district_name, disease_id, alert_week)
                logger.info(f"TEI:.....{tei_id}")
                
                tei_link = f"https://dev.eidsr.znphi.co.zm/dhis-web-tracker-capture/index.html#/dashboard?tei={tei_id}&program=xDsAFnQMmeU&ou={district_uid}"
                msg =f"eIDSR Alert | {alert_id}: \nThere has been more cases in {district_name} for {disease_name} after comparison between week {comparison_week} and baseline (1.5x average of weeks {', '.join(map(str, baseline_weeks))}). \n \n{tei_link}"
                

            
                # nationa_uid = rootOU
                # #if district_uid in emails_to_alert:
                # if district_uid in email_to_alert or nationa_uid in email_to_alert:
                #     recipient_emails = email_to_alert.get(district_uid, email_to_alert.get(nationa_uid, []))
                #     print(recipient_emails)

                #     #Create the email subject and HTML body
                #     subject = f"eIDSR Alert: Doubling of cases in {district_name} for {disease_name}"
                #     body_html = create_email_body1(msg)

                #     # Send the email
                #     send_email_alert(
                #         smtp_server=smtp_server,
                #         port=port,
                #         sender_email=sender_email,
                #         password=password,
                #         recipient_emails=recipient_emails,
                #         subject=subject,
                #         body_html=body_html
                #     )        
                    
                # else:
                #     print("district_uid does not exist in emails_to_alert")


                # # SEND TELEGRAM
                # if district_uid in telegram_to_alert or nationa_uid in telegram_to_alert:
                #     recipient_telegram = telegram_to_alert.get(district_uid, telegram_to_alert .get(nationa_uid, []))
                #     print(recipient_telegram)

                #     for id in recipient_telegram:              
                #         # Send Telegram alert
                #         send_telegram_message(id, msg)         
                    
                #     else:
                #         print("district_uid does not exist in emails_to_alert")
                # else:
                #     print("district_uid does not exist in emails_to_alert")
                send_telegram_message.delay('-1002490743936', msg)

    return result_df, f"Comparison between week {comparison_week} and baseline (1.5x average of weeks {', '.join(map(str, baseline_weeks))})"



# def cluster_of_cases(df, disease, num):
#     dataElements_list = [f'{disease}']  # List of dataElement IDs for diseases requiring notification
#     # print(dataElements_list)
#     number_of_weeks = get_recent_epi_weeks(1)
#     # print(number_of_weeks)

#     # Filter data for relevant disease and weeks
#     df_x = get_disease_data(df, dataElements_list, number_of_weeks)


#     alert_week = get_recent_epi_weeks(1) 
#     alert_week = alert_week[0]
#     logger.info(f"WEEK............{alert_week}")
#     if not df_x.empty:        
#         final_df = df_x[df_x['value'] >= num]

#         # Alert people in district
#         for index, row in final_df.iterrows():
#             district_uid = row['orgUnit']
#             district_name = row['orgUnit_name']          
#             disease_name = row['dataElement_name']
#             disease_id = row['dataElement']
#             period = row['pe']        
#             value1 = row['value']
#             week = row['week']

#             dx = [f'{disease_id}']
#             pe = [f'{period}']
#             ou = f'LEVEL-MQLiogB9XBV;{district_uid}'

#             logger.info(f"POSTING TO ALERT PROGRAM...............{alert_week}")
#             check_record = check_alert_in_db(disease_name, district_uid, alert_week)
#             if check_record >=1:
#                 print(check_record)
#                 print('ALERT ALREADY IN DB')          
#             else:
#                 print('CONTINUE!')
#                 #Post to DHIS2
#                 tei_id, alert_id = post_to_alert_program(district_uid, district_name, disease_id, alert_week)
#                 logger.info(f"TEI:.....{tei_id}")

#                 # Get Facility level data
#                 facility_data_df = fetch_aggregated_data(api, dx, pe, ou)
#                 # Ensure 'value' is numeric
#                 facility_data_df['value'] = pd.to_numeric(facility_data_df['value'], errors='coerce').fillna(0)

#                 # Only work with facilities with >= the number of cluster issue
#                 facility_data_df = facility_data_df[facility_data_df['value'] >= num]

#                 orgz = None

#                 tei_link = f"https://dev.eidsr.znphi.co.zm/dhis-web-tracker-capture/index.html#/dashboard?tei={tei_id}&program=xDsAFnQMmeU&ou={district_uid}" 

#                 if not facility_data_df.empty:                
#                     facility_df_with_names = replace_uids_with_names(api, facility_data_df)
#                     # facility_df_with_names.to_csv(f'data/facility-name-{uuid.uuid4()}.csv', index=False)

#                     # Prepare the list of orgUnit_name(value)
#                     org_units_list = [
#                         f"{row['orgUnit_name']}({row['value']})"
#                         for _, row in facility_df_with_names.iterrows()
#                     ]
#                     org_units_str = ', '.join(org_units_list)
#                     orgz = org_units_str
                                
#                     msg = (
#                             f"eIDSR Alert | {alert_id}: \nDetected clusters of {disease_name} cases "
#                             f"in {district_name}->({value1}) for Week {week}.\n"
#                             f"Facilities affected: \n{orgz}. \n \n {tei_link}"
#                         )
                    
#                     send_telegram_message.delay('-1002490743936', msg)                

#                 else:
#                     print(f'No Clusters of {num}')

#     else:
#         print(f'No Clusters of {num}')


def cluster_of_cases(df, disease, num):
    dataElements_list = [f'{disease}']  # List of dataElement IDs for diseases requiring notification
    number_of_weeks = get_recent_epi_weeks(1)

    # Filter data for relevant disease and weeks
    df_x = get_disease_data(df, dataElements_list, number_of_weeks)
    
    alert_week = get_recent_epi_weeks(1)
    alert_week = alert_week[0]
    logger.info(f"WEEK............{alert_week}")

    if not df_x.empty:
        final_df = df_x[df_x['value'] >= num]

        alert_sent = False  # Initialize flag to track if alert has been sent

        # Alert people in district
        for index, row in final_df.iterrows():
            district_uid = row['orgUnit']
            district_name = row['orgUnit_name']
            disease_name = row['dataElement_name']
            disease_id = row['dataElement']
            period = row['pe']
            value1 = row['value']
            week = row['week']

            dx = [f'{disease_id}']
            pe = [f'{period}']
            ou = f'LEVEL-MQLiogB9XBV;{district_uid}'

            logger.info(f"POSTING TO ALERT PROGRAM...............{alert_week}")
            check_record = check_alert_in_db(disease_name, district_uid, alert_week)
            if check_record >= 1:
                logger.info('ALERT ALREADY IN DB')
            else:
                logger.info('CONTINUE!')
                
                if not alert_sent:  # Check if an alert has already been sent
                    # Post to DHIS2
                    tei_id, alert_id = post_to_alert_program(district_uid, district_name, disease_id, alert_week)
                    alert_sent = True  # Set the flag to True after sending the alert
                    logger.info(f"TEI:.....{tei_id}")

                    # Get Facility level data
                    facility_data_df = fetch_aggregated_data(api, dx, pe, ou)
                    # Ensure 'value' is numeric
                    facility_data_df['value'] = pd.to_numeric(facility_data_df['value'], errors='coerce').fillna(0)

                    # Only work with facilities with >= the number of cluster issue
                    facility_data_df = facility_data_df[facility_data_df['value'] >= num]

                    if not facility_data_df.empty:
                        # Replace UIDs with readable names
                        facility_df_with_names = replace_uids_with_names(api, facility_data_df)

                        # Prepare the list of orgUnit_name(value)
                        org_units_list = [
                            f"{row['orgUnit_name']}({row['value']})"
                            for _, row in facility_df_with_names.iterrows()
                        ]
                        org_units_str = ', '.join(org_units_list)
                        orgz = org_units_str

                        # Create link to the alert
                        tei_link = f"https://dev.eidsr.znphi.co.zm/dhis-web-tracker-capture/index.html#/dashboard?tei={tei_id}&program=xDsAFnQMmeU&ou={district_uid}"

                        # Prepare the alert message
                        msg = (
                            f"eIDSR Alert | {alert_id}: \nDetected clusters of {disease_name} cases "
                            f"in {district_name}->({value1}) for Week {week}.\n"
                            f"Facilities affected: \n{orgz}. \n \n {tei_link}"
                        )

                        # Send the alert via Telegram
                        send_telegram_message.delay('-1002490743936', msg)
                        logger.info(f"Alert sent for district: {district_name} for disease: {disease_name}")
                    else:
                        logger.info(f'No Clusters of {num} detected at the facility level.')
    else:
        logger.info(f'No Clusters of {num} detected at the district level.')

