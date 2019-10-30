# AST-Server
AST Server is a python3 application for authenticating and handling diagnostic results for Apple's AST 1 ADR Server. The file "server.py" is designed for AST versions up to 1.5.25v38. For AST 1.5.27, the file "server_1527.py" is required.

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
6. Edit server.py or server_1527.py and enter your mysql credentials and change the secret key.
```
Note: There might be other dependencies required depending on your current python installation. Any error messages should indicate what additional modules you need to install.

__Usage for AST Servers up to version 1.5.25v38:__
```
python3 server.py
```

__Usage for AST Server 1.5.27:__
```
python3 server_1527.py
```

__Additional Installation Instructions for AST Server 1.5.27:__

AST 1.5.27 will not work with server_1527.py out of the box. You will need to replace a few system files in order for it to work properly.
```
1. Install AST 1.5.27 normally
2. replace the following files with the files from AST 1.5.25v38:

/usr/local/libexec/gw_controld
/usr/local/libexec/gw_datad
/usr/local/libexec/gw_logd

/usr/share/man/man8/gw_controld.8
/usr/share/man/man8/gw_datad.8
/usr/share/man/man8/gw_logd.8
```
These files are what control the protocols for AST. This is still an experimental patching process. So far, this process seems to work correctly, and test logs etc are successfully received by the server. The only noticeable issue is cosmetic, in that when booted into the AST diagnostic utility, the AST Version symbol shows the red exclaimation symbol.

__Connections:__

Once server is running, connect to ```127.0.0.1:5000``` in a web browser (unless you have edited these values in server.py). Register an account. Log in to the newly created account and view your profile page for Account ID / Store # required for login.

Gateway Manager connects to: (make sure to use http and not https)
```
http://127.0.0.1:5000/services/ws/capture
```
Your login credentials are the email you used to create the account, the password created and the store #. Please note that AST server 1.5.27 does not require a password.

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

__Extras:__

Included is an uninstaller for previously installed versions of Apple Service Toolkit / Gateway manager. It is not an uninstaller for this server! It is to enable you to perform a clean install of Apple Service Toolkit. To run:
```
sudo bash uninstall.sh
```
