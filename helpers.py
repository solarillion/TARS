from datetime import *


def reformat_time(ts):
    t = datetime.strptime(ts[11:19], "%H:%M:%S").time()
    t = datetime.combine(date.today(), t) + timedelta(hours=5, minutes=21, seconds=10)
    return t.strftime("%I:%M %p")