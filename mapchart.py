import asyncio
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
import os

download_dir = "./downloads/image"
download_dir = os.path.abspath(download_dir)

gecko_driver = "./geckodriver.exe"
BASE_URL = "https://mapchart.net/"

  

async def fetch_image(config, mapname, user="no_user"):

    if not BASE_URL in mapname:
        full_url = BASE_URL + mapname
    else:
        full_url = mapname

    if not full_url.endswith(".html"):
        full_url += ".html"

    options = Options()
    options.headless = True

    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", download_dir)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "image/png")
    options.set_preference("browser.download.useDownloadDir", True)
    #options.add_argument("--headless")


    driver = webdriver.Firefox(
        options=options,
        service=Service(gecko_driver)
    )


    try:
        print("driver capabilities: ", driver.capabilities)
        print(f"accessing {full_url}")
        driver.get(full_url)
        print("waiting for page to load...")
        asyncio.sleep(2)
        print("page loaded!")

        print("clicking agree button...")
        try:
            agree_button = driver.find_element(By.XPATH, "//button[text()='Agree and proceed']")
            agree_button.click()
            print("clicked agree to cookies button")
            await asyncio.sleep(0.5)
        except Exception:
            print("no agree button found, continuing...")

        try:
            vic3continue = driver.find_element(By.ID, 'vic3-continue-btn')
            vic3continue.click()
            print("clicked vic3 continue button")
            await asyncio.sleep(0.5) # wait for the fadeout animation to finish
        except Exception:
            pass




        saveloadbutton = driver.find_element(By.ID, 'downup') # find the button for opening the load menu
        saveloadbutton.click() #click it

        print("waiting for config textarea to show up...")
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, 'upload-config-textarea')))
        print("config textarea is visible!")
        textarea = driver.find_element(By.ID, 'upload-config-textarea') # find the bit where you can paste the config
        driver.execute_script("arguments[0].value = arguments[1];", textarea, config) # javascript is faster than send_keys i think
        #textarea.send_keys(config)
        print("pasted config into textarea")
        await asyncio.sleep(0.5) # wait for the textarea to update
        uploadbutton = driver.find_element(By.ID, 'upload-config') # find the button for loading configurations
        uploadbutton.click() # click it

        print("waiting for map to load in...")

        await asyncio.sleep(4)        

        print("opening legend options...")
        legend_options = driver.find_element(By.ID, 'advanced-legend-btn')
        legend_options.click()
        await asyncio.sleep(0.1)
        print("hiding legend...")
        legend_status = driver.find_element(By.ID, 'legend-status')
        select = Select(legend_status)
        select.select_by_value("hide")

        maptitle = driver.find_element(By.ID, 'map-title')
        driver.execute_script("arguments[0].value = arguments[1];", maptitle, user)

        await asyncio.sleep(5)

        attempts = 0
        

        body = driver.find_element(By.TAG_NAME, 'body')
        body.send_keys(Keys.ALT + 'd')
        print("download started")
        print("waiting for download to finish...")

        waits = 0
        while True:
            await asyncio.sleep(1.5)
            if waits > 20:
                print("download failed, giving up")
                return None
            files = os.listdir(download_dir)
            downloadstarted = os.path.exists(os.path.join(download_dir, f"{user}.png"))
            if not any([f.endswith(".part") for f in files]) and downloadstarted:
                break
            else:
                waits += 1
                print(f"download still in progress... ({waits} waits)")

        filename = os.path.join(download_dir, f"{user}.png")

    finally:
        driver.quit() # close the browser
        print("driver closed")
        print(f"files should be saved in: {os.path.abspath(download_dir)}")
    return filename

async def main():
    with open("downloads/txt/test.txt", "r") as f:
        config = f.read()

    await fetch_image(config, "victoria-3-provinces", "loritsi")

if __name__ == "__main__":
    asyncio.run(main())

