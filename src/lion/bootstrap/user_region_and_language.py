
# NOTE: User group name is determiend based on the location data. This means that
# when providing location data, the user group name must be included. The provided 
# environemnt variables is to simplify developer's work to switch between regions
# As a onboarding processes, make sure a right group_name is provided in the 
# input data, e.g., in orm.location

from lion.bootstrap.constants import COUNTRY_LANGS

def get_rgn(user_group_name):

    cntry_code = user_group_name.split('-')[2] # fedex-lion-uk-users
    try:
        return str(cntry_code).upper() if cntry_code.lower() != 'uk' else 'GB'
    except Exception:
        return 'GB'

def get_lang(user_group_name):

    cntry_code = user_group_name.split('-')[2]
    try:
        return COUNTRY_LANGS.get(cntry_code, []).pop(0)
    except Exception:
        return 'English'
