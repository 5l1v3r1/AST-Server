# AST-Server
AST Server is a python3 application for authenticating and handling diagnostic results for AST 1 ADR Server. Has been tested up to version 1.5.23v16.

__Installation:__
```
1. copy files to desired location
2. install mysql
3. create database and import ast_server.sql
4. install the following pip3 modules
      pip3 install Flask
      pip3 install xmltodict
      pip3 install mysql-connector-python
5. Edit server.py and enter your mysql credentials and change the secret key.
```
Note: There might be other dependencies required depending on your current python installation. Any error messages should indicate what additional modules you need to install.

__Usage:__
```
python3 server.py
```

__Connections:__
Once server is running, connect to ```127.0.0.1:5000``` in a web browser (unless you have edited these values in server.py). Register and account. Log in and view your profile page for Account ID / Store # required for login.

Server connects to:
```
http://127.0.0.1:5000/services/ws/capture
```
Your login credentials are the email you used to create the account, the password created and the store #.

__TODO:__
```
- error handling
- optimization
```
