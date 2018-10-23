import os
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command

from stack.apps import StackConfig
from stack.models import Question, Answer, User
from stack.utils import add_tag


class SeleniumTestSet(StaticLiveServerTestCase):

    index = "/" + StackConfig.name + "/"
    username = "test_user"
    password = "test_password"
    email = "test@mail.com"
    image = "test_content/test_avatar.jpg"
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 5)

    @classmethod
    def generate_test_data(cls):

        call_command('loaddata', 'test_content/test_data.json', verbosity=0)
        for i in range(1, 21, 1):
            new_question = Question(content="test_content" + str(i),
                                    header="test_question" + str(i),
                                    user=User.objects.get(username=SeleniumTestSet.username))
            new_question.save()

            if i % 2 == 0:
                add_tag("tag1", new_question)
            else:
                add_tag("tag1", new_question)
                add_tag("tag2", new_question)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def get_index_page(self):
        """Method to return to the main page"""
        self.driver.get(self.live_server_url + self.index)
        self.driver.maximize_window()
        self.driver.refresh()

    def setup_login(self):
        """Method to log in user by selenium"""
        login_path = "//a[contains(text(), 'Log in')]"
        username_id = "id_username"
        password_id = "id_password"
        login_button_path = "//button[contains(text(), 'Login')]"

        login_ref = self.wait.until(ec.presence_of_element_located((By.XPATH, login_path)))
        login_ref.click()

        username = self.wait.until(ec.presence_of_element_located((By.ID, username_id)))
        username.send_keys(self.username)

        password = self.wait.until(ec.presence_of_element_located((By.ID, password_id)))
        password.send_keys(self.password)

        self.driver.find_element_by_xpath(login_button_path).click()

    def test_search_by_word(self):
        """Verify that it is possible to find question by entered key words"""
        self.generate_test_data()

        search_path = "//input[@name='search']"
        apply_search_path = "//button[contains(text(), 'GO')]"
        question_css_selector = ".question_separator"

        self.get_index_page()
        search = self.wait.until(ec.presence_of_element_located((By.XPATH, search_path)))
        search.send_keys("test question")

        apply_search = self.wait.until(ec.presence_of_element_located((By.XPATH, apply_search_path)))
        apply_search.click()

        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, question_css_selector)))
        questions = self.driver.find_elements_by_css_selector(question_css_selector)

        matched = list(filter(lambda m: 'test_question' in m.text, questions))

        self.assertEqual(len(matched), 20)

    def test_search_by_tag(self):
        """Verify that it is possible to find question by tag"""
        self.generate_test_data()

        search_path = "//input[@name='search']"
        apply_search_path = "//button[contains(text(), 'GO')]"
        tag_css_selector = ".tag"

        self.get_index_page()

        search = self.wait.until(ec.presence_of_element_located((By.XPATH, search_path)))
        search.send_keys("tag:tag2")

        apply_search = self.wait.until(ec.presence_of_element_located((By.XPATH, apply_search_path)))
        apply_search.click()

        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, tag_css_selector)))
        tags = self.driver.find_elements_by_css_selector(tag_css_selector)

        matched = list(filter(lambda m: 'tag2' in m.text, tags))

        self.assertEqual(len(matched), 10)

    def test_login(self):
        """Verify that registered user is able to log in"""
        avatar_css_selector = ".avatar"
        displayed_name_path = "//a[contains(text(), '" + self.username + "')]"
        ask_question_path = "//a[contains(text(), 'Ask new question')]"
        logout_ref = "//a[contains(text(), 'logout')]"

        self.generate_test_data()
        self.get_index_page()
        self.setup_login()

        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, avatar_css_selector)))
        self.wait.until(ec.presence_of_element_located((By.XPATH, displayed_name_path)))
        self.wait.until(ec.presence_of_element_located((By.XPATH, ask_question_path)))
        self.wait.until(ec.presence_of_element_located((By.XPATH, logout_ref)))

    def test_ask_question(self):
        """Verify that registered user is able to ask new question"""
        ask_question_path = "//a[contains(text(), 'Ask new question')]"
        q_header_id = "q_header"
        q_content_id = "q_content"
        q_tags_id = "q_tags"
        q_button_id = "q_button"
        tag_css_selector = ".tag"
        question_css_selector = ".question_separator"

        self.generate_test_data()
        self.get_index_page()
        self.setup_login()

        ask_question = self.wait.until(ec.presence_of_element_located((By.XPATH, ask_question_path)))
        ask_question.click()

        q_header = self.wait.until(ec.presence_of_element_located((By.ID, q_header_id)))
        q_header.send_keys("New question")

        q_content = self.wait.until(ec.presence_of_element_located((By.ID, q_content_id)))
        q_content.send_keys("New question details")

        q_tags = self.wait.until(ec.presence_of_element_located((By.ID, q_tags_id)))
        q_tags.send_keys("tag1, tag2, tag3")

        q_button = self.wait.until(ec.presence_of_element_located((By.ID, q_button_id)))
        q_button.click()

        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, tag_css_selector)))
        tags = self.driver.find_elements_by_css_selector(tag_css_selector)

        matched_tags = list(filter(lambda m: 'tag1' or 'tag2' or 'tag3' in m.text, tags))

        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, question_css_selector)))
        questions = self.driver.find_elements_by_css_selector(question_css_selector)

        matched_questions = list(filter(lambda m: 'New question' in m.text, questions))

        self.assertEqual(len(matched_tags), 3)
        self.assertEqual(len(matched_questions), 1)

    def test_answer(self):
        """Verify that registered user is able to give answers"""
        question_path = "//a[contains(text(), 'test_question1')]"
        answer_area_id = "answer"
        answer_button_id = "a_button"
        answer_css_selector = ".answer_block"

        self.generate_test_data()
        self.get_index_page()
        self.setup_login()

        question = self.wait.until(ec.presence_of_element_located((By.XPATH, question_path)))
        question.click()

        for i in range(1, 6, 1):

            answer_area = self.wait.until(ec.presence_of_element_located((By.ID, answer_area_id)))
            answer_area.send_keys("New answer №" + str(i))

            answer_button = self.wait.until(ec.presence_of_element_located((By.ID, answer_button_id)))
            answer_button.click()

        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, answer_css_selector)))
        answers = self.driver.find_elements_by_css_selector(answer_css_selector)

        self.assertEqual(len(answers), 5)
