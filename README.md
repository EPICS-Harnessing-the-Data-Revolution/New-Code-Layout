# Running the HDR Server


## Steps
1. `env/scripts/activate`
2. `python manage.py runserver`
3. in your browswer of choice: `127.0.0.1:8000`

## Details

Open a terminal either through VS Code or command prompt. On older installs of VS Code it might be neccesariy to run the following command if you use the in-built VS Code terminal: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` This will allow scripts to run in the VS terminal. 


After that you will need to set up the env folder, if it has not already been set up. 
- You will only need to do this once per commputer, unless you move or replace your repository. Make sure your terminals path (the file path listed on each terminal line) is on the top level of your repository folder. It will be something along the lines of
    - `C:\Users\your_name\Documents\GitHub\your_forked_repo`
 
 The first command is `python -m venv env`
 Now enter the environment you just created with `env\scripts\activate` 
 - You will need to run this command every time you run the server
 - The command may also differ slightly depending on os, you may need `source env\scripts\activate`, and the exact activation file may change, though the directory is the same

 Before you run the server you will need to install a few python packages. Python should come with pip, a package installer and the command is `pip install -r requirements.txt` 
 - The current list of packages as of Nov 2023 is: django, numpy, plotly, xlsxwriter, whitenoise. There may be more neccesary down the line.
 - `pip install package_name` is used to install specific packages if the above command doesn't do everything needed


After you are done installing the requisite packages, run `env\scripts\activate` (The exact script run can vary depending on os, but it will be located in the same file regardless) 

Followed by `python manage.py runserver`
-  If there are any additional packages you need to install it will ask you to do so now. You might also ask you to migrate some files. Just follow the command it gives you. 

The server should be running. If you ever want to stop the server running so you can use the terminal for something else, the command is `Ctrl + C`. In order to see the server pages, open up any browser and go to `127.0.0.1:8000` (or `127.0.0.1:8000/home` for older versions) This should open the home page and you can navigate fromt there. 
