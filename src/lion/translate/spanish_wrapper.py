from lion.translate.base_translator import BaseTranslator


class SpanishTranslatorWrapper(BaseTranslator):

    weekdays_en_es = {
        "Mon": "Lun", "Tue": "Mar", "Wed": "Mié",
        "Thu": "Jue", "Fri": "Vie", "Sat": "Sáb", "Sun": "Dom"
    }

    dct_overrides = {
        "Start Point": {"full": "Punto de inicio", "short": "Inicio"},
        "End Point": {"full": "Punto final", "short": "Final"},
        "TU Destination": {"full": "Destino TU", "short": "TU"},
        "Start Time": {"full": "Hora de inicio", "short": "H. inicio"},
        "End Time": {"full": "Hora de llegada", "short": "H. llegada"},
        "Driving Time": {"full": "Tiempo de conducción", "short": "Conducción"},
        "Miles": {"full": "Millas", "short": "Millas"},
        "Traffic Type": {"full": "Tipo de tráfico", "short": "Tráfico"},
        "Break": {"full": "Pausa obligatoria", "short": "Pausa"},
    }

    def translate_weekday(self, weekday):
        return self.weekdays_en_es.get(weekday, self.sync_translate(weekday))

    def translate_text(self, text):
        if text in self.weekdays_en_es:
            return self.weekdays_en_es[text]
        if text in self.dct_overrides:
            return self.dct_overrides[text]["short"]
        return self.sync_translate(text).replace(".", ". ").replace("  ", " ").strip()

    def driver_leaves_loc_at(self, loc, departure_time):
        return f"El conductor comienza su servicio en {loc} a las {departure_time}. "

    def then_drivers_4_to_arrive_at(self, driving_time, dest, arrival_time):
        return f"Realiza un primer trayecto de {driving_time} para llegar al sitio de {dest} a las {arrival_time}. "

    def can_take_break_here(self, break_duration):
        return f"Se puede tomar un descanso de {break_duration} en este lugar. "

    def poa(self, poa_duration):
        return f"La Período de Disponibilidad en este lugar es de {poa_duration}. "

    def finally_drives_to_arrive_at(self, dur, dest, arrival_time):
        return f"El conductor retoma la ruta para un segundo trayecto de {dur}, con una llegada prevista a {dest} a las {arrival_time}. "

    def total_shift(self, total_shift_duration):
        return f"La duración total del turno es de {total_shift_duration}. "

    def total_driving_time(self, total_driving_time):
        return f"El tiempo acumulado de conducción es de {total_driving_time}. "

    def total_idle_time(self, idle_time):
        return f"El tiempo de inactividad total es de {idle_time}. "
