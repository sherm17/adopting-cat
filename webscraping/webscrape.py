from abc import ABC, abstractclassmethod
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import selenium
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class CatAdoptionWebScraper(ABC):
    
    @abstractclassmethod
    def get_cat_data(self):
        pass


class EastBaySpcaWebScraper(CatAdoptionWebScraper):
    def __init__(self):
        self.url = 'https://eastbayspca.org/adoptions/adopt-me/#'
        self.browser = webdriver.Firefox()
        self.cat_list = []


    def _get_photo_urls(self, cat_modal_element):
        """Return list of photo urls"""
        cat_photo_url_list = []
        first_photo = cat_modal_element.find_element(By.CSS_SELECTOR, value='aside.animalModal_image img').get_attribute('src')
        cat_photo_url_list.append(first_photo)

        try:
            animal_image_controller = cat_modal_element.find_element(By.CSS_SELECTOR, value='div.animalModal_image_control')
            num_of_photos_left = len(animal_image_controller.find_elements(By.CSS_SELECTOR, value='span'))  - 1
            next_photo_button = cat_modal_element.find_elements(By.CSS_SELECTOR, value='button.animalModal_slidebutton')[1]

            for _ in range(num_of_photos_left):
                next_photo_button.click()
                curr_photo = self.browser.find_element(By.CSS_SELECTOR, value='aside.animalModal_image img').get_attribute('src')
                cat_photo_url_list.append(curr_photo)
                next_photo_button.click()

        except selenium.common.exceptions.NoSuchElementException:
            logger.info('There is only one photo for this cat')
        return cat_photo_url_list


    def _parse_cat_modal(self, cat_modal_element):
        """
            return dictionary holding cat info. keys are
            id, name, age, sex, breed, age_in_year, location, 
            notes, weight_in_lbs, status, photo_urls, url
        """
        cat_info = {}
        animal_info = cat_modal_element.find_element(By.CSS_SELECTOR, value='div.animalModal_info')
        
        cat_name = cat_modal_element.find_element(By.CSS_SELECTOR, value='h1.animalModal_name').text
        cat_info['name'] = cat_name

        # get photos
        cat_info['photo_urls'] = self._get_photo_urls(cat_modal_element)

        animal_info_rows = animal_info.find_elements(By.CSS_SELECTOR, value='p.animal_info_row')
        for row in animal_info_rows:
            animal_info_key = row.find_element(By.CSS_SELECTOR, value='span.animal_info_key').text.lower()
            animal_info_val = row.find_element(By.CSS_SELECTOR, value='span.animal_info_value').text.lower()
            cat_info[animal_info_key] = animal_info_val

        animal_description = cat_modal_element.find_element(By.XPATH, value="//div[@class='animalModal_description']/p[1]")
        animal_description_text = animal_description.text
        cat_info['notes'] = animal_description_text

        # recalculate age into decimal number
        # data format = 2 Years, 1 Month, 2 Weeks (approx)
        cat_age_info = cat_info['age'].strip()
        years, months, weeks = cat_age_info.split(',')
        years = int(re.search(r'\d+', years).group())
        months = int(re.search(r'\d+', months).group())
        weeks = int(re.search(r'\d+', weeks).group())
        cat_info['age'] = round((years + months / 12 + weeks / 52), 2)

        # change sex to first letter of sex. female = f and male = m
        cat_info['sex'] = cat_info['sex'][0]

        # set location to east bay
        cat_info['location'] = 'east bay spca'

        # set status to 'available for adoption'
        cat_info['status'] = 'available for adoption'

        # change dict keys to match sql column names
        cat_info['age_in_year'] = cat_info.pop('age')
        cat_info['id'] = cat_info.pop('animal id') + '-eastbay'
        cat_info['weight_in_lbs'] = None
        return cat_info


    def get_cat_data(self):
        """Return list containing dictionaries of cat info"""
        self.browser.get(self.url)
        filter_labels = self.browser.find_elements(By.CSS_SELECTOR, value='span.filter-label')
        for label in filter_labels:
            if label.text == 'CATS':
                label.click()
        time.sleep(2)
        animal_list = self.browser.find_elements(By.CSS_SELECTOR, value='div.animal')

        for animal in animal_list:
            animal.click()

            animal_model = self.browser.find_element(By.CSS_SELECTOR, value='div.animalModal')
            cat_data = self._parse_cat_modal(animal_model)

            # add url to cat_data
            cat_data['url'] = self.browser.current_url
            self.cat_list.append(cat_data)

            close_button = self.browser.find_element(By.CSS_SELECTOR, value='button.animalModal_close')
            close_button.click()
        self.browser.quit()
        return self.cat_list


class SanFranSpcaWebScraper(CatAdoptionWebScraper):

    def __init__(self):
        self.url = 'https://www.sfspca.org/adoptions/cats/?'
        self.browser = webdriver.Firefox()
        self.cat_list = []


    def _parse_cat_weight_str(self, cat_weight_str):
        if ';' in cat_weight_str:
            cat_weight = cat_weight_str.split(';')
            lbs = int(re.search(r'\d+', cat_weight[0]).group())
            oz = int(re.search(r'\d+', cat_weight[1]).group())
            return round(lbs + oz/16, 2)
        else:
            lbs = int(re.search(r'\d+', cat_weight_str).group())
            return lbs 

    def _parse_cat_detail(self, url, adoption_detail_web_elem, cat_photo_url_containers):
        """
            return dictionary holding cat info. keys are
            id, name, age, sex, breed, age_in_year, location, 
            notes, weight_in_lbs, status, photo_urls, url
        """
        cat_info = {}

        # id
        cat_id = url.split('/')[-1] or url.split('/')[-2]
        cat_info['id'] = cat_id + '-sanfran'

        # url
        cat_info['url'] = url

        # name
        name = self.browser.find_elements(By.CSS_SELECTOR, value='h2.elementor-heading-title ')[0].text
        cat_info['name'] = name

        # parse cat photo url containers
        cat_photo_urls = [img_element.get_attribute('src')  for img_element in cat_photo_url_containers]        
        cat_info['photo_urls'] = cat_photo_urls

        table_rows = adoption_detail_web_elem.find_elements(By.CSS_SELECTOR, value='tr')
        for row in table_rows:
            animal_info_key = row.find_element(By.TAG_NAME, value='th').text.lower()
            animal_info_val = row.find_element(By.TAG_NAME, value='td').text

            cat_info[animal_info_key] = animal_info_val
        
        # cat weight format  = '6lbs; 9 oz'
        if 'weight' in cat_info:
            cat_weight_str = cat_info['weight']
            cat_info['weight'] = self._parse_cat_weight_str(cat_weight_str)

        # get first letter of sex. male = m female = f
        cat_info['gender'] = cat_info['gender'][0].lower()

        # parse age
        cat_age_str = cat_info['age'] 
        if ';' in cat_age_str:
            cat_age_str_elems = cat_info['age'].split(';')
            for elem in cat_age_str_elems:
                if 'y' in elem.lower():
                    years = int(re.search(r'\d+', elem).group())
                elif 'm' in elem.lower():
                    months = int(re.search(r'\d+', elem).group())
            cat_info['age'] = round((years + months / 12 ), 2)
        else:
            if 'y' in cat_age_str.lower():
                age = int(re.search(r'\d+', cat_age_str).group())
            elif 'm' in cat_age_str.lower():
                age = int(re.search(r'\d+', cat_age_str).group())
            cat_info['age'] = age

        # set location to 'san francisco'
        cat_info['location'] = 'san francisco spca'
        # set status to 'available for adoption
        cat_info['status'] = 'available for adoption'

        # change dict keys to match sql column names
        cat_info['age_in_year'] = cat_info.pop('age')
        if 'weight' in cat_info:
            cat_info['weight_in_lbs'] = cat_info.pop('weight')
        cat_info['sex'] = cat_info.get('gender', None)
        cat_info['notes'] = None
        return cat_info


    def get_cat_data(self):
        """Return list containing dictionaries of cat info"""
        self.browser.get(self.url)
        cat_detail_anchor = self.browser.find_elements(By.CSS_SELECTOR, value='a.userContent__permalink')

        cat_detail_url = [link.get_attribute('href') for link in cat_detail_anchor]

        for url in cat_detail_url:
            self.browser.get(url)
            try:
                adoption_detail_web_elem = self.browser.find_element(By.CSS_SELECTOR, value='table.adoptionFacts__table')
                
                cat_photo_link_container = self.browser.find_elements(By.CSS_SELECTOR, value='div.adoptionCarousel--item img')            
                cat_data = self._parse_cat_detail(url, adoption_detail_web_elem, cat_photo_link_container)

                self.cat_list.append(cat_data)
            except selenium.common.exceptions.NoSuchElementException:
                logger.info('Webscraping SF SPCA: This cat url may not be valid')
        self.browser.quit()
        return self.cat_list


class JellysPlaceWebScraper(CatAdoptionWebScraper):
    """Jellys place gets their cat adoption data from shelterluv.com"""

    def __init__(self):
        self.url = 'https://www.shelterluv.com/embed/24538?species=Cat'
        self.browser = webdriver.Firefox()
        self.cat_list = []

    def _parse_cat_age(self, cat_age_str):
        """example format 3Y/0M/0W """
        years, months, weeks = cat_age_str.split('/')
        years = int(re.search(r'\d+', years).group())
        months = int(re.search(r'\d+', months).group())
        weeks = int(re.search(r'\d+', weeks).group())

        if months > 0:
            months = months / 12
        if weeks > 0:
            weeks = weeks / 52

        age = round((years + months + weeks), 2)
        return age


    def _get_cat_photo_urls(self, cat_info_container):
        """
        Each cat adoption link can contain one or more urls.
        The ones that only contain one photo url have the image inside
        a div with class 'single-image-container'.
        The ones that have multiple photo urls have the images inside
        a div with class 'VueCarousel-slide'.
        There can be cats that have no photos as well. The default photo
        location is 'https://www.shelterluv.com/img/default/default_cat.png'
        """
        photo_urls = None
        try:
            image_url = cat_info_container.find_element(
                By.XPATH, value="//div[@class='p-2']/div/div/div[2]/div/following-sibling::img"
            ).get_attribute('src')
            photo_urls = [image_url]
        except selenium.common.exceptions.NoSuchElementException:
            logger.info('Webscraping Jellys Place: Single photo not found')
        
        try:
            image_elements = cat_info_container.find_elements(
                By.CSS_SELECTOR, value='div.VueCarousel-slide img'
            )
            photo_urls = [elem.get_attribute('src') for elem in image_elements]
        except selenium.common.exceptions.NoSuchElementException:
            logger.info('Webscraping Jellys Place: Multiple Photos not found')
        
        return photo_urls
        

    def _parse_cat_info(self, cat_info_container):
        cat_detail_container = cat_info_container.find_elements(By.XPATH, value="//div[@class='p-2']/div/div/div[4]/div[1]/div")
        cat_info = {}

        for info in cat_detail_container:
            key_and_val = info.find_elements(By.CSS_SELECTOR, value='div')
            key = key_and_val[0].text.lower().strip()
            val = key_and_val[1].text.lower().strip()
            cat_info[key] = val

        cat_age_str = cat_info['age']

        cat_info['age_in_year'] = self._parse_cat_age(cat_age_str)
        cat_info['photo_urls'] = self._get_cat_photo_urls(cat_info_container)

        cat_info['id'] = cat_info.pop('animal id')
        cat_info['sex'] = cat_info['sex'][0]
        cat_info['location'] = 'jellys_place'
        cat_info['status'] = 'available for adoption'
        cat_info['weight_in_lbs'] = None
        return cat_info
    

    def get_cat_data(self):
        """Return list containing dictionaries of cat info"""
        self.browser.get(self.url)

        container_div = WebDriverWait(self.browser, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div#app'))
        )
        time.sleep(3)
        cat_anchor_elements = container_div.find_elements(By.TAG_NAME, value='a')
        cat_info_links = [anchor.get_attribute('href') for anchor in cat_anchor_elements]
        for link in cat_info_links:
            self.browser.get(link)
            cat_info_container = self.browser.find_element(By.CSS_SELECTOR, value='div#app')
            cat_data = self._parse_cat_info(cat_info_container)

            # add url to cat dict
            cat_data['url'] = link
            self.cat_list.append(cat_data)
        print(self.cat_list)
        return self.cat_list

def run_eastbay_spca_scraper(**context):
    e = EastBaySpcaWebScraper()
    cats = e.get_cat_data()
    context["task_instance"].xcom_push(key='East_Bay_SPCA_Adoptable_Cats', value=cats)

def run_sf_spca_scraper(**context):
    sf = SanFranSpcaWebScraper()
    cats = sf.get_cat_data()
    context["task_instance"].xcom_push(key='SF_SPCA_Adoptable_Cats', value=cats)

def run_jellys_place_scraper(**context):
    jellysplace = JellysPlaceWebScraper()
    cats = jellysplace.get_cat_data()
    context["task_instance"].xcom_push(key='Jellys_Place_Adoptable_Cats', value=cats)
