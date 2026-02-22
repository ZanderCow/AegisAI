import os
import time
import uuid

import pytest
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'), override=False)

FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL', 'http://frontend:5173')
SELENIUM_REMOTE_URL = os.getenv('SELENIUM_REMOTE_URL', 'http://selenium:4444/wd/hub')
AUTH_PAGE_URL = f"{FRONTEND_BASE_URL.rstrip('/')}/e2e/auth"


@pytest.fixture(scope='module')
def driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1440,900')

    browser = webdriver.Remote(
        command_executor=SELENIUM_REMOTE_URL,
        options=options,
    )
    browser.implicitly_wait(1)
    yield browser
    browser.quit()


def _open_page(browser):
    browser.get(AUTH_PAGE_URL)
    WebDriverWait(browser, 20).until(
        EC.presence_of_element_located((By.ID, 'signup-submit'))
    )


def _submit_signup(browser, email: str, password: str):
    _open_page(browser)
    browser.find_element(By.ID, 'signup-email').clear()
    browser.find_element(By.ID, 'signup-email').send_keys(email)
    browser.find_element(By.ID, 'signup-password').clear()
    browser.find_element(By.ID, 'signup-password').send_keys(password)
    browser.find_element(By.ID, 'signup-submit').click()


def _submit_login(browser, email: str, password: str):
    _open_page(browser)
    browser.find_element(By.ID, 'login-email').clear()
    browser.find_element(By.ID, 'login-email').send_keys(email)
    browser.find_element(By.ID, 'login-password').clear()
    browser.find_element(By.ID, 'login-password').send_keys(password)
    browser.find_element(By.ID, 'login-submit').click()


def _wait_for_status(browser, element_id: str, forbidden_value: str = 'n/a') -> str:
    wait = WebDriverWait(browser, 20)

    def status_updated(_):
        value = browser.find_element(By.ID, element_id).text.strip()
        return value if value and value != forbidden_value else False

    return wait.until(status_updated)


def _status_code(browser, element_id: str) -> int:
    raw = _wait_for_status(browser, element_id)
    return int(raw)


def _text(browser, element_id: str) -> str:
    return browser.find_element(By.ID, element_id).text


def _bool_text(browser, element_id: str) -> str:
    return _text(browser, element_id).strip().lower()


def _unique_email(prefix: str = 'e2e.user') -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@example.com"


def test_signup_success_creates_user(driver):
    email = _unique_email()
    password = 'ValidPass123!'

    _submit_signup(driver, email, password)

    assert _status_code(driver, 'signup-status') == 201
    assert _bool_text(driver, 'signup-ok') == 'true'
    assert email in _text(driver, 'signup-body')


def test_signup_rejects_duplicate_email(driver):
    email = _unique_email('duplicate')
    password = 'ValidPass123!'

    _submit_signup(driver, email, password)
    first_status = _status_code(driver, 'signup-status')
    assert first_status == 201

    _submit_signup(driver, email, password)
    second_status = _status_code(driver, 'signup-status')
    assert second_status == 400
    assert 'already exists' in _text(driver, 'signup-body').lower()


def test_signup_rejects_invalid_email_format(driver):
    _submit_signup(driver, 'not-an-email', 'ValidPass123!')

    assert _status_code(driver, 'signup-status') == 422
    assert _bool_text(driver, 'signup-ok') == 'false'


def test_signup_rejects_short_password(driver):
    _submit_signup(driver, _unique_email('shortpass'), 'short')

    assert _status_code(driver, 'signup-status') == 422
    assert _bool_text(driver, 'signup-ok') == 'false'


def test_login_rejects_fake_user(driver):
    _submit_login(driver, _unique_email('fake-user'), 'ValidPass123!')

    assert _status_code(driver, 'login-status') == 401
    assert _bool_text(driver, 'login-ok') == 'false'


def test_login_succeeds_for_registered_user(driver):
    email = _unique_email('loginsuccess')
    password = 'ValidPass123!'

    _submit_signup(driver, email, password)
    signup_status = _status_code(driver, 'signup-status')
    assert signup_status == 201

    # The backend issues tokens with iat/exp timing; this small delay avoids same-second edge cases.
    time.sleep(1)

    _submit_login(driver, email, password)

    assert _status_code(driver, 'login-status') == 200
    assert _bool_text(driver, 'login-ok') == 'true'
    assert 'access_token' in _text(driver, 'login-body')


def test_login_rejects_invalid_email_format(driver):
    _submit_login(driver, 'invalid-email', 'ValidPass123!')

    assert _status_code(driver, 'login-status') == 422
    assert _bool_text(driver, 'login-ok') == 'false'


def test_page_exposes_backend_api_base_for_debug(driver):
    _open_page(driver)

    api_base = _text(driver, 'api-base-url')
    assert api_base
    assert 'http' in api_base
