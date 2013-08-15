# Hungareader

A web application for my Hungarian students.  The main idea: Read stories. Learn words.

### Getting Started

This app is powered by Google App Engine and Python.  You will need to install the app engine launcher from 

https://developers.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python

Then open it and click on Make Symlinks (which will allow you to run the `dev_appserver.py` command below).

The only Python module which should need installing is PyCrypto.  The best way to install it is

`sudo easy_install -Z pycrypto`

but if you already have a messed up version of PyCrypto, you can force an upgrade with the option -U before -Z.

Now you should be ready to rock.  Simply cd to this Hungareader directory and run

`dev_appserver.py --datastore_path=./dev_appserver.datastore --port 8888 .`

You can view the app at localhost:8888 and the datastore at localhost:8000.

