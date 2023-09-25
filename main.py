from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import csv, getpass, os, re, time
from datetime import datetime

save_path = input("Enter file save path relative to your home directory: ")
save_path = save_path.split("\\")
filter_start_date = input("Enter filter start date in YYYY-MM-DD format: ").strip()
login_username = input("Enter login username for Ellucian Hub: ").strip()
login_pw = getpass.getpass("Enter login password for Ellucian Hub: ").strip()
url = f'https://elluciansupport.service-now.com/customer_center?id=release_information&table=ellucian_product_release&fields=number,short_description,release_id,ellucian_product_line,ellucian_product_name,date_released,summary,description,community_url,ellucian_product_full_hierarchy&target_page_id=standard_ticket&filter=date_releasedBETWEENjavascript:gs.dateGenerate(%27{filter_start_date}%27,%2700:00:00%27)@javascript:gs.endOfToday()%5Eellucian_product_line%3Dca1944661b233c5440faa642604bcb9b%5EEQ&sel=189f215487fa0910b13d74c9cebb35d0'
updates_csv = os.path.join(os.path.expanduser('~'), *save_path, 'ellucian_product_release.csv')
update_links_dict_list = []

options = webdriver.ChromeOptions()
prefs = {"download.default_directory":os.path.join(os.path.expanduser('~'), *save_path)}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=options)
driver.implicitly_wait(7)
driver.get(url)

def login():
    login_button = driver.find_element(By.XPATH, "//button[text()='Customer Login']")
    login_button.click()
    
    username_box = driver.find_element(By.ID, "okta-signin-username")
    
    password_box = driver.find_element(By.ID, "okta-signin-password")
    
    username_box.send_keys(login_username)
    password_box.send_keys(login_pw)
    
    login_form_submit = driver.find_element(By.ID, "okta-signin-submit")
    login_form_submit.click()
    
def get_updates():
    export_btn = driver.find_element(By.ID, "optionsMenu")
    export_btn.click()
    export_csv = driver.find_element(By.XPATH, "//a[text()='Export as CSV']")
    export_csv.click()
    while not os.path.exists(updates_csv):
        time.sleep(0.5)
    
def csv_to_dict(filename):
    with open(filename) as f:
        dict_reader = csv.DictReader(f, quotechar='"')
        dict_reader = list(dict_reader)
    return dict_reader

def filter_colleague_updates(update_list):
    filtered_dict_list = [d for d in update_list if filter_condition(d)]
    return filtered_dict_list

def download_update_pdfs(update_list):
    src_filename = os.path.join(os.path.expanduser('~'), *save_path, "ellucian_product_release.pdf")
    file_downloading_end = 'crdownload'
    for upd in update_list:
        if check_exists_by_xpath("//button[text()='Customer Login']"):
            login()
        upd_url = upd['community_url']
        release_id = upd['release_id'][:8]
        print(release_id)
        summary = re.sub(r'[<>:\"\/|?*]', ' ', upd['summary'])
        new_filename = os.path.join(os.path.expanduser('~'), *save_path, f"{release_id} {summary.strip()}.pdf")
        driver.get(upd_url)
        export_btn = driver.find_element(By.ID, "printOptionsMenu")
        export_btn.click()
        pdf_button = driver.find_element(By.XPATH, "//a[text()='Export as PDF']")
        pdf_button.click()
        while not os.path.exists(src_filename):
            time.sleep(0.5)

        os.rename(src_filename, new_filename)

def filter_condition(d):
    date_format = "%Y-%m-%d"
    filter_date = datetime.strptime(filter_start_date, date_format).date()
    if d['date_released'] != "":
        return d['ellucian_product_line'] == "Colleague" and datetime.strptime(d['date_released'], date_format).date() >= filter_date
    else:
        return False
    
def check_exists_by_xpath(xpath):
    try:
        driver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        return False
    return True

if __name__ == "__main__":
    login()
    get_updates()
    dict_list = csv_to_dict(updates_csv)
    filtered_dict_list = filter_colleague_updates(dict_list)
    download_update_pdfs(filtered_dict_list)
