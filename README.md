# adopting-cat
This project is an automated web bot that gathers cat data from bay area SPCAs. I created this project to help a friend who wanted to adopt a cat from near by SPCAs. The program is automated by Airflow and is set to webscrape SCPAs every hour. The program then send an email to the user letting them know if any new cats were listed in the SPCAs. Below is a list of SPCAs that this program is gathering cat data from. 
* East Bay SPCA
* San Francisco SPCA


Below is a diagram of the dags in Airflow.
![image](https://user-images.githubusercontent.com/31725260/162595482-e2573c36-9012-4db9-9d35-73298c30a229.png)


## Installation
#### Below are commands to set up your development environment
```sh
git clone https://github.com/sherm17/adopting-cat.git
cd adopting-cat
pipenv sync --dev
pipenv shell
```
#### Setting up and running Airflow
```sh
# airflow will need a home, ~/airflow is the default
# in this project, airflow's home is set to be in a folder called 'airflow' located in the working directory
export AIRFLOW_HOME=$(pwd)/airflow

#initialize the database
airflow db init

```
#### Update smtp info in airflow/airflow.cfg
I chose gmail as my smtp but you can choose another service if you'd like. 
Below are the variables that will need to be updated in the airflow.cfg file
```sh
smtp_host = smtp.gmail.com
smtp_starttls = True
smtp_ssl = False
smtp_user = YOUR_GMAIL_ACCOUNT@gmail.com
smtp_password = YOUR_16_DIGIT_APP_PASSWORD
smtp_port = 587
smtp_mail_from = YOUR_GMAIL_ACCOUNT@gmail.com
```

#### Update executor to LocalExecutor and sql_alchemy_conn 
By default, the executor is set to SequentialExecutor and 
the database is SQLite. This will not let airflow run the 
webscrapers in parallel. I chose Postgres as my database 
after changing the executor to LocalExecutor

```sh
executor = LocalExecutor
sql_alchemy_conn = postgresql+psycopg2://<your_user>:<your_passphrase>@<host>/<database_name>

```
#### Set your airflow variables
Assign the 3 variables below to some value
* sender_email (this will be used to send out alerts)
* receiver_email (this is the email receiving the alerts)
* cat_database_connect_str (database connection string)
```sh
airflow variables set key=sender_email value=SOME_EMAIL
airflow variables set key=receiver_email value=SOME_EMAIL
airflow variables set key=cat_database_connect_str value=DATABASE_CONNECTION_STRING
```

## Adding new websites to scrape from
Adding a new website to scrape from can be done easily. You will need to create a new class in webscraping/spca_webscrape.py. This class should implement the abstract get_cat_data method. This method should return a list of dictionaries that holds cat info. Then, define a new function that will instantiate an instance of the new class and run the corresponding get_cat_data method. The new function should also push the data onto Airflow using xcom. In data_processing/check_cats.py, grab the new data via xcom. Lastly, import the new function that you defined in spca_webscrape.py and include it in dag.py in the root folder.


