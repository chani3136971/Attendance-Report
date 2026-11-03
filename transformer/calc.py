
from datetime import time

from models import minutes

MONTHS = ["ינו", "פבר", "מרץ", "אפר", "מאי", "יונ", "יול", "אוג", "ספט", "אוק", "נוב", "דצמ"]


def row_hours(start: time, end: time) -> float:
    return round((minutes(end) - minutes(start)) / 60, 2)