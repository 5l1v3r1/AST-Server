# AST-Server
AST Server is a python3 application for authenticating and handling diagnostic results for AST 1 ADR Server. Has been tested up to version 1.5.25v38.

__Installation:__
```
1. copy files to desired location
2. install python3 if not already installed
3. install mysql
4. create database and import ast_server.sql
5. install the following pip3 modules
      pip3 install Flask
      pip3 install xmltodict
      pip3 install mysql-connector-python
6. Edit server.py and enter your mysql credentials and change the secret key.
```
Note: There might be other dependencies required depending on your current python installation. Any error messages should indicate what additional modules you need to install.

__Usage:__
```
python3 server.py
```

__Connections:__

Once server is running, connect to ```127.0.0.1:5000``` in a web browser (unless you have edited these values in server.py). Register an account. Log in to the newly created account and view your profile page for Account ID / Store # required for login.

Server connects to:
```
http://127.0.0.1:5000/services/ws/capture
```
Your login credentials are the email you used to create the account, the password created and the store #.

__Change Address:__

The server comes configured by default to run on localhost (127.0.0.1:5000). But if you wish to change the ip address of the server, edit the host value on the very last line of server.py.


Default Configuration:
```
if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0')
```

Example of an Alternate Configuration:
```
if __name__ == "__main__":
	app.run(debug=True, host='192.168.1.143')
```

__TODO:__
```
- error handling
- optimization
```
