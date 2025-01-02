from PIL import Image, ImageDraw, ImageFont
from math import ceil, pi, sin, cos, tan
import time
import os
import timeit

# i hate PIL but its simple and i dont need to do anything fancy

LEADERBOARDPATH = "./savedata/leaderboards/"
USERPATH = "./savedata/users/"

BLUE = (92, 91, 142)
GREEN = (100, 169, 100)
RED = (172, 40, 71)

BLURPLE = (127, 125, 193)   # blue grey
GRURPLE = (123, 206, 123)   # green grey
RURPLE = (211, 50, 91)      # red grey

BG_COLOUR = RED
CIRCLE_BLACK = (29, 27, 29)
TEXT_WHITE = (255, 255, 255)
TEXT_GRURPLE = RURPLE

if not os.path.exists(LEADERBOARDPATH):
    os.makedirs(LEADERBOARDPATH)

if not os.path.exists(USERPATH):
    os.makedirs(USERPATH)

try: # be mindful of the file type if you are changing the font (ttf, otf, et
    BIGNUMBER = ImageFont.truetype("./assets/typeface.otf", 60)  # monaspace neon extrabold
    MEDNUMBER = ImageFont.truetype("./assets/typeface.otf", 50)   # monaspace neon extrabold
    TITLE = ImageFont.truetype("./assets/typeface.otf", 40)     # monaspace neon extrabold
    BODY = ImageFont.truetype("./assets/typeface.otf", 20)      # monaspace neon extrabold
    BODY_LIGHT = ImageFont.truetype("./assets/light.otf", 20)   # monaspace neon regular
    TINY = ImageFont.truetype("./assets/typeface.otf", 15)      # monaspace neon extrabold
    TINY_LIGHT = ImageFont.truetype("./assets/light.otf", 15)  # monaspace neon regular
except IOError:
    print("!! graphics.py could not find typeface.ttf, using default font !!")
    font = ImageFont.load_default()

def timefunction(func):
    def timed(*args, **kwargs):
        start = timeit.default_timer()
        result = func(*args, **kwargs)
        end = timeit.default_timer()
        runs_per_second = 1 / (end - start)
        print(f"{func.__name__} took {end-start:.3f} seconds (est. {int(runs_per_second)} per second)") # print the time it took to run the function
        return result
    return timed


class Bounds: # a class to more easily handle bounding boxes and things we need from them
    def __init__(self, bounds):
        self.left = bounds[0]
        self.top = bounds[1]
        self.right = bounds[2]
        self.bottom = bounds[3]
        self.width = self.right - self.left
        self.height = self.bottom - self.top
        self.hmiddle = round(self.left + self.width / 2) # can't be a float
        self.vmiddle = round(self.top + self.height / 2) # can't be a float
        self.centre = (self.hmiddle, self.vmiddle)

        self.topleft = (self.left, self.top)
        self.topright = (self.right, self.top)
        self.bottomleft = (self.left, self.bottom)
        self.bottomright = (self.right, self.bottom)
def middle(a, b):
    return round((a + b) / 2) # can't be a float


def get_width(text, font):
    (width, height) = font.getsize(text)
    return width

def progress_circle(level, percent, size, index, downscale=True, firstpage=False):
    TOP3 = {
        0: (218, 177, 99),  # gold
        1: (176, 167, 184), # silver
        2: (181, 103, 43)   # bronze
    }
    if index in TOP3 and firstpage:
        colour = TOP3[index]
    else:
        colour = TEXT_WHITE

    if len(str(level)) == 1:
        font = BIGNUMBER
    elif len(str(level)) == 2:
        font = MEDNUMBER
    else:
        font = TITLE


    size = size * 2                             # we are going to downscale it later
    circle = Image.new("RGBA", (size+2, size+2))# padding to prevent clipping
    draw = ImageDraw.Draw(circle)

    draw.ellipse((0, 0, size, size), fill=CIRCLE_BLACK) # background circle

    #draw.ellipse((8, 8, size-8, size-8), outline=colour, width=6) # progress ring

    draw.arc((8, 8, size-8, size-8),-90, -90 + (360*(percent/100)), fill=colour, width=8) # progress arc (offset by -90 degrees so it starts at the top)

    draw.text((size//2, (size//2)+5), f"{level}", font=font, fill=colour, anchor="mm") # level number

    if downscale:
        circle = circle.resize((size//2, size//2), Image.LANCZOS) # downscale it for anti-aliasing purposes

    mask = circle.split()[3] # alpha channel
    return circle, mask

def user_unit(displayname, username, level, percent, tonextlevel, index, right=295, firstpage=False):
        CIRCLESIZE = 55
        halfCIRCLESIZE = ceil(CIRCLESIZE/2)

        trunc = False

        unit = Image.new("RGBA", (400,100))
        draw = ImageDraw.Draw(unit)

        top = f"{displayname}"
        displaybounds = Bounds(draw.textbbox((10,10), f"T{top}", font=BODY)) # T ensures the text is max height when calculating bounds


        while displaybounds.right > 295:    # check if the text is too long
            trunc = True
            top = top[:-1]                  # remove the last character
            displaybounds = Bounds(draw.textbbox((10,10), f"T{top}", font=BODY)) # recalculate bounds
        if trunc == True:
            top = top[:-3] + "..."              # add ellipsis if the name is too long
            trunc = False # reset truncation state

        draw.text((CIRCLESIZE + 10, 10), top, font=BODY, fill=TEXT_WHITE)

        bottom = f"{tonextlevel} to next level"

        userbounds = Bounds(draw.textbbox((10,35), f"T{bottom}", font=TINY_LIGHT))  # T ensures the text is max height when calculating bounds

        while userbounds.right > 295:       # check if the text is too long
            trunc = True
            bottom = bottom[:-1]            # remove the last character
            userbounds = Bounds(draw.textbbox((10,35), f"T{bottom}", font=TINY_LIGHT)) # recalculate bounds
        if trunc == True:
            bottom = bottom[:-3] + "..."
            trunc = False # reset truncation state

        draw.text((CIRCLESIZE + 10, 35), bottom, font=TINY_LIGHT, fill=TEXT_WHITE)

        collective_middle = middle(displaybounds.bottom, userbounds.top)

        circle, mask = progress_circle(level, percent, CIRCLESIZE, index, firstpage=firstpage)
        
        circletop = collective_middle - halfCIRCLESIZE
        circletopleft = (5, circletop)

        unit.paste(circle, circletopleft, mask)

        mask = unit.split()[3]
        return unit, mask

@timefunction
def leaderboard_image(leaderboard, guildname, page, maxpages):

    if page > 1:
        firstpage = False
    else:
        firstpage = True


    for i in range(len(leaderboard), 10):
        leaderboard.append(leaderboard[0])
    WIDTH = 600 
    HEIGHT = 360
    print(f"creating leaderboard image for {guildname}")
    print(f"length of leaderboard: {len(leaderboard)}")

    date = time.strftime("%d %m %y", time.gmtime()) # get the current date into a string (dd mm yy)

    image = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOUR)  
    draw = ImageDraw.Draw(image)

    draw.text((0, 30), f"{"_ " * 60}", font=BODY_LIGHT, fill=TEXT_GRURPLE) # dashed underline

    ypos = 50
    xpos = 0
    secondcolumn = False
    for i, user in enumerate(leaderboard):
        print(f"processing {user}")
        if i > 4 and not secondcolumn:
            xpos = 305
            ypos = 50
            secondcolumn = True
        displayname = str(user[0])
        username = str(user[1])
        level = int(user[2])
        percent = int(user[3])
        tonextlevel = int(user[4])
        unit, mask = user_unit(displayname, username, level, percent, tonextlevel, i, firstpage=firstpage)
        image.paste(unit, (xpos, ypos), mask)
        ypos += 60

    
    titlebounds = Bounds(draw.textbbox((0,0), guildname, font=TITLE))
    titlepos = (10, 10)
    titlebounds = Bounds(draw.textbbox(titlepos, guildname, font=TITLE)) # update bounds after right-aligning
    draw.text(titlepos, f"{guildname.upper()}", font=TITLE, fill=TEXT_WHITE)

    

    datebounds = Bounds(draw.textbbox((0,0), date, font=TINY, anchor="rt"))
    datepos = (WIDTH-10, 10)
    draw.text(datepos, date, font=TINY, fill=TEXT_WHITE, anchor="rt")

    pagebounds = Bounds(draw.textbbox((0,0), f"page {page}/{maxpages}", font=TINY, anchor="rt"))
    pagepos = (WIDTH-8, 28)
    draw.text(pagepos, f"(page {page}/{maxpages})", font=TINY_LIGHT, fill=TEXT_WHITE, anchor="rt")

    savepath = f"{LEADERBOARDPATH}{guildname}.png"

    image.save(savepath)
    return savepath

@timefunction
def user_level_image(entry):
    displayname, username, level, points, percent, tonextlevel, index = entry # unpack the tuple

    WIDTH, HEIGHT = 300, 100
    DIM = (WIDTH, HEIGHT)

    image = Image.new("RGB", DIM, BG_COLOUR)
    draw = ImageDraw.Draw(image)

    CIRCLE_SIZE = 55

    progress, mask = progress_circle(level, percent, CIRCLE_SIZE, index, firstpage=True)
    progress = progress.resize((60, 60), Image.LANCZOS)
    circlesize = progress.size[0]
    mask = progress.split()[3]

    circletop = HEIGHT - circlesize - 5
     # bottom of the image minus the size of the circle with padding

    image.paste(progress, (5,circletop), mask)

    titlebounds = Bounds(draw.textbbox((0,0), displayname, font=BODY))
    trunc = False
    while titlebounds.right > WIDTH-45:
        trunc = True
        displayname = displayname[:-1]
        titlebounds = Bounds(draw.textbbox((0,0), displayname, font=BODY))
        if len(displayname) < 5:
            trunc = None
            break
    if trunc == True:
        displayname = displayname[:-3] + "..."
        trunc = False
    if trunc == None:
        displayname = ""

    draw.text((10, 10), displayname, font=BODY, fill=TEXT_WHITE)

    trunc = False
    if username.lower() != displayname.lower():
        usernameisdisplayname = False
    else:
        usernameisdisplayname = True

    userpos = (titlebounds.right + 20, 13)
    ogusername = username # save the original username for the filename
    trunc = False
    userbounds = Bounds(draw.textbbox(userpos, f"({username})", font=TINY_LIGHT))
    while userbounds.right > WIDTH-45:
        trunc = True
        username = username[:-1]
        userbounds = Bounds(draw.textbbox(userpos, f"({username})", font=TINY_LIGHT))
        if len(username) < 6:
            trunc = None
            break
    if trunc == True:
        username = username[:-3] + "..."
        trunc = False
    elif trunc == None:
        username = ""

    if not username == "" and not usernameisdisplayname:
        draw.text(userpos, f"({username})", font=TINY_LIGHT, fill=TEXT_WHITE)

    draw.text((0, 14), f"{"_ " * 60}", font=BODY_LIGHT, fill=TEXT_GRURPLE) # dashed underline

    draw.text((circlesize + 10, 45), f"{points} points", font=TINY, fill=TEXT_WHITE)
    draw.text((circlesize + 10, 70), f"({tonextlevel} to next level)", font=TINY_LIGHT, fill=TEXT_WHITE)

    if index != "X":
        index = index+1
    draw.text((WIDTH-10, 10), f"#{index}", font=BODY, fill=TEXT_WHITE, anchor="rt")

    savepath = f"{USERPATH}{ogusername}.png"

    image.save(savepath)
    return savepath

    

if __name__ == "__main__":
    leaderboard_image("test", "test")
    print("leaderboard image saved")