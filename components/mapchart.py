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
import json

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
        await asyncio.sleep(2)
        try:
            agree_button = driver.find_element(By.XPATH, "//button[text()='Agree and proceed']")
            agree_button.click()
            print("clicked agree to cookies button")
            await asyncio.sleep(0.5) # wait for the fadeout animation to finish
        except Exception:
            print("no agree button found, continuing...")
            pass

        try:
            vic3continue = driver.find_element(By.ID, 'vic3-continue-btn')
            vic3continue.click()
            print("clicked vic3 continue button")
            await asyncio.sleep(0.5) # wait for the fadeout animation to finish
        except Exception:
            print("no vic3 button found, continuing...")
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

        await asyncio.sleep(5)   

        print("opening legend options...")
        legend_options = driver.find_element(By.ID, 'advanced-legend-btn')
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", legend_options) # make sure the element is in view
        attempts = 0
        while True:
            if attempts > 60:
                print("failed to open legend options")
                return None
            try:
                legend_options.click()
                
                break
            except Exception:
                try:
                    uploadbutton.click() # click the upload button again to make sure the config is applied
                except Exception:
                    attempts += 1
                    await asyncio.sleep(1)
                    pass
        await asyncio.sleep(0.1)
        print("hiding legend...")
        legend_status = driver.find_element(By.ID, 'legend-status')
        select = Select(legend_status)
        select.select_by_value("title")

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
    return filename

async def main():
    with open("downloads/txt/test.txt", "r") as f:
        config = f.read()

    await fetch_image(config, "victoria-3-provinces", "loritsi")

if __name__ == "__main__":
    asyncio.run(main())

async def process_mapchart(interaction: discord.Interaction, file: discord.Attachment, mapchart_url: str):
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
        await interaction.followup.send("the command failed, please try again (or report this as a bug on the github page)")
        return

    try:
        await interaction.followup.send(
            content="mapchart image saved:",
            file=discord.File(filename)
        )
    except FileNotFoundError:
        await interaction.followup.send("the image was downloaded, but it couldn't be found. please try again (or report this as a bug on the github page)")

    if os.path.exists(filename):
        os.remove(filename) # delete the file after sending it (we don't need it anymore)

async def getmaptype(file):
    data = await file.read() # read the file as bytes
    try:
        data = json.loads(data) # try to parse it as json
        try:
            return data["page"], None
        except KeyError:
            return None, "this map is too old and has no page key. to fix this, open the config yourself in https://mapchart.net and save it again"
    except json.JSONDecodeError:
        return None, "this is not a valid configuration file (maybe corrupted)"

class Mapchart(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        if os.path.exists("savedata/mapchart.yml"):
            with open("savedata/mapchart.yml", "r") as f:
                self.config = yaml.safe_load(f)
        print("Mapchart cog loaded")

    async def cog_load(self):
        self.client.tree.add_command(mapchart_context)
        

    @discord.app_commands.command(name="mapchart_from_file", description="get a mapchart image from a txt attachment")
    async def mapchart(self, interaction: discord.Interaction, mapchart_txt: discord.Attachment):
        file = mapchart_txt
        mapchart_url, error = await getmaptype(file)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return
        await process_mapchart(interaction, file, mapchart_url)

    # @discord.app_commands.command(name="mapchart_from_id", description="get a mapchart image from message ID")
    # async def mapchart_url(self, interaction: discord.Interaction, id: str):
    #     message = await interaction.channel.fetch_message(id)
    #     if not message.attachments:
    #         await interaction.response.send_message("the message must have an attachment")
    #         return
        
    #     attachments = message.attachments

    #     for attachment in attachments:
    #         if attachment.filename.endswith(".txt"):
    #             file = attachment
    #             break

    #     mapchart_url, error = await getmaptype(file)
    #     if error:
    #         await interaction.response.send_message(error)
    #         return
    #     await process_mapchart(interaction, file, mapchart_url)

@discord.app_commands.context_menu(name="Render Mapchart Image")
async def mapchart_context(interaction: discord.Interaction, message: discord.Message):
    if not message.attachments:
        await interaction.response.send_message("the message doesn't have a mapchart txt file attached", ephemeral=True)
        return
    attachments = message.attachments
    file = None
    for attachment in attachments:
        if attachment.filename.endswith(".txt"):
            file = attachment
            break
    if file is None:
        await interaction.response.send_message("the message doesn't have a mapchart txt file attached", ephemeral=True)
        return
    mapchart_url, error = await getmaptype(file)
    if error:
        await interaction.response.send_message(error, ephemeral=True)
        return
    await process_mapchart(interaction, file, mapchart_url)

async def setup(client):
    await client.add_cog(Mapchart(client))
