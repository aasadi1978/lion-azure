from logging import ERROR, getLogger


def flaskWarningsOff():

    # Limit Flask console updates to Errors only
    log = getLogger('werkzeug')
    log.setLevel(ERROR)