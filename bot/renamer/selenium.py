from datetime import datetime
import platform
from random import randint
import traceback

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


from .. import constants
from ..base.exceptions import (
    CredentialInvalid, EmptyList, EntityInvalid,
    EntityIsSuccess, InvalidValidationMethod, NotFound, MaxRetries
)
from ..base.selenium import BaseSelenium


class RenamerSelenium(BaseSelenium):
    WAIT_BEFORE_NEXT = 5
    WAIT_BEFORE_INPUT = 10

    def __init__(self, entity, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entity = entity
        try:
            self.handle()
        except (CredentialInvalid, EntityInvalid, InvalidValidationMethod):
            self.entity.report_fail()
            self.quit_driver()
        except (EmptyList, NotFound, MaxRetries):
            self.quit_driver()
        except EntityIsSuccess:
            self.entity.report_success()
            self.quit_driver()
        except Exception as err:
            print(err)
            print(traceback.format_exc())
            self._start_debug()
            self.quit_driver()

    def handle(self):
        self.driver = self.get_driver(size=(1200, 700))
        self.do_login()
        self.do_open_verification_tab()
        self.go_to_edit()
        self.do_final_name()
        self.do_final_category_1()
        self.do_service_area()
        self.do_hours()
        self.do_special_hours()
        self.do_website()
        self.do_attributes()
        self.do_description()
        self.do_opening_date()

        self.do_code_fill()

        self.do_address()
        self.do_phone()

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

        self.do_code_send()
        self.get_final_data()
        self.quit_driver()

    def go_to_edit(self):
        row = self.get_business_row()
        self.click_element(
            By.XPATH,
            (
                'td[2]/content/a',
                'td[3]/content/a',
            ),
            source=row
        )
        current_url = self.driver.current_url
        self.driver.get(current_url.replace('/dashboard/', '/edit/'))

    def get_business_row(self):
        if self.driver.current_url != 'https://business.google.com/locations':
            self.driver.get('https://business.google.com/locations')

        rows = self.get_elements(
            By.XPATH,
            (
                '/html/body/div[4]/c-wiz/div[2]/div[1]/c-wiz/div/c-wiz[3]'
                '/div/content/c-wiz[2]/div[2]/table/tbody/tr',
                '/html/body/div[7]/c-wiz/div[2]/div[1]/c-wiz/div/c-wiz[3]'
                '/div/content/c-wiz[2]/div[2]/table/tbody/tr'
            ),
            raise_exception=False,
            timeout=5
        )
        if not rows:
            raise EmptyList(
                msg="There aren't any business", logger=self.logger
            )

        row = None
        for r in rows:
            if self.entity.name in r.text or self.entity.final_name in r.text:
                row = r
                break

        if not row:
            raise NotFound(msg="Business not found.", logger=self.logger)

        return row

    def do_open_verification_tab(self):
        row = self.get_business_row()

        status = self.get_element(
            By.XPATH,
            'td[3]',
            source=row
        ).text

        if status.strip() not in (
            'Verification required',
            'Pending verification',
            'Suspended',
            'Published'
        ):
            status = self.get_element(
                By.XPATH,
                'td[4]',
                source=row
            ).text

        if status.strip() == 'Published':
            raise EntityIsSuccess
        elif status.strip() == 'Suspended':
            raise EntityInvalid

        element = self.get_element(
            By.XPATH,
            (
                'td[4]/content/div/div',
                'td[5]/content/div/div'
            ),
            source=row
        )

        if platform.system() == 'Darwin':
            ActionChains(self.driver) \
                .key_down(Keys.COMMAND) \
                .click(element) \
                .key_up(Keys.COMMAND) \
                .perform()
        else:
            ActionChains(self.driver) \
                .key_down(Keys.CONTROL) \
                .click(element) \
                .key_up(Keys.CONTROL) \
                .perform()

        self.driver.switch_to.window(self.driver.window_handles[1])
        text = self.get_element(
            By.XPATH, '//body', move=False, timeout=5
        ).text.strip()

        if 'Is this your business' in text:
            elements = self.get_elements(
                By.XPATH,
                (
                    '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/'
                    'div[1]/div/content/label[2]'
                )
            )
            self.click_element(
                By.XPATH,
                'div[1]',
                source=elements[-1],
                timeout=5
            )
            self.click_element(
                By.XPATH,
                (
                    '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/'
                    'div[2]/button'
                )
            )

            text = self.get_element(
                By.XPATH, '//body', move=False, timeout=5
            ).text.strip()

        if (
            'Enter the code' not in text and
            'Get your code at this number now by automated call' not in text
        ):
            raise EntityInvalid(
                "Cannot validate by phone.", logger=self.logger
            )

        self.driver.switch_to.window(self.driver.window_handles[0])

    def do_final_name(self):
        if not self.entity.final_name:
            return
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[2]',
            ),
            timeout=5
        )

        xpath_input = (
            '//*[@id="js"]/div[9]/div/div[2]/content/div/div[4]/'
            'div/div[1]/div/div[1]/input'
        )

        self.clear_input(By.XPATH, xpath_input)
        self.fill_input(By.XPATH, xpath_input, self.entity.final_name)
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[9]/div/div[2]/content/div/div[5]/div[2]'
            ),
        )

    def do_final_category_1(self):
        if not self.entity.final_category_1:
            return
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[3]'
            ),
            timeout=self.WAIT_BEFORE_NEXT
        )

        xpath_input = (
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
            'div/div[1]/div/div[1]/div[1]/input[2]'
        )

        self.clear_input(
            By.XPATH,
            xpath_input,
            timeout=self.WAIT_BEFORE_INPUT
        )
        self.fill_input(
            By.XPATH,
            xpath_input,
            self.entity.final_category_1
        )

        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div/div[1]/div/div[1]/div[2]/div/div/div[1]'
            ),
            timeout=5
        )
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[5]/div[2]',
            ),
        )

    def do_service_area(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[5]'
            ),
            timeout=self.WAIT_BEFORE_NEXT
        )

        xpath_input = (
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div/div[1]/'
            'div/div/div/div/div/div/div[1]/div[2]/div[1]/div/div[1]/input'
        )
        self.clear_input(By.XPATH, xpath_input, timeout=10)
        self.fill_input(
            By.XPATH,
            xpath_input,
            '{}, {}'.format(
                self.entity.final_city,
                self.entity.final_state
            )
        )

        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div/div[1]/div/div/div/div/div/div/div[2]/div/div/div[1]',
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div/div[1]/div/div/div/div/div/div/div[3]/div/div/div[1]',
            )
        )
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[5]/div[2]'
            )
        )

    def do_hours(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[6]'
            ),
            move=True,
            timeout=self.WAIT_BEFORE_INPUT
        )
        elements = self.get_elements(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[3]/div/div',
            timeout=self.WAIT_BEFORE_NEXT
        )
        for element in elements:
            checkbox = self.get_element(
                By.XPATH,
                'label/div',
                source=element
            )
            if checkbox.get_attribute('aria-checked') != 'true':
                checkbox.click()

            self.click_element(
                By.XPATH,
                'div[2]/div[1]/div/div[1]/div[1]/input[2]',
                source=element
            )
            self.click_element(
                By.XPATH,
                'div[2]/div[1]/div/div[1]/div[2]/div/div/div[1]',
                source=element
            )

        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div[2]'
        )

    def do_special_hours(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[7]'
            ),
            move=True,
            timeout=self.WAIT_BEFORE_INPUT
        )
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div[2]/div[1]/span[1]/div'
            ),
            raise_exception=False,
            timeout=self.WAIT_BEFORE_NEXT
        )
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div[2]/div[3]/span[1]/div'
            ),
            raise_exception=False
        )
        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[5]/div[2]'
        )

    def do_website(self):
        if not self.entity.final_website:
            return
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[9]'
            ),
            move=True,
            timeout=self.WAIT_BEFORE_INPUT
        )

        xpath_input = (
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div[1]/'
            'div[1]/div/div[1]/input'
        )
        self.clear_input(
            By.XPATH,
            xpath_input,
            timeout=self.WAIT_BEFORE_NEXT
        )
        self.fill_input(
            By.XPATH,
            xpath_input,
            self.entity.final_website
        )

        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[5]/div[2]'
        )

    def do_attributes(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[10]'
            ),
            move=True,
            timeout=self.WAIT_BEFORE_NEXT
        )

        elements = []
        el = self.get_element(
            By.XPATH,
            '//*[@id="attr-dialog-content"]/div[9]',
            timeout=self.WAIT_BEFORE_INPUT,
            raise_exception=False
        )
        if el:
            elements.append(el)

        el = self.get_element(
            By.XPATH,
            '//*[@id="attr-dialog-content"]/div[10]',
            raise_exception=False
        )
        if el:
            elements.append(el)

        to_clic = randint(0, 1)
        special = False

        if not elements:
            elements = self.get_elements(
                By.XPATH,
                '//*[@id="attr-dialog-content"]/div'
            )
            to_clic = randint(1, 2)
            special = True

        element = elements[to_clic]

        if special:
            element = self.get_element(By.XPATH, 'div', source=element)

        if element.get_attribute('aria-checked') != 'true':
            element.click()

        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[5]/div[2]'
        )

    def do_description(self):
        if not self.entity.final_description:
            return
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[11]'
            ),
            move=True,
            timeout=self.WAIT_BEFORE_NEXT
        )

        xpath_input = (
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
            'div/div[1]/div[1]/textarea'
        )
        self.clear_input(
            By.XPATH,
            xpath_input,
            timeout=self.WAIT_BEFORE_INPUT
        )
        self.fill_input(By.XPATH, xpath_input, self.entity.final_description)
        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[5]/div[2]',
            timeout=5
        )

    def do_opening_date(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[12]'
            ),
            move=True,
            timeout=self.WAIT_BEFORE_NEXT
        )

        date_start = int(datetime(2011, 1, 1).timestamp())
        date_end = int(datetime(2018, 12, 31).timestamp())
        date_final = randint(date_start, date_end)
        date_final = datetime.fromtimestamp(date_final)

        # Year
        xpath_year = (
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
            'div[1]/span[1]/div/div[1]/div/div[1]/input'
        )
        self.clear_input(By.XPATH, xpath_year, timeout=self.WAIT_BEFORE_INPUT)
        self.fill_input(By.XPATH, xpath_year, date_final.year)

        # Month
        xpath_month = (
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div[1]/'
            'span[2]/span/div',
        )
        self.click_element(
            By.XPATH,
            xpath_month
        )
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div[1]/span[2]/span/div/div[2]/div[{}]'
            ).format(date_final.month + 2),
            timeout=3
        )

        # Day
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div[1]/span[3]/div'
            )
        )
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div[1]/span[3]/div/div[2]/div[{}]'
            ).format(date_final.day + 2),
            timeout=3
        )

        # Apply
        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[5]/div[2]'
        )

    def do_code_fill(self):
        self.driver.switch_to_window(self.driver.window_handles[1])

        success = self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/div/'
                'div[1]/div/div[2]/button[2]'
            ),
            raise_exception=False
        )

        if not success:
            self.click_element(
                By.XPATH,
                (
                    '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/'
                    'div[2]/div/div[1]/button'
                ),
            )

        xpath_phone = (
            '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/div/'
            'div[1]/div/div[1]/h3',
            '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/h3/strong',
        )

        try:
            phone_number = self.get_element(
                By.XPATH,
                xpath_phone,
                move=False
            ).text
        except TimeoutException:
            phone_number = self.get_element(
                By.XPATH,
                xpath_phone,
                move=False,
                timeout=20
            ).text

        code = None
        retries = 0
        while not code:
            retries += 1
            if retries >= 10:
                raise MaxRetries(
                    msg="Too mamny retries", logger=self.logger
                )
            try:
                code = self.entity.get_code(phone_number=phone_number)
            except Exception as err:
                print(err)
                code = None
            self._wait(2)

        self._wait(10)

        text = self.get_element(By.XPATH, '//body', move=False).text
        if "Couldn't connect" in text:
            raise InvalidValidationMethod

        xpath_code = (
            '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/'
            'div[1]/div[2]/div[1]/div/div[1]/input'
        )
        self.clear_input(By.XPATH, xpath_code, timeout=5)
        self.fill_input(By.XPATH, xpath_code, code)

    def do_address(self):
        self.driver.switch_to_window(self.driver.window_handles[0])

        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[4]'
            ),
            move=True,
        )
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/'
                'div/div[3]/div[4]/div'
            ),
            timeout=self.WAIT_BEFORE_INPUT
        )

        # Input full address
        xpath_input_address = (
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div/div[3]/'
            'div[1]/div/div/div[2]/div/div/div[2]/input',
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div/div[3]/'
            'div[1]/c-wiz/c-wiz/div/div/div[4]/div/div[1]/div/div[1]/input'
        )
        self.fill_input(
            By.XPATH,
            xpath_input_address,
            (
                '{address} {city} {state} {zip_code}'.format(
                    address=self.entity.final_address,
                    city=self.entity.final_city,
                    state=constants.STATES[self.entity.final_state],
                    zip_code=self.entity.final_zip_code
                )
            )
        )

        # Zip Code
        xpath_zipcode = (
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div/'
            'div[3]/div[1]/div/div/div[2]/div/div/div[6]/input',
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div/'
            'div[3]/div[1]/c-wiz/c-wiz/div/div/div[7]/div/div[1]/div/'
            'div[1]/input',
        )

        self.fill_input(
            By.XPATH,
            xpath_zipcode,
            self.entity.final_zip_code,
            timeout=2
        )

        # City
        xpath_city = (
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div/'
            'div[3]/div[1]/div/div/div[2]/div/div/div[4]/input',
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div/'
            'div[3]/div[1]/c-wiz/c-wiz/div/div/div[5]/div/div[1]/div/'
            'div[1]/input',
        )
        self.fill_input(
            By.XPATH,
            xpath_city,
            self.entity.final_city,
            timeout=2
        )

        # State
        xpath_state = (
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div/'
            'div[3]/div[1]/div/div/div[2]/div/div/div[5]/div[2]',
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div/'
            'div[3]/div[1]/c-wiz/c-wiz/div/div/div[6]/div[1]'
        )
        self.click_element(
            By.XPATH,
            xpath_state,
            timeout=2
        )
        elements = self.get_elements(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div/'
                'div[3]/div[1]/div/div/div[2]/div/div/div[5]/div[3]/div',
                '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div/'
                'div[3]/div[1]/c-wiz/c-wiz/div/div/div[6]/div[1]/div[2]/div'
            )
        )

        for element in elements:
            if element.text == constants.STATES[self.entity.final_state]:
                element.click()
                break

        # Clear and input address
        self.clear_input(By.XPATH, xpath_input_address)
        self.fill_input(
            By.XPATH,
            xpath_input_address,
            self.entity.final_address,
            timeout=2
        )

        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[5]/div[2]',
            timeout=5
        )

    def do_phone(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[1]/div[2]/'
                'content/div[8]'
            ),
            move=True,
            timeout=self.WAIT_BEFORE_NEXT
        )

        xpath_input = (
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[3]/div[1]/'
            'div/div/div[2]/div[1]/div/div[1]/input'
        )

        # Grab current number
        current_phone = self.get_element(
            By.XPATH, xpath_input, move=False, timeout=self.WAIT_BEFORE_INPUT
        ).get_attribute('value')

        # Fill new number
        self.clear_input(By.XPATH, xpath_input)
        self.fill_input(
            By.XPATH,
            xpath_input,
            self.entity.final_phone_number
        )

        if current_phone:
            self.click_element(
                By.XPATH,
                (
                    '//*[@id="js"]/div[10]/div/div[2]/content/div/div[3]/'
                    'div[3]/div'
                )
            )
            self.fill_input(
                By.XPATH,
                (
                    '//*[@id="js"]/div[10]/div/div[2]/content/div/div[3]/'
                    'div[3]/div[1]/div[1]/div/div[2]/div[1]/div/div[1]/input'
                ),
                current_phone,
                timeout=3
            )

        self.click_element(
            By.XPATH,
            '//*[@id="js"]/div[10]/div/div[2]/content/div/div[4]/div[2]'
        )

    def do_code_send(self):
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/'
                'div[1]/div[3]/button'
            ),
            timeout=self.WAIT_BEFORE_INPUT
        )
        self._wait(60*5)  # 5 Minutes

    def get_final_data(self):
        # Click "Get started"
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/c-wiz[1]/div/div[2]/div/div/'
                'div[3]/button'
            )
        )

        # Click "Get started" again
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[10]/div/div[2]/div[3]/div',
                '//*[@id="js"]/div[9]/div/div[2]/div[3]/div'
            ),
            raise_exception=False,
            timeout=self.WAIT_BEFORE_INPUT
        )

        # Click "No thanks"
        self.click_element(
            By.XPATH,
            (
                '//*[@id="js"]/div[9]/div/div[2]/content/div/div[2]/div/'
                'div[4]/div[2]'
            ),
            raise_exception=False
        )

        # Click "X"
        self.click_element(
            By.XPATH,
            (
                '//*[@id="main_viewpane"]/div[2]/c-wiz/c-wiz/div/aside/'
                'div[2]/div/div/div'
            ),
            raise_exception=False
        )

        # Check if is "Pending" or "Suspended"
        text = self.get_element(
            By.XPATH,
            '//body',
            move=False
        ).text

        if 'This location has been suspended due to quality issues.' in text:
            self.logger(instance=self.entity, data={'status': 'Pending'})
            self.entity.report_fail()
            return
        elif 'Your business is verified. Listings may be reviewed ' in text:
            self.logger(instance=self.entity, data={'status': 'Suspended'})
            self.entity.report_pending()
            return

        # Get GMaps link
        gmaps = self.get_element(
            By.XPATH,
            '//*[@id="dcrd-8"]/div/ul/li[1]/a',
            move=False,
            raise_exception=False
        ).get_attribute('href')

        # Get GSearch link
        gsearch = self.get_element(
            By.XPATH,
            '//*[@id="dcrd-8"]/div/ul/li[2]/a',
            move=False,
            raise_exception=False
        ).get_attribute('href')

        data = {'google_maps': gmaps, 'google_search': gsearch}
        self.logger(instance=self.entity, data=data)
        self.entity.report_success(**data)
