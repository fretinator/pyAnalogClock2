# ****************************************************************************************
# Draw an Analog Clock using a little Rectangular to Polar Coordinate Fun. Uses RTC Clock
# to keep time. 
# ****************************************************************************************
from datetime import datetime
from modules.analog_clock import AnalogClock
from guizero import App, Drawing, Box, TextBox

def drawDate():
    global DateField
    DateField.rectangle(0, 0, DateField.width, DateField.height, bgApp, False)
    now = datetime.now()
    x = int((DateField.width/ 2) - (DateField.width / 5))
    y = int(DateField.height / 10)
    size = int(DateField.width / 20)
    month = str(now.month)
    day = str(now.day)
    year = str(now.year)
    DateField.text(x, y, month + '/' + day + '/' + year, fgDate, 'courier', size)


def resizeDateField():
    global DateField
    DateField.resize(app.width, int(app.height * 0.75))
    drawDate()
def app_resize():
    global canvas, clock, DateField
    # Resize main canvas objects who also have resize handlers
    canvas.resize(app.width / 2, int(app.height * 0.75))
    clock.handle_resize()
    resizeDateField()


bgApp: str = '#0000FF'
fgDate: str = 'WHITE'
# Create App
app: App = App('Savina\'s Clocl', width=600, height=800, layout="grid", bg=bgApp)

# Create AnalogClock
canvas: Drawing = Drawing(app, app.width, int(app.height * .75), grid=[0, 0])
clock: AnalogClock = AnalogClock(app, canvas)
DateField = Drawing(app, app.width, int(app.height * 0.25), grid=[0,1])
drawDate()

app.when_resized = app_resize
app.full_screen = True
app.display()
