import math


## Taken from Incursion
##"Reprise", "Icemelt", "Turnleaf", "Blossom" --spring/summer
## "Suntide", "Harvest", "Leafdry", "Softwind", --summer/fall
## "Thincold", "Deepcold", "Midwint", "Arvester", --fall/winter


calendar_data = [
    (30, "Arvester"),
    (1, "Midwinter"),
    (30, "Reprise"),
    (30, "Icemelt"),
    (30, "Turnleaf"), # April
    (1, "Greengrass"),
    (30, "Blossom"), # May
    (30, "Suntide"), # June
    (30, "Harvest"),
    (1, "Midsummer"),
    (30, "Leafdry"), # August
    (30, "Softwind"),
    (1, "Highharvestide"),
    (30, "Thincold"),
    (30, "Deepcold"), # November
    (1, "Year Feast"),
    (30, "Midwint") #December
  ]

MINUTE = 60/10
HOUR = MINUTE*60
DAY = HOUR*24
YEAR = DAY*365



class obj_Calendar():
    def __init__(self, year=1370, day=1, hour=8):
        self.calendar = []
        self.days = 0
        for m in calendar_data:
            self.days = self.days + m[0]

        self.start_year = year
        self.start_day = day
        self.start_hour = hour

        self.turn = 0

    def get_time(self, turn):
        turn = turn + self.start_hour * HOUR
        min = int(math.floor((turn % DAY) / MINUTE))
        hour = int(math.floor(min / 60))
        min = int(math.floor(min % 60))
        return hour, min

    def get_day(self, turn):
        turn = turn + self.start_hour * HOUR
        d = int(math.floor(turn / DAY) + (self.start_day))
        y = int(math.floor(d / 365))
        d = int(math.floor(d % 365))
        return d, self.start_year + y

    def get_month_num(self,day):
        i = len(calendar_data)

        while i > 0 and (day < self.days):
            i -= 1

        return i

    def get_month_name(self, day):
        month = self.get_month_num(day)
        return calendar_data[month][1]

    def get_time_date(self, turn):
        date, year = self.get_day(turn)
        month = self.get_month_name(date)
        hour, min = self.get_time(turn)
        return "Today is %s %s of %s DR. The time is %d:%d" % (date, month, year, hour, min)