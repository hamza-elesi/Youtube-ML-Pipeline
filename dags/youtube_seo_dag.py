from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 10, 8),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'simple_test_dag',  # DAG name
    default_args=default_args,
    description='A simple test DAG',
    schedule_interval=timedelta(days=1),  # This DAG runs once a day
)

# Simple Python function that will be executed by the DAG
def print_hello():
    print("Hello from Airflow!")

# Create a PythonOperator to execute the function
hello_task = PythonOperator(
    task_id='hello_task',  # Task name
    python_callable=print_hello,  # The function to execute
    dag=dag,
)

# This DAG only has one task, so no need to set dependencies
