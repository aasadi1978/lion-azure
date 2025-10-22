# lion-uk-technical-doc
This repository contains sphinx source code for LION-UK technical doc

- Execute the batch file `set_sphinx-doc-projectdir.bat` to set the project directory of envSphinx venv to current directory
- Execute `s_phinx-build-execute.bat` to build the output. Default output directory is **TEMP_Sphinx_Dist** folder in user home directory.
  If missing, the directory will be created and if available, the existing data will be overwritten
  
  
        set distDir="%userprofile%\TEMP_Sphinx_Dist"
  
        if not exist %distDir% (
           mkdir %distDir%
        )

  If you prefer a local direcotry, just create a folder called **dist** in your local project dir.

- We store large files, such as pictures, vidoes, files, etc., which we call them **media** outside git repository, e.g., in a cloud or external hard disc. The specify the path
  in `global_params.py` via the parameter `pr_media_path`. If you prefer local media directory, create a directory called **media** and store your files there. By default,
  the app will read from that folder

  Cloning the Repository: 

    - Open your terminal or command prompt.
    - Run the following command to clone the repository to your local machine:
      `git clone git@github.com:alireza-asadi_fedex/lion-uk-technical-doc.git`
    - Navigate to the project directory: `cd lion-uk-technical-doc`


