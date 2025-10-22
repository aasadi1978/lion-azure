## Setting up LION for users

This section guides end-users through installing (or re-installing) **LION** on Windows using the provided installer script.

### Prerequisites

- **Windows** machine.
- **Python 3.12.2+** installed and available on `PATH` (so `python` runs in Command Prompt).
- A **LION wheel** file (`.whl`) either:

  - in the same folder as the installer script, or
  - in a shared location at `%LION_SHARED_DIR%\Installer`.

### Set up an app folder

1. Create a folder for the app, e.g., LION-APP
2. copy the batch file `install_lion.bat` (or a similar wrapper) to the app directory
3. Optionally (but recommended), create an empty LION_HOME directory. If not the cuurent directory will be used as lion_home

### Migerate to new LION setup

In the case, older master database and runtimes information have to be imported, just copy the databases `lion_master_data.db` and `lion_runtimes_default.db` into `sqldb` directory in current folder or `DELTA_HOME` and restart the app. The master databases, including runtimes will be automatically upgraded. Scenarios created by the older LION, will be upgraded autoamtically upon importing into the app

### Quick start (recommended)

1. Close the LION app if it’s open.
2. (If using a shared installer) set the shared folder path:

   ```bat
   set LION_SHARED_DIR=\\your\share\path
   ```

3. Run the installer (double-click `install_lion.bat` or run from Command Prompt):

   ```bat
   install_lion.bat
   ```

4. On success, the console shows:

   - the wheel path used,
   - the installed version (via `importlib.metadata`),
   - and `import ok: lion`.

> If you see **“No installer found! The window can be closed.”** the script couldn’t find a `.whl` in the current folder or `%LION_SHARED_DIR%\Installer`.

### What the installer does

- Stops running `lion.exe` and `Python.exe` to avoid file locks.
- Looks for a `.whl` in the current folder, then `%LION_SHARED_DIR%\Installer`.
- Creates/activates a local virtual environment `venv`.
- Uninstalls any existing `lion` package from that env.
- Cleans pip cache, upgrades pip.
- Installs LION from the found `.whl` with `--force-reinstall`.
- Verifies by printing the installed version and testing `import lion`.

### Notes for users

- You may need to run from an **Administrator** Command Prompt if process termination fails.
- The LION installation is isolated inside the local `venv` folder next to the script.
- To re-install, re-run the same script; it will handle cleanup automatically.

### Troubleshooting

- **Installer can’t find the wheel**

  - Ensure a `.whl` sits next to `install_lion.bat`, **or** set `%LION_SHARED_DIR%` and place the wheel in `%LION_SHARED_DIR%\Installer`.

- **Virtual environment creation fails**

  - Ensure `python` runs in Command Prompt and try:

    ```bat
    python -m ensurepip --upgrade
    ```

    then re-run the installer.

- **Activation fails or `venv\Scripts\activate.bat` missing**

  - Delete the `venv` folder and re-run the installer.

- **Pip install errors**

  - Verify the wheel matches your Python version/architecture (e.g., 64-bit).
  - Temporarily disable VPN/proxy if network hooks interfere with pip’s upgrade step.

---

## Setting up LION for developement

### 1. Clone the Repository

Navigate to your working directory (e.g., `LION_APP`) and run:

```bash
git clone git@github.com:alireza-asadi_fedex/LION-UK.git
```

> 🔀 Currently, we are working on the branch `LION-UK-Restructuring`.

If the wrong branch (e.g., `main`) is checked out by default, you can switch manually:

```bash
cd LION_APP
git fetch origin
git checkout master
git branch --set-upstream-to=origin/master master
```

---

### 2. Download Shared Assets

Manually download the `images` folder from your SharePoint directory (`LION_SHARED_ASSETS_PATH`), e.g., `%OneDrive%\LION-UK\LION_SHARED_ASSETS` and copy into the `static` directory of your cloned `LION_APP` project.

---

### 3. Set Up the Python Environment

It is recommended to use **Python 3.12.2**. Once python isntalled, it is recommended to create a virtual environemnt to isolate your development environement:

#### On Windows:

```powershell
python -m venv venv
```

If you have multiple python versions, you can specify the full path to the corresponding `python.exe`. In other words:

```powershell
PATH\TO\python.exe -m venv venv
```

#### Activate venv:

```bash
# Windows
venv\Scripts\activate
```

---

### 4. Install Dependencies

Inside the activated virtual environment, install the required Python packages:

```bash
pip install -r requirements.txt
```

---

### 6. Start the App

Finally, to run the app:

```bash
# Windows
start_lion_uk.bat

```

### Project tree view

The file `project_tree_view.md` contains the tree view of the project which helps the developer understand the folder structure.
