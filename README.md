npvrProxy
========

A small flask app to proxy requests between Plex Media Server and NextPVR (based off [tvhProxy by jkaberg](https://github.com/jkaberg/tvhProxy)).

#### tvhProxy configuration
1. In npvrProxy.py configure options as per your setup (leave npvrSID blank).
2. Create a virtual enviroment: ```$ virtualenv venv```
3. Activate the virtual enviroment: ```$ . venv/bin/activate```
4. Install the requirements: ```$ pip install -r requirements.txt```
5. Finally run the app with: ```$ python npvrProxy.py```

#### Virtual host configuration
1. Add an entry in /etc/hosts file (or whatever your OS uses) on the machine running PMS, remember to change the IP if tvhProxy resides on another server:

    ```
    127.0.0.1	localhost
    127.0.0.1	npvrproxy
    ```

#### Configure web server (virtual host)
2. Configure a web server virtual host to listen for PMS on port 80 and proxy to tvhProxy on port 5004, remember to change localhost if tvhProxy resides on another server.
    
    Nginx example:
    ```
    server {
        listen       80;
        server_name  npvrproxy;
        location / {
            proxy_pass http://localhost:5004;
        }
    }
    ```
    
    Apache example:
    ```
    <VirtualHost *:80>
        ServerName npvrProxy

        ProxyPass / http://localhost:5004/
        ProxyPassReverse / http://localhost:5004/    
    </VirtualHost>
    ```

#### systemd service configuration
A startup script for Ubuntu can be found in tvhProxy.service (change paths in tvhProxy.service to your setup), install with:

    $ sudo cp npvrProxy.service /etc/systemd/system/npvrProxy.service
    $ sudo systemctl daemon-reload
    $ sudo systemctl enable npvrProxy.service
    $ sudo systemctl start npvrProxy.service

#### Plex configuration
Enter the virtual host name as the DVR device address when setting up Plex DVR: ```npvrproxy```
