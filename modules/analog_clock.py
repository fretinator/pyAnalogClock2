# ****************************************************************************************
# Draw an Analog Clock using a little Rectangular to Polar Coordinate Fun. Uses RTC Clock
# to keep time. 
# ****************************************************************************************
import time
from datetime import datetime

from guizero import App, Drawing
from dataclasses import dataclass
import numpy as np
from typing import List


@dataclass
class RectPos:
    x1: int
    y1: int
    x2: int
    y2: int


class AnalogClockPos:
    hash_positions = []
    x: int
    y: int
    r: int

    def add_pos(rect_pos: RectPos):
        AnalogClockPos.hash_positions.append(rect_pos)

    def get_pos(the_hour: int):
        return AnalogClockPos.hash_positions[the_hour]

    def clear_pos():
        AnalogClockPos.hash_positions.clear()

    def __init(self):
        x = 0
        y = 0
        r = 0


@dataclass
class TrianglePos:
    x1: int
    y1: int
    x2: int
    y2: int
    x3: int
    y3: int


class Coordinates:
    x: int
    y: int
    r: int
    phi: float

    def __init__(self):
        x = 0
        y = 0
        r = 0
        phi = 0.0

    def from_polar(self, r, phi):
        self.x = r * np.cos(phi)
        self.y = r * np.sin(phi)


class AnalogClock:
    app: App
    screen_back_color = "BLUE"
    clock_hash_color = "BLACK"
    clock_time_color = "SILVER"
    clock_face_color = "WHITE"
    hour_hand_color = "BLACK"
    minute_hand_color = "GRAY"
    inner_circle_color = "GREEN"
    canvas: Drawing
    curMillis = 0
    lastMillis = 0
    UPDATE_MILLIS = 5000  # seconds
    firstRun = True
    prevDayOfMonth = -1
    CLOCK_PADDING = 10
    HASH_LINE_SIZE = 16
    HASH_RECT_HEIGHT = 16
    HASH_RECT_WIDTH = 8
    INNER_CIRCLE_RADIUS = 8
    HOUR_HAND_BASE = 24
    HOUR_HAND_LENGTH = 60
    MINUTE_HAND_BASE = 12
    MINUTE_HAND_LENGTH = 100
    CIRCLE_RADS = 2 * np.pi
    APPROXIMATION_VALUE = 0.001
    DATE_SEPARATION = 60  # 30 pixels below clock
    DATE_SIZE = 3  # How big to write the date
    BTN_TEXT_SIZE = 3
    BTN_TEXT_PAD = 8
    point: Coordinates
    lastHourPos: TrianglePos
    lastMinutePos: TrianglePos
    lastMinute = -1  # used to know when to redraw hands
    lastDay = -1

    def __init__(self,
        app: App,
        canvas: Drawing,
        screen_back_color = "BLUE",
        clock_hash_color = "BLACK",
        clock_face_color = "WHITE",
        hour_hand_color = "BLACK",
        minute_hand_color = "GRAY",
        inner_circle_color = "GREEN"):

        self.app = app
        self.clockCanvas = canvas
        self.screen_back_color = screen_back_color
        self.clock_hash_color = clock_hash_color
        self.clock_face_color = clock_face_color
        self.hour_hand_color = hour_hand_color
        self.inner_circle_color = inner_circle_color
        self.daysOfTheWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        self.point = Coordinates()
        self.lastHourPos = TrianglePos(0, 0, 0, 0, 0, 0)
        self.lastMinutePos = TrianglePos(0, 0, 0, 0, 0, 0)
        self.lastMinute = -1  # used to know when to redraw hands
        self.lastDay = -1  # used to know when to redraw date

        self.clockPos: AnalogClockPos = AnalogClockPos()

        self.clockWidth = int(self.clockCanvas.width / 2)
        self.clockHeight = self.clockWidth # Circle

        # Now setup Analog Clock Info
        self.calculate_clock_position()
        self.draw_clock(True, True)
        self.clockCanvas.repeat(1000, self.draw_clock)

    def approximately_equal(self, f1: float, f2: float):
        return abs(f1 - f2) < self.APPROXIMATION_VALUE


    # Guizero expects the bounding box if the circle, not the center
    # and radius
    def draw_circle(self, canvas: Drawing, x1: int, y1: int, r: int, drawColor: str,
                    outlineOnly: bool):
        new_x1: int = x1 - r
        new_y1: int = y1 - r
        new_x2: int = x1 + r
        new_y2: int = y1 + r

        if outlineOnly:
            canvas.oval(new_x1, new_y1, new_x2, new_y2, outline_color=drawColor,
                        outline=True)
        else:
            canvas.oval(new_x1, new_y1, new_x2, new_y2, color=drawColor)


    # x and y are output parameters
    def get_clock_point(self, r: int, phi: float):

        self.point.from_polar(r, phi)
        # The point fromPolar is calculating points based off of a
        # 0,0 origin, but ours is at clockPos.x, clockPos.y,
        # which in a 320 width screen is point 160, 160
        return self.point.x + self.clockPos.x, self.point.y + self.clockPos.y


    # returns float
    def get_angle_for_minute(self, theMinute: int):

        minute_slice = self.CIRCLE_RADS / 60  # Angle measurement in each hour

        # No negative angles
        if theMinute < 15:
            theMinute += 60

        # For minutes, 15 minutes is 0, so we have to take away 15 minutes
        theMinute -= 15  # Rotate my coordinate so 0 is the new "pole"

        return theMinute * minute_slice


    # Returns float to support fractional hours
    # Needed because hour keeps moving slightly while minute hand moves
    def get_angle_for_hour(self, theHour: float):
        hour_slice = self.CIRCLE_RADS / 12  # Angle measurement in each minute

        # No negative hours
        if theHour < 3:
            theHour += 12

        theHour -= 3  # Rotate my coordinate so 12 is the new "pole"

        return theHour * hour_slice


    def draw_inner_circle(self):
        self.draw_circle(self.clockCanvas, self.clockPos.x, self.clockPos.y, self.INNER_CIRCLE_RADIUS,
                    self.inner_circle_color, False)
        self.draw_circle(self.clockCanvas, self.clockPos.x, self.clockPos.y, int(self.INNER_CIRCLE_RADIUS / 2),
                    self.clock_hash_color, True)


    # Expects hour from 0 to 11, with 0 being 12 AM/PM
    def draw_time_hash(self, the_hour: int):
        my_pos = AnalogClockPos.get_pos(the_hour)

        if (the_hour % 3) == 0:
            self.clockCanvas.rectangle(my_pos.x1, my_pos.y1, my_pos.x2, my_pos.y2, self.clock_hash_color)
            self.draw_time_text(the_hour)
        else:
            self.clockCanvas.line(my_pos.x1, my_pos.y1, my_pos.x2, my_pos.y2, self.clock_hash_color)

    def draw_time_text(self, the_hour):
        hour_pos: RectPos = AnalogClockPos.get_pos(the_hour)
        font_size = int(self.clockCanvas.width / 20)
        offset = int(self.clockCanvas.width / 40)
        if 0 == the_hour:
            self.clockCanvas.text(hour_pos.x1 - offset, hour_pos.y2 + int(0.75 * offset), str(the_hour + 12),
                                  self.clock_hash_color, 'courier', font_size)

        if 3 == the_hour:
            self.clockCanvas.text(hour_pos.x1 - int(2.5 * offset), hour_pos.y1 - offset, str(the_hour),
                                  self.clock_hash_color, 'courier', font_size)

        if 6 == the_hour:
            self.clockCanvas.text(hour_pos.x1 - int(0.75 * offset), hour_pos.y2 - int(3 * offset), str(the_hour),
                                  self.clock_hash_color, 'courier', font_size)

        if 9 == the_hour:
            self.clockCanvas.text(hour_pos.x2 + offset, hour_pos.y1 - offset, str(the_hour),
                                  self.clock_hash_color, 'courier', font_size)

    def draw_face(self):
        # First draw filled circle to get back color of clock
        self.draw_circle(self.clockCanvas, self.clockPos.x, self.clockPos.y, self.clockPos.r,
                         self.clock_face_color, False)

        # Now draw outline of clock in clock_hash_color
        #draw_circle(clockCanvas, clockPos.x, clockPos.y, clockPos.r, clock_hash_color, True)

        # Then draw lines for 12 time marks
        for myHour in range(12):
            self.draw_time_hash(myHour)


    def erase_last_minute(self):
        self.clockCanvas.triangle(self.lastMinutePos.x1, self.lastMinutePos.y1,
                             self.lastMinutePos.x2, self.lastMinutePos.y2, self.lastMinutePos.x3,
                             self.lastMinutePos.y3, color=self.clock_face_color)


    def erase_last_hour(self):
        self.clockCanvas.triangle(self.lastHourPos.x1, self.lastHourPos.y1,
                             self.lastHourPos.x2, self.lastHourPos.y2, self.lastHourPos.x3,
                             self.lastHourPos.y3, color=self.clock_face_color)


    def draw_hour(self, theHour: int, theMinute: int, firstTime: bool):
        print("Drawing hour: " + str(theHour))

        if not firstTime:
            self.erase_last_hour()

        # first determine end of the hour hand triangle
        # which is the furthest point away from center of clock.
        # Use (x3,y3)
        fractional_hour = (1.0 * theHour) + (theMinute / 60.0)
        hour_angle = self.get_angle_for_hour(fractional_hour)
        self.lastHourPos.x3, self.lastHourPos.y3 = self.get_clock_point(self.HOUR_HAND_LENGTH,
                                                                        hour_angle)

        # Now get 2 base points, each is perpendicular to hour hand
        first_phi = hour_angle - (self.CIRCLE_RADS / 4)
        second_phi = hour_angle + (self.CIRCLE_RADS / 4)
        base_r = int(self.HOUR_HAND_BASE / 2)

        self.lastHourPos.x1, self.lastHourPos.y1 = self.get_clock_point(base_r, first_phi)
        self.lastHourPos.x2, self.lastHourPos.y2 = self.get_clock_point(base_r, second_phi)

        # Now draw hour hand
        self.clockCanvas.triangle(self.lastHourPos.x1, self.lastHourPos.y1,
                             self.lastHourPos.x2, self.lastHourPos.y2, self.lastHourPos.x3,
                             self.lastHourPos.y3, color=self.hour_hand_color)


    def draw_minute(self, theMinute: int, firstTime: bool):
        if not firstTime:
            self.erase_last_minute()

        # first determine end of the minute hand triangle
        # which is the farthest point away from center of clock.
        # Use (x3,y3)
        minute_angle = self.get_angle_for_minute(theMinute)
        self.lastMinutePos.x3, self.lastMinutePos.y3 = self.get_clock_point(self.MINUTE_HAND_LENGTH,
                                                                            minute_angle)

        # Now get 2 base points, each is perpendicular to hour hand
        first_phi = minute_angle - (self.CIRCLE_RADS / 4)
        second_phi = minute_angle + (self.CIRCLE_RADS / 4)
        base_r = int(self.MINUTE_HAND_BASE / 2)

        self.lastMinutePos.x1, self.lastMinutePos.y1 = self.get_clock_point(base_r, first_phi)
        self.lastMinutePos.x2, self.lastMinutePos.y2 = self.get_clock_point(base_r, second_phi)

        # Now draw hour hand
        self.clockCanvas.triangle(self.lastMinutePos.x1, self.lastMinutePos.y1,
                             self.lastMinutePos.x2, self.lastMinutePos.y2, self.lastMinutePos.x3,
                             self.lastMinutePos.y3, color=self.minute_hand_color)


    def draw_hands(self, now: datetime, firstTime: bool):
        self.draw_hour(now.hour, now.minute, firstTime)
        self.draw_minute(now.minute, firstTime)


    def draw_clock(self, firstTime: bool = False, forceDrawHands: bool = False):
        if firstTime:
            self.draw_face()

        now = datetime.now()

        self.print_time('Drawing clock', now)

        if firstTime or forceDrawHands or (now.minute != self.lastMinute):
            self.draw_hands(now, firstTime)

        self.draw_inner_circle()

        self.lastMinute = now.minute
        self.lastDay = now.day


    # Used to draw lines for 1,2,4,5,7,8,10,11
    def calculate_rect_pos_for_line(self, theHour: int):
        phi = self.get_angle_for_hour(theHour)

        r = self.clockPos.r - self.HASH_LINE_SIZE - 1  # The first point

        x1, y1 = self.get_clock_point(r, phi)

        r = self.clockPos.r - 1  # The second point

        x2, y2 = self.get_clock_point(r, phi)

        return x1, y1, x2, y2


    # Expects hour from 0 to 11, 0 = 12 AM/PM
    def get_rect_pos(self, theHour: int):
        rect_pos = RectPos(0, 0, 0, 0)

        if theHour == 0:  # RECTANGLE
            rect_pos.x1 = self.clockPos.x - (self.HASH_RECT_WIDTH / 2)
            rect_pos.y1 = self.clockPos.y - self.clockPos.r + 1
            rect_pos.x2 = rect_pos.x1 + self.HASH_RECT_WIDTH
            rect_pos.y2 = rect_pos.y1 + self.HASH_RECT_HEIGHT
            return rect_pos
        if theHour == 3:  # RECTANGLE sideways
            rect_pos.x1 = self.clockPos.x + self.clockPos.r - self.HASH_RECT_HEIGHT - 1
            rect_pos.y1 = self.clockPos.y - (self.HASH_RECT_WIDTH / 2)
            rect_pos.x2 = rect_pos.x1 + self.HASH_RECT_HEIGHT
            rect_pos.y2 = rect_pos.y1 + self.HASH_RECT_WIDTH
            return rect_pos
        if theHour == 6:  # RECTANGLE
            rect_pos.x1 = self.clockPos.x - (self.HASH_RECT_WIDTH / 2)
            rect_pos.y1 = self.clockPos.y + self.clockPos.r
            rect_pos.x2 = rect_pos.x1 + self.HASH_RECT_WIDTH
            rect_pos.y2 = rect_pos.y1 - self.HASH_RECT_HEIGHT
            return rect_pos
        if theHour == 9:  # RECTANGLE sideways
            rect_pos.x1 = self.clockPos.x - self.clockPos.r + 1
            rect_pos.y1 = self.clockPos.y - (self.HASH_RECT_WIDTH / 2)
            rect_pos.x2 = rect_pos.x1 + self.HASH_RECT_HEIGHT
            rect_pos.y2 = rect_pos.y1 + self.HASH_RECT_WIDTH
            return rect_pos
        # LINE
        rect_pos.x1, rect_pos.y1, rect_pos.x2, rect_pos.y2 = \
            self.calculate_rect_pos_for_line(theHour)

        return rect_pos


    def calculate_clock_position(self):
         # The x origin
        self.clockPos.r = (self.clockWidth - 2 * self.CLOCK_PADDING) / 2
        self.clockPos.x = self.CLOCK_PADDING + self.clockPos.r
        self.clockPos.y = self.CLOCK_PADDING + self.clockPos.r

        # Now set the positions for the 12 hashes for hours
        AnalogClockPos.clear_pos()

        for myHour in range(12):
            AnalogClockPos.add_pos(self.get_rect_pos(myHour))

        self.HOUR_HAND_LENGTH = int(self.clockPos.r / 2)
        self.MINUTE_HAND_LENGTH = int(self.clockPos.r * 0.75)


    def millis():
        now = datetime.now()
        return now.timestamp() * 1000


    def fill_canvas(self, canvas: Drawing, drawColor: str):
        canvas.rectangle(0, 0, canvas.width, canvas.height, color=drawColor)


    def print_time(self, msg: str, tm: datetime):
        print(msg + " - H=" + str(tm.hour) + ":" + str(tm.minute))

    def handle_resize(self) -> object:
        self.clockWidth = int(self.app.width / 2)
        self.clockHeight = self.clockWidth  # Circle
        self.clockCanvas.height = self.clockHeight
        self.clockCanvas.width = self.clockWidth

        self.calculate_clock_position()
        self.fill_canvas(self.clockCanvas, self.screen_back_color)
        self.draw_clock(True, True)

if __name__ == "__main__":
    app = App(title="Clock", layout='grid', height=600, width=800,
          bg="BLUE")

    clockDiameter = app.width / 2
    clockCanvas = Drawing(app, width=clockDiameter, height=clockDiameter,
                          grid=[0, 0])

    clock = AnalogClock(app, clockCanvas)

    app.when_resized = clock.handle_resize
    app.full_screen = True

    app.display()


   
