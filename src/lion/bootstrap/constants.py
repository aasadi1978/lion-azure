from datetime import datetime, timedelta
from importlib.metadata import version


COUNTRY_LANGS = {
    # Americas
    "US": ["English"],
    "CA": ["English", "French"],
    "MX": ["Spanish"],
    "BR": ["Portuguese"],
    "AR": ["Spanish"],
    "CL": ["Spanish"],
    "CO": ["Spanish"],
    "PE": ["Spanish"],
    "VE": ["Spanish"],
    "UY": ["Spanish"],
    "PY": ["Spanish", "Guaraní"],
    "BO": ["Spanish", "Quechua", "Aymara", "Guaraní"],
    "EC": ["Spanish"],
    "GT": ["Spanish"],
    "CU": ["Spanish"],
    "DO": ["Spanish"],
    "PR": ["Spanish", "English"],

    # Europe (incl. UK note: code is GB)
    "GB": ["English"],
    "IE": ["English", "Irish"],
    "FR": ["French"],
    "ES": ["Spanish"],
    "PT": ["Portuguese"],
    "IT": ["Italian"],
    "DE": ["German"],
    "NL": ["Dutch"],
    "BE": ["Dutch", "French", "German"],
    "LU": ["Luxembourgish", "French", "German"],
    "CH": ["German", "French", "Italian", "Romansh"],
    "AT": ["German"],
    "DK": ["Danish"],
    "NO": ["Norwegian"],
    "SE": ["Swedish"],
    "FI": ["Finnish", "Swedish"],
    "IS": ["Icelandic"],
    "PL": ["Polish"],
    "CZ": ["Czech"],
    "SK": ["Slovak"],
    "HU": ["Hungarian"],
    "RO": ["Romanian"],
    "BG": ["Bulgarian"],
    "GR": ["Greek"],
    "CY": ["Greek", "Turkish"],
    "MT": ["Maltese", "English"],
    "SI": ["Slovene"],
    "HR": ["Croatian"],
    "BA": ["Bosnian", "Croatian", "Serbian"],
    "RS": ["Serbian"],
    "ME": ["Montenegrin"],
    "MK": ["Macedonian"],
    "AL": ["Albanian"],
    "UA": ["Ukrainian"],
    "BY": ["Belarusian", "Russian"],
    "LT": ["Lithuanian"],
    "LV": ["Latvian"],
    "EE": ["Estonian"],
    "TR": ["Turkish"],

    # Middle East & North Africa
    "SA": ["Arabic"],
    "AE": ["Arabic"],
    "QA": ["Arabic"],
    "KW": ["Arabic"],
    "BH": ["Arabic"],
    "OM": ["Arabic"],
    "IQ": ["Arabic", "Kurdish"],
    "IR": ["Persian"],
    "IL": ["Hebrew", "Arabic"],
    "JO": ["Arabic"],
    "LB": ["Arabic"],
    "SY": ["Arabic"],
    "YE": ["Arabic"],
    "EG": ["Arabic"],
    "MA": ["Arabic", "Berber"],
    "DZ": ["Arabic", "Berber"],
    "TN": ["Arabic"],
    "LY": ["Arabic"],

    # Sub-Saharan Africa
    "ZA": ["Zulu", "Xhosa", "Afrikaans", "English", "Northern Sotho", "Tswana", "Sotho", "Tsonga", "Swati", "Venda", "Ndebele"],
    "NG": ["English"],
    "KE": ["English", "Swahili"],
    "TZ": ["Swahili", "English"],
    "UG": ["English", "Swahili"],
    "GH": ["English"],
    "ET": ["Amharic"],
    "SN": ["French"],
    "CI": ["French"],
    "CM": ["French", "English"],
    "CD": ["French"],
    "RW": ["Kinyarwanda", "French", "English"],
    "BI": ["Kirundi", "French", "English"],

    # South & Central Asia
    "IN": ["Hindi", "English"],
    "PK": ["Urdu", "English"],
    "BD": ["Bengali"],
    "LK": ["Sinhala", "Tamil"],
    "NP": ["Nepali"],
    "AF": ["Pashto", "Dari"],
    "KZ": ["Kazakh", "Russian"],
    "UZ": ["Uzbek"],
    "TM": ["Turkmen"],
    "TJ": ["Tajik"],
    "KG": ["Kyrgyz", "Russian"],

    # East & Southeast Asia
    "CN": ["Chinese"],
    "HK": ["Chinese", "English"],
    "MO": ["Chinese", "Portuguese"],
    "TW": ["Chinese"],
    "JP": ["Japanese"],
    "KR": ["Korean"],
    "KP": ["Korean"],
    "MN": ["Mongolian"],
    "VN": ["Vietnamese"],
    "TH": ["Thai"],
    "MY": ["Malay"],
    "SG": ["English", "Malay", "Mandarin", "Tamil"],
    "ID": ["Indonesian"],
    "PH": ["Filipino", "English"],
    "KH": ["Khmer"],
    "LA": ["Lao"],
    "MM": ["Burmese"],
    "BN": ["Malay"],

    # Oceania
    "AU": ["English"],
    "NZ": ["English", "Māori"],
    "FJ": ["Fijian", "English", "Fiji Hindi"],
    "PG": ["English", "Hiri Motu", "Tok Pisin"],

    # Eastern Europe & Caucasus
    "RU": ["Russian"],
    "GE": ["Georgian"],
    "AM": ["Armenian"],
    "AZ": ["Azerbaijani"],
    "MD": ["Romanian"],
    "BY": ["Belarusian", "Russian"],

    # Extra examples
    "EG": ["Arabic"],
    "QA": ["Arabic"],
}


update_status_log = False
MIN_REPOS_MOVEMENT_ID = int(5e6)
INIT_LOADED_MOV_ID = int(1e6)

LION_MONDAY = datetime(2022, 10, 3)
WEEKDAYS_NO_SAT = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sun']
WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
LION_DATES = {'Mon': LION_MONDAY,
                'Tue': LION_MONDAY + timedelta(days=1),
                'Wed': LION_MONDAY + timedelta(days=2),
                'Thu': LION_MONDAY + timedelta(days=3),
                'Fri': LION_MONDAY + timedelta(days=4),
                'Sat': LION_MONDAY + timedelta(days=5),
                'Sun': LION_MONDAY + timedelta(days=6)}

NOW = datetime.now()
dt_from = NOW - timedelta(days=1)
dt_from = datetime(dt_from.year, dt_from.month, dt_from.day, 12, 0)

dt_to = NOW + timedelta(days=1)
dt_to = datetime(dt_to.year, dt_to.month, dt_to.day, 11, 59)

CALENDAR_DATE_FROM = dt_from.strftime("%m/%d/%Y %H:%M")

# https://usbrandcolors.com/fedex-colors/
# https://colorhunt.co/palette/2c3333395b64a5c9cae7f6f2
# https://colorhunt.co/palettes/dark
MOVEMENT_TYPE_COLOR = {'input': '#00CC00',  # '#012169',
                        'repos': '#C8102E',  # '#FF0033',  # '#FF6600', '#C8102E'
                        'repos2': '#e83c58',  # Adhoc empty
                        'subco': '#E1E1E1',  # '#89f589',
                        'employed': '#CCD1E4',  # '#00FFFF',
                        'shift': '#E1E1E1',
                        'fixed': '#FFBF00',
                        'deleted': '#737575',
                        'changed': '#f7c42a',
                        'new': '#00FFFF',
                        'dragged': '#00FFFF',  # '#2C3333'
                        'adhoc': '#00FFFF',
                        'infeas': '#FF0033',
                        'break': '#306D75',
                        'Unknown': 'black'}



MOVEMENT_DUMP_AREA_NAME = 'Movement dump'
RECYCLE_BIN_NAME = 'Recycle bin'

LOC_STRING_SEPERATOR = '.'

LION_SQLITE_LOCAL_DATABASE = 'data.db'
TAG_NAME = f"lion-{version('lion')}"

LION_STRG_CONTAINER_DRIVER_REPORT: str = 'driver-reports'
LION_STRG_CONTAINER_LOGS: str = 'logs'
LION_STRG_CONTAINER_OPTIMIZATION: str = 'optimization'

LION_DEFAULT_GROUP_NAME:str='fedex-lion-demo'