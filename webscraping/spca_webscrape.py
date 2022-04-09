from abc import ABC, abstractclassmethod
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import re
import selenium


class SpcaCatWebScraper(ABC):
    
    @abstractclassmethod
    def get_cat_data(self):
        pass


class EastBaySpcaWebScraper(SpcaCatWebScraper):
    def __init__(self):
        self.url = 'https://eastbayspca.org/adoptions/adopt-me/#'
        self.browser = webdriver.Firefox()
        self.cat_list = []


    def _get_photo_urls(self, cat_modal_element):
        # get photos
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
            print("only one photo for this cat")
        return cat_photo_url_list


    def _parse_cat_modal(self, cat_modal_element):
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


class SanFranSpcaWebScraper(SpcaCatWebScraper):

    def __init__(self):
        self.url = 'https://www.sfspca.org/adoptions/cats/?'
        self.browser = webdriver.Firefox()

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
            id, age, weight, gender, breed, photo_urls
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
        cat_list = []

        self.browser.get(self.url)
        cat_detail_anchor = self.browser.find_elements(By.CSS_SELECTOR, value='a.userContent__permalink')

        cat_detail_url = [link.get_attribute("href") for link in cat_detail_anchor]

        for url in cat_detail_url:
            self.browser.get(url)
            try:
                adoption_detail_web_elem = self.browser.find_element(By.CSS_SELECTOR, value='table.adoptionFacts__table')
                
                cat_photo_link_container = self.browser.find_elements(By.CSS_SELECTOR, value='div.adoptionCarousel--item img')            
                cat_data = self._parse_cat_detail(url, adoption_detail_web_elem, cat_photo_link_container)

                cat_list.append(cat_data)
            except selenium.common.exceptions.NoSuchElementException:
                print('cat url may not be working')
        self.browser.quit()
        return cat_list


def run_eastbay_spca_scraper(**context):
    e = EastBaySpcaWebScraper()
    cats = e.get_cat_data()
    context["task_instance"].xcom_push(key='East_Bay_SPCA_Adoptable_Cats', value=cats)

def run_sf_spca_scraper(**context):
    sf = SanFranSpcaWebScraper()
    cats = sf.get_cat_data()
    context["task_instance"].xcom_push(key='SF_SPCA_Adoptable_Cats', value=cats)


