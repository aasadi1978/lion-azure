from lion.translate.base_translator import BaseTranslator


class ItalianTranslatorWrapper(BaseTranslator):

    weekdays_en_it = {
        "Mon": "Lun", "Tue": "Mar", "Wed": "Mer",
        "Thu": "Gio", "Fri": "Ven", "Sat": "SSab", "Sun": "Dom"
    }

    dct_overrides = {
        "Start Point": {"full": "Punto di partenza", "short": "Inizio"},
        "End Point": {"full": "Punto finale", "short": "Fine"},
        "TU Destination": {"full": "Destinazione TU", "short": "TU"},
        "Start Time": {"full": "Ora di partenza", "short": "O. partenza"},
        "End Time": {"full": "Ora di arrivo", "short": "O. arrivo"},
        "Driving Time": {"full": "Tempo di guida", "short": "Guida"},
        "Miles": {"full": "Miglia", "short": "Miglia"},
        "Traffic Type": {"full": "Tipo di traffico", "short": "Traffico"},
        "Break": {"full": "Pausa obbligatoria", "short": "Pausa"},
    }

    def translate_weekday(self, weekday):
        return self.weekdays_en_it.get(weekday, self.sync_translate(weekday))

    def translate_text(self, text):
        if text in self.weekdays_en_it:
            return self.weekdays_en_it[text]
        if text in self.dct_overrides:
            return self.dct_overrides[text]["short"]
        return self.sync_translate(text).replace(".", ". ").replace("  ", " ").strip()

    def driver_leaves_loc_at(self, loc, departure_time):
        return f"L'autista inizia il servizio a {loc} alle {departure_time}. "

    def then_drivers_4_to_arrive_at(self, driving_time, dest, arrival_time):
        return f"Esegue un primo tragitto di {driving_time} per arrivare a {dest} alle {arrival_time}. "

    def can_take_break_here(self, break_duration):
        return f"È possibile fare una pausa di {break_duration} in questo luogo. "

    def poa(self, poa_duration):
        return f"Il periodo di disponibilità in questo luogo è di {poa_duration}. "

    def finally_drives_to_arrive_at(self, dur, dest, arrival_time):
        return f"L'autista riprende la strada per un secondo tragitto di {dur}, con arrivo previsto a {dest} alle {arrival_time}. "

    def total_shift(self, total_shift_duration):
        return f"La durata totale del turno è di {total_shift_duration}. "

    def total_driving_time(self, total_driving_time):
        return f"Il tempo totale di guida è di {total_driving_time}. "

    def total_idle_time(self, idle_time):
        return f"Il tempo totale di inattività è di {idle_time}. "
