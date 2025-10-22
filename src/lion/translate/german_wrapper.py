from lion.translate.base_translator import BaseTranslator


class GermanTranslatorWrapper(BaseTranslator):

    weekdays_en_de = {
        "Mon": "Mo", "Tue": "Di", "Wed": "Mi",
        "Thu": "Do", "Fri": "Fr", "Sat": "Sa", "Sun": "So"
    }

    dct_overrides = {
        "Start Point": {"full": "Startpunkt", "short": "Start"},
        "End Point": {"full": "Zielpunkt", "short": "Ziel"},
        "TU Destination": {"full": "TU-Ziel", "short": "TU"},
        "Start Time": {"full": "Abfahrtszeit", "short": "A. Zeit"},
        "End Time": {"full": "Ankunftszeit", "short": "A. Zeit"},
        "Driving Time": {"full": "Fahrzeit", "short": "Fahrzeit"},
        "Miles": {"full": "Meilen", "short": "Meilen"},
        "Traffic Type": {"full": "Verkehrsart", "short": "Verkehr"},
        "Break": {"full": "Pause", "short": "Pause"},
    }

    def translate_weekday(self, weekday):
        return self.weekdays_en_de.get(weekday, self.sync_translate(weekday))

    def translate_text(self, text):
        if text in self.weekdays_en_de:
            return self.weekdays_en_de[text]
        if text in self.dct_overrides:
            return self.dct_overrides[text]["short"]
        return self.sync_translate(text).replace(".", ". ").replace("  ", " ").strip()

    def driver_leaves_loc_at(self, loc, departure_time):
        return f"Der Fahrer beginnt seinen Dienst in {loc} um {departure_time}. "

    def then_drivers_4_to_arrive_at(self, driving_time, dest, arrival_time):
        return f"Er führt eine erste Fahrt von {driving_time} durch, um {dest} um {arrival_time} zu erreichen. "

    def can_take_break_here(self, break_duration):
        return f"Eine Pause von {break_duration} kann an diesem Standort eingelegt werden. "

    def poa(self, poa_duration):
        return f"Die Verfügbarkeitsdauer an diesem Standort beträgt {poa_duration}. "

    def finally_drives_to_arrive_at(self, dur, dest, arrival_time):
        return f"Der Fahrer setzt seine Fahrt für einen zweiten Abschnitt von {dur} fort, mit einer voraussichtlichen Ankunft in {dest} um {arrival_time}. "

    def total_shift(self, total_shift_duration):
        return f"Die Gesamtdauer der Schicht beträgt {total_shift_duration}. "

    def total_driving_time(self, total_driving_time):
        return f"Die gesamte Fahrzeit beträgt {total_driving_time}. "

    def total_idle_time(self, idle_time):
        return f"Die gesamte Leerlaufzeit beträgt {idle_time}. "
