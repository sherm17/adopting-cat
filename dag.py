import airflow.utils.dates

from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonOperator
from airflow.operators.email_operator import EmailOperator
from airflow.models import Variable

# import sys
# sys.path.append('/home/speng/Desktop/projects/spca-cat-adoption')
from webscraping import webscrape
from data_processing import check_cats
from data_processing import clean_up

start = DummyOperator(task_id='start') 

dag = DAG(
    dag_id="scrape-spca",
    start_date=airflow.utils.dates.days_ago(3),
    max_active_runs=1,
    schedule_interval="@hourly"
)


email= EmailOperator(
       task_id='email',
       to=Variable.get('receiver_email'),
       subject='Cat Adoption Updates',
       html_content="{{ task_instance.xcom_pull(task_ids='check_for_new_cats', key='new_cats') }}",
       dag=dag
)

scrape_eastbay_spca = PythonOperator(
    task_id='scrape_eastbay_spca',
    python_callable=webscrape.run_eastbay_spca_scraper,
    dag=dag
)

scrape_sf_spca = PythonOperator(
    task_id='scrape_sf_spca',
    python_callable=webscrape.run_sf_spca_scraper,
    dag=dag
)

scrape_jellysplace = PythonOperator(
    task_id='scrape_jellys_place',
    python_callable=webscrape.run_jellys_place_scraper,
    dag=dag
)

check_for_new_cats = PythonOperator(
    task_id='check_for_new_cats',
    python_callable=check_cats.check_for_new_cats,
    trigger_rule="none_failed",
    dag=dag
)

clean_up = PythonOperator(
    task_id='clean_up',
    python_callable=clean_up.run_clean_up,
    dag=dag
)


start >> [scrape_sf_spca, scrape_eastbay_spca, scrape_jellysplace]
[scrape_eastbay_spca, scrape_sf_spca, scrape_jellysplace] >> check_for_new_cats >> email >> clean_up
 