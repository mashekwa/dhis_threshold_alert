# DHIS2 Aggregate - Python Threshold Alert Program

## Overview

This project is designed to monitor and analyze aggregate data from DHIS2 and provide timely alerts when predefined thresholds are exceeded. It leverages Python and DHIS2 integrations to automate alert generation and notification, ensuring prompt awareness of critical data conditions.

---

## Goals

1. **Data Extraction**  
   Retrieve aggregate data from DHIS2 for specific datasets and conditions.

2. **Threshold Analysis**  
   Perform threshold analysis using a Python-based program to identify conditions where thresholds are surpassed.

3. **Alert Management**  
   Populate a DHIS2 tracker alert program with relevant details about conditions breaching the thresholds.

4. **User Notifications**  
   Notify designated users from a specified DHIS2 user group via:
   - Email
   - SMS
   - Telegram  
   Additionally, broadcast alerts to a general Telegram group for widespread awareness.

---

## Tech Stack

- **[DHIS2](https://dhis2.org/)**: A leading open-source platform for health data management and analysis.  
- **Python/Flask**: Used for building the core threshold analysis program and alert management logic.  
- **Celery**: Task queue for handling background jobs and notifications efficiently.  
- **PostgreSQL**: Relational database for storing alert and notification data.  
- **Docker**: Containerization to ensure consistency across deployments.  
- **Redis**: Message broker for Celery tasks.

---

## Key Features

- **Automated Data Analysis**: Automatically fetches and analyzes data from DHIS2.  
- **Customizable Thresholds**: Flexible threshold configuration for different datasets and conditions.  
- **Integrated Notifications**: Multi-channel notifications to ensure timely communication.  
- **Tracker Alert Population**: Updates DHIS2 tracker programs with relevant alert information.  

---

## Getting Started
This guide assumes you already have docker and docker-compose installed on your machine.

1. **Clone the repository**:  
   ```
   git clone <repository-url>
   ```

2. **Set up environment variables**:
    ```
    cp example.env .env
    ```
    Update the different variables defined in the .env file. Before proceeding with step 4. ensure the port mapping in the docker-compose.yml file works for your enviroment, this involves making sure the ports are available.

3. **Build the Docker image**:
    ```
    docker-compose build
    ```
4. **Start up the containers**:
    ```
    docker-compose up or docker-compose up -d
    ```


---
## STILL TO COMPLETE
- Mini backend (FastAPI).
- Mini frontend (Vuejs).


## License

This project is licensed under the [MIT License](LICENSE).
    


