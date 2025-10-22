from webbrowser import open_new


def open_browser(port=8080):
    open_new(f'http://localhost:{int(port)}')