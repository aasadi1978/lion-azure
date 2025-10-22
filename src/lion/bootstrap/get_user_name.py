import getpass, subprocess, ctypes
import ctypes.wintypes as wt

def full_name() -> str:

    try:
        NameDisplay = 3
        GetUserNameExW = ctypes.windll.secur32.GetUserNameExW
        GetUserNameExW.argtypes = [ctypes.c_int, wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
        GetUserNameExW.restype = wt.BOOL
        size = wt.DWORD(0)
        GetUserNameExW(NameDisplay, None, ctypes.byref(size))
        buf = ctypes.create_unicode_buffer(size.value or 256)
        if GetUserNameExW(NameDisplay, buf, ctypes.byref(size)):
            v = buf.value.strip()
            if v:
                return v
    except Exception:
        pass

    # 2) PowerShell local/domain
    try:
        powershell_str = r'''
    $u = $env:USERNAME
    try { $l = Get-LocalUser -Name $u -ErrorAction Stop; if ($l.FullName) { $l.FullName; exit } } catch {}
    try { $a = Get-ADUser -Identity $u -Properties DisplayName -ErrorAction Stop; if ($a.DisplayName) { $a.DisplayName; exit } } catch {}
    exit 1
    '''
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", powershell_str],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        if out:
            return out
    except Exception:
        pass

    # 3) Fallback to username
    return getpass.getuser()
