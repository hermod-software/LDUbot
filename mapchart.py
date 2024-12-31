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
import yaml
import discord
from discord.ext import commands, tasks

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
    options.add_argument("--headless")


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

        await asyncio.sleep(6)        

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
                return None, "failed to download"
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
    return filename

async def main():
    with open("downloads/txt/test.txt", "r") as f:
        config = f.read()

    await fetch_image(config, "victoria-3-provinces", "loritsi")

if __name__ == "__main__":
    asyncio.run(main())

class Mapchart(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        if os.path.exists("savedata/mapchart.yml"):
            with open("savedata/mapchart.yml", "r") as f:
                self.config = yaml.safe_load(f)
        print("Mapchart cog loaded")

    @discord.app_commands.command(name="mapchart", description="generate a mapchart image from a txt attachment")
    async def mapchart(self, interaction: discord.Interaction, mapchart_txt: discord.Attachment, mapchart_url: str):
        file = mapchart_txt

        try: 
            config = await file.read()            # read the file as bytes
            config = config.decode("utf-8") # turn it into utf-8
        except Exception as e:
            print("failed to read and decode the file (possibly corrupted)")
        user = interaction.user.name    # get the user's username


        if not file.filename.endswith(".txt"):
            await interaction.followup.send("the file must be a .txt file")
            return
        
        await interaction.response.defer()  # we can't respond straight away so we need to defer the response

        filename = await fetch_image(config, mapchart_url, user) # this bit takes a while and returns the filename of the downloaded map

        if filename is None:
            await interaction.followup.send("the download failed, please try again (or report this as a bug on the github page)")
            return

        try:
            await interaction.followup.send(
                content="mapchart image saved:",
                file=discord.File(filename)
            )
        except FileNotFoundError:
            await interaction.followup.send("the file was downloaded, but it couldn't be found. please try again (or report this as a bug on the github page)")

        if os.path.exists(filename):
            os.remove(filename)
        


async def setup(client):
    await client.add_cog(Mapchart(client))
