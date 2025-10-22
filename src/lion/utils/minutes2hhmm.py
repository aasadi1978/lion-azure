def minutes2hhmm(m):

    try:

        h = int(int(m)/60)
        hh = f'0{h}' if h < 10 else f'{h}'
        mn = f'00{int(m - h * 60)}'[-2:]

        return f'{hh}:{mn}'

    except Exception:
        return ''