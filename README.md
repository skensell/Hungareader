# Hungareader

A web application for my Hungarian students.  The main idea: Read stories. Learn words.

### Getting Started

This app is powered by Google App Engine and Python.  You will need to install the app engine launcher from Google's website.  Once you've done so simply cd to this Hungareader directory and run

`dev_appserver.py --port 8888 .`

You can view the app at localhost:8888 and the datastore at localhost:8000.


After pulling all the files in this repo, you will need to add a file `secrets.py` to /utilities/. In this file you should define two strings -- __secret__ and __encryption_key__ -- to be whatever you like. The `.gitignore` file has already been configured to ignore `secrets.py` so that it won't be included in commits.

