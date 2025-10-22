# Setting up LION for users

This section guides end-users through installing (or re-installing) **LION** on Windows using the provided installer script.

### Prerequisites

- **Windows** machine.
- **Python 3.12.2+** installed and available on `PATH` (so `python` runs in Command Prompt). The installer is available in `%LION_SHARED_DIR%\_onboarding\python`
- A **LION wheel** file (`.whl`) in a shared location at `%LION_SHARED_DIR%\_onboarding\whl`: `lion-1.x.x-py3-none-any.whl`.
- A **LION-Agent** file (`.whl`) in a shared location at `%LION_SHARED_DIR%\_onboarding\whl`: `lion_agent-1.x-py3-none-any.whl`.

### Installation steps

1. Install python if you have not yet done it. Verify by opening a CMD and typing `python --version`
2. If successfull, go ahead and `pip install Path\To\lion_agent-1.x-py3-none-any.whl`; If the whl path has space, wrap the full path in `"`.

- Verify lion-agent by typing `pip show lion_agent`; you shoudl get a valid package info.
- Note that `lion_agent` can be installed on main python and no venv is required

3. start the agent by typing `lion_agent`
4. Schedule a task using Windows Task Scheduler to run `lion_agent` on log in as follows:

To get **PYTHON_PATH** on your machine, run `where python` on a CMD.

Here’s your ready-to-use **Windows batch file** (`create_lion_agent_task.bat`) that sets up a scheduled task to run your `lion_agent` module every 5 minutes, indefinitely, with logging and elevated privileges — all via the main Python interpreter (no `.exe`).

---

### 🧩 `create_lion_agent_task.bat`

```bat
@echo off
@echo off
REM ===========================================================
REM  Create Windows Task Scheduler job for LION Agent
REM  Runs: python -m lion_agent
REM  Frequency: Every 5 minutes, indefinitely
REM  Privilege: Highest
REM  Logging: C:\logs\lion_agent.log
REM ===========================================================

set LION_PROJECT_PATH=%USERPROFILE%\LION_APP
set TASK_NAME=LION_Agent
set PYTHON_PATH="C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe"
set LOG_PATH=%LION_PROJECT_PATH%\lion_agent.log"
set TASK_CMD=%PYTHON_PATH% -m lion_agent >> %LOG_PATH% 2>&1

if not exist "%LION_PROJECT_PATH%" mkdir "%LION_PROJECT_PATH%"

echo Deleting old task if it exists...
schtasks /delete /f /tn "%TASK_NAME%" >nul 2>&1

echo Creating new scheduled task...
schtasks /create ^
  /tn "%TASK_NAME%" ^
  /tr "%TASK_CMD%" ^
  /sc minute ^
  /mo 5 ^
  /ru "%USERNAME%" ^
  /rl HIGHEST ^
  /f ^
  /it ^
  /delay 0000:30 ^
  /ri 5 ^
  /du 9999:59 ^
  /k no

if %ERRORLEVEL%==0 (
    echo Task "%TASK_NAME%" created successfully.
    echo.
    echo You can verify with:
    echo     schtasks /query /tn "%TASK_NAME%" /v /fo list
    echo.
) else (
    echo Failed to create the scheduled task.
)

pause
```

---

### What it does

- Runs `python -m lion_agent` (no `.exe`)
- Redirects logs to `%LOG_PATH%`
- Runs with highest privileges (`/RL HIGHEST`)
- Repeats every 5 minutes (`/SC MINUTE /MO 5`)
- Runs indefinitely (no stop condition)
- Automatically recreates the task if it already exists

---

### To use

1. Save the file as `create_lion_agent_task.bat`
2. **Right-click → Run as Administrator**
3. Verify it’s scheduled:

```bash
schtasks /query /tn "LION_Agent" /v /fo list
```

4. Check logs at:

   ```bash
   %LOG_PATH%
   ```

---

If you want the task to **start automatically at Windows boot** (even before you log in)?
you can switch to run `At startup` instead of `At logon`.
