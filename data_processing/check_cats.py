
from models.cat import Cat, CatOnWebPage, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from airflow.models import Variable


def _construct_email_mess_for_newcats(cat_dict):
    message = """
    There is a new cat at location: {location}<br>
    name: {name}<br>
    age: {age}<br>
    notes: {notes}<br>
    gender: {gender}<br>
    url: <a href="{url}">{url}</a> <br>
    <br>""".format(location=cat_dict['location'], gender=cat_dict['sex'], name=cat_dict['name'], age=cat_dict['age_in_year'], notes=cat_dict['notes'], url=cat_dict['url'])
    return message

def check_for_new_cats(**context):
    new_cat_message = ''
    new_cats_list = []

    engine = create_engine(Variable.get('cat_database_connect_str'))
    Session = sessionmaker(bind=engine)
    session = Session()

    # truncate table
    session.query(CatOnWebPage).delete()

    east_bay_spca_cats = context['task_instance'].xcom_pull(
        task_ids='scrape_eastbay_spca', key='East_Bay_SPCA_Adoptable_Cats'
    )
    san_fran_spca_cats = context['task_instance'].xcom_pull(
        task_ids='scrape_sf_spca', key='SF_SPCA_Adoptable_Cats'
    )

    all_cats = san_fran_spca_cats + east_bay_spca_cats

    cat_obj_list = [
        CatOnWebPage(
            id=cat.get('id', None),
            name=cat.get('name', None),
            sex=cat.get('sex', None),
            breed=cat.get('breed', None),
            age_in_year=cat.get('age_in_year', None),
            location=cat.get('location', None),
            notes=cat.get('notes', None),
            weight_in_lbs=cat.get('weight_in_lbs',None),
            status=cat.get('status', None),
            photo_urls=cat.get('photo_urls', None),
            url=cat.get('url', None)
        )
        for cat in all_cats
    ]

    session.add_all(cat_obj_list)
    session.commit()

    # now compare existing cats with cats on webpage
    new_cats = session.query(CatOnWebPage) \
        .join(Cat, Cat.id == CatOnWebPage.id, isouter=True) \
        .filter(Cat.id == None) \
        .order_by(CatOnWebPage.age_in_year).all()

    # convert instances of CatOnWebPage to dict
    for new_cat in new_cats:
        curr_cat = dict(new_cat.__dict__)
        curr_cat.pop('_sa_instance_state', None)
        new_cats_list.append(curr_cat)

    if len(new_cats_list) == 0:
        new_cat_message = 'There no new cats listed in the past hour'
    else:
        for new_cat in new_cats_list:
            new_cat_message += _construct_email_mess_for_newcats(new_cat)
    
            # copy new cats to cat table, which tracks all cats
            a_cat = Cat(
                id=new_cat['id'],
                name=new_cat['name'],
                sex=new_cat['sex'],
                breed=new_cat['breed'],
                age_in_year=new_cat['age_in_year'],
                location=new_cat['location'],
                notes=new_cat['notes'],
                weight_in_lbs=new_cat['weight_in_lbs'],
                status=new_cat['status'],
                photo_urls=new_cat['photo_urls'],
                url=new_cat['url']
            )
            session.add(a_cat)
            session.commit()

    context["task_instance"].xcom_push(key='new_cats', value=new_cat_message)
    session.close()
    engine.dispose()


