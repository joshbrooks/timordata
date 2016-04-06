# selenium_tests.py
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

page = 'https://localhost/nhdb/project/?q=status.A#object=24536'


# el = fox.find_element_by_class_name('show-edit-canvas')
# el.click()

# def checkEditModals(page = 'https://localhost/nhdb/project/?q=status.A#object=24536'):
fox = webdriver.Firefox()
err = []
fox.get(page)
try:
    el = WebDriverWait(fox, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-canvas]"))
    )
    el = fox.find_element(By.CSS_SELECTOR, "[data-canvas]")

    menu = fox.find_element(By.ID, "myNavmenuCanvas")

    # for i in range(0, len(menu.find_elements(By.CSS_SELECTOR, '[data-modalurl]')):
    #     menu.find_element
    #
    #     if not i.is_displayed():
    #         el.click()
    #     i =
    #
    #     close = WebDriverWait(fox, 10).until(EC.element_to_be_clickable(i))
    #     WebDriverWait(fox,1)
    #     close = WebDriverWait(fox, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.modal.in .close')))
    #
    #
    #     close.click()

finally:
    time.sleep(0.2)
    fox.quit()
    pass
# return err
#
# if __name__ == '__main__':
#     checkEditModals()
#     checkEditModals('https://localhost/nhdb/organization/?q=active.true#object=1106')