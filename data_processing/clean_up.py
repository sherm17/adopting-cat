from airflow.utils.db import provide_session
from airflow.models import XCom
from models.cat import CatOnWebPage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from airflow.models import Variable


@provide_session
def run_clean_up(session=None):

    engine = create_engine(Variable.get('cat_database_connect_str'))
    Session = sessionmaker(bind=engine)
    s = Session()

    # truncate cat_on_web_page table
    s.query(CatOnWebPage).delete()
    s.close()

    # remove xcom data
    session.query(XCom).filter(XCom.dag_id == "scrape-spca").delete()
    engine.dispose()

 