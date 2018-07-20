import logging
import sys
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger("nhdb.tests")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stderr))


class MySeleniumTests(StaticLiveServerTestCase):
    fixtures = ["auth.json"]

    @classmethod
    def setUpClass(cls):
        super(MySeleniumTests, cls).setUpClass()
        try:
            cls.selenium = WebDriver()
        except:
            print("WebDriver had a problem, skipping interaction tests")
            cls.selenium = None
            return

    @classmethod
    def tearDownClass(cls):
        if cls.selenium:
            cls.selenium.quit()
            super(MySeleniumTests, cls).tearDownClass()

    def test_login(self):
        if not self.selenium:
            return
        self.selenium.get("%s%s" % (self.live_server_url, "/nhdb/project/"))
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys("josh")
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys("josh")
        self.selenium.find_element_by_xpath('//input[@value="Log in"]').click()

    def test_project_page(self):
        if not self.selenium:
            return
        fox = self.selenium
        fox.get("https://localhost/nhdb/project/?q=status.A#object=24536")
        fox.find_element_by_css_selector("[data-canvas]").click()
        fox.find_element_by_class_name("edit-link").click()
