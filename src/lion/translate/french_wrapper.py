from lion.translate.base_translator import BaseTranslator


class FrenchTranslatorWrapper(BaseTranslator):

    weekdays_en_fr = {
        "Mon": "Lun", "Tue": "Mar", "Wed": "Mer",
        "Thu": "Jeu", "Fri": "Ven", "Sat": "Sam", "Sun": "Dim"
    }

    dct_overrides = {
        "Start Point": {"full": "Point de départ", "short": "Départ"},
        "End Point": {"full": "Point d'arrivée", "short": "Arrivée"},
        "TU Destination": {"full": "Destination TU", "short": "TU"},
        "Start Time": {"full": "Heure de départ", "short": "H. départ"},
        "End Time": {"full": "Heure d'arrivée", "short": "H. arrivée"},
        "Driving Time": {"full": "Temps de conduite", "short": "Conduite"},
        "Miles": {"full": "Miles", "short": "Miles"},
        "Traffic Type": {"full": "Type de circulation", "short": "Transport"},
        "Break": {"full": "Pause obligatoire", "short": "Pause"},
    }

    def translate_weekday(self, weekday):
        return self.weekdays_en_fr.get(weekday, self.sync_translate(weekday))

    def translate_text(self, text):
        if text in self.weekdays_en_fr:
            return self.weekdays_en_fr[text]
        if text in self.dct_overrides:
            return self.dct_overrides[text]["short"]
        return self.sync_translate(text).replace(".", ". ").replace("  ", " ").strip()

    def driver_leaves_loc_at(self, loc, departure_time):
        return f"Le conducteur débute son service à {loc} à {departure_time}. "

    def then_drivers_4_to_arrive_at(self, driving_time, dest, arrival_time):
        return f"Il effectue un premier trajet de {driving_time} pour atteindre le site de {dest} à {arrival_time}. "

    def can_take_break_here(self, break_duration):
        return f"Une pause de {break_duration} peut être prise à cet emplacement. "

    def poa(self, poa_duration):
        return f"La Période de Disponibilité à cet emplacement est de {poa_duration}. "

    def finally_drives_to_arrive_at(self, dur, dest, arrival_time):
        return f"Le conducteur reprend ensuite la route pour un second trajet de {dur}, avec une arrivée prévue à {dest} à {arrival_time}. "

    def total_shift(self, total_shift_duration):
        return f"La durée totale de la vacation est de {total_shift_duration}. "

    def total_driving_time(self, total_driving_time):
        return f"Le temps cumulé de conduite s'élève à {total_driving_time}. "

    def total_idle_time(self, idle_time):
        return f"Le temps d'inactivité total est de {idle_time}. "
