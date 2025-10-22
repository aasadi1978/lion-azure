from PIL import Image
from os import path as os_path
from lion.config.paths import LION_IMAGES_PATH

def pushpin(loc_type=None):

    pushpins = {}
    pushpins['CUSTOMER'] = "blue-pin 25px.png"
    pushpins['HUB'] = "red-pin 25px.png"
    pushpins['SWAP'] = "red-pin 15px.png"
    pushpins['RTH'] = pushpins['HUB']
    pushpins['STATION'] = "orange-pin 15px.png"
    pushpins['DEPOT'] = pushpins['STATION']
    pushpins['GATEWAY'] = "icons8-airplane-take-off-30 orange.png"
    pushpins['AIRPORT'] = pushpins['GATEWAY']
    pushpins['PORT'] = "icons8-boat-leaving-port-24.png"
    pushpins['RAMP'] = "icons8-airplane-take-off-25 black.png"
    pushpins['AirHub'] = pushpins['GATEWAY']
    pushpins['AIRHUB'] = pushpins['GATEWAY']

    if loc_type:

        pshpin = {}
        if loc_type.upper() in pushpins.keys():
            myimg = pushpins[loc_type.upper()]
            img = Image.open(os_path.join(
                LION_IMAGES_PATH, myimg))

        else:
            myimg = 'location-pointer 25px.png'
            img = Image.open(os_path.join(
                LION_IMAGES_PATH, 'location-pointer 25px.png'))

        s = img.size
        pshpin['imageFile'] = myimg

        if myimg in ["blue-pin 25px.png"]:
            pshpin['width'] = s[0] + 10
        else:
            pshpin['width'] = s[0]

        if myimg in ["red-pin 25px.png"]:
            pshpin['height'] = s[1] - 10
        else:
            pshpin['height'] = s[1]

        return pshpin

    loc_types = list(pushpins)
    pshpins = {}
    for loc_type in loc_types:
        pshpin = {}
        if loc_type.upper() in pushpins.keys():
            myimg = pushpins[loc_type.upper()]
            img = Image.open(os_path.join(
                LION_IMAGES_PATH, myimg))

        else:
            myimg = 'location-pointer 25px.png'
            img = Image.open(os_path.join(
                LION_IMAGES_PATH, 'location-pointer 25px.png'))

        s = img.size
        # pshpin['path'] = f"{LION_IMAGES_PATH}\{myimg}".replace('\\', '/')
        # pshpin['path'] = url_for('static', filename=f'pushpins/{myimg}')
        pshpin['imageFile'] = myimg

        if myimg in ["blue-pin 25px.png"]:
            pshpin['width'] = s[0] + 10
        else:
            pshpin['width'] = s[0]

        if myimg in ["red-pin 25px.png"]:
            pshpin['height'] = s[1] - 10
        else:
            pshpin['height'] = s[1]

        pshpins[loc_type] = pshpin

    return pshpins
