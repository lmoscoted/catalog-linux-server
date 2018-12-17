# Linux Server Configuration for Web Apps deployment

In this project we will take a baseline installation of a Linux server and prepare it to host web applications, more specificly Item Catalog App, which was developed in the [catalog repository](https://github.com/lmoscoted/catalog). We will secure our server from a number of attack vectors, install and configure a database server, and deploy our existing Item Catalog Web app onto it. I choose Google Cloud Platform as the  Linux server instance provider  and Ubuntu 16.04 LTS as our Linux OS.

*IP Address: 35.247.193.231* 

*URL using xip.io DNS service :  www.35.247.193.231.xip.io*



## Get your server
* Start a new Ubuntu Linux server instance on Amazon Lightsail. There are full details on setting up your Lightsail instance on the next page.
*  Follow the instructions provided to SSH into your server.
*  First, we need create a new project in Google Cloud Platform. Then, we go to Compute Engine and create a new Ubuntu Linux server instance.
*  On Compute Engine, select VM Instances, create Instance.
*  There, we need to provide a name for the instance, set up the time zone, choose the machine type and a Boot disk (Ubuntu 16.04 LTS)
*  Finally, choose create in order to create the Instance.

_Note:_ You need to set up the External IP address as static: 

* Go to he main menu on Google Cloud Platform, select VPC Network.
* You need to choose External IP addresses, and  change on the _type section_ from ephemeral to static, and save.

### Create Firewall rules for our VM instance
We need to create the three Firewall rules that our VM Instance will use for all the required services: HTTP (80/tcp), SSH (2200/tcp) and NTP (123/udp).

* Go to the main menu on the left-upper side and choose VPC Network.
* Select Firewall rules, and create a Firewall rule.
* You have only to provide a name,_custom-ssh_, specify a protocol and a port (2200/tcp), put 0.0.0.0/0. on the Source Ip ranges and select All instances in the network on the Targets section.  The remaining fields should not be changed.
* Then, Hit the Create botton. 
* For the incomming requests from web, we need to follow the same previous step, but on the port specification we put tcp/80.
* For the ntp requests we will do the same, specifying udp/123.

## Secure your server.
Now, we need to access to our new VM instance.On the left-upper side we choose Compute Engine, VM instances and choose SSH to connect to the VM Instance. Later, we will be logged in as an Ubuntu User. When you SSH in, you'll be logged as the ubuntu user. When you want to execute commands as root, you'll need to use the sudo command to do it.

* Update and upgrade all the installed packages:
    - sudo apt-get updatde
    - sudo apt-get upgrade
* Change the SSH port from 22 to 2200:
    - sudo nano /etc/ssh/sshd_config
    - Change port 22 to 2200, save and exit 
    - Restart the sshd service by running: sudo server sshd restart
    - Check the sshd service status: sudo service sshd status
* Configure the Uncomplicated Firewall (UFW) to only allow incoming connections for SSH (port 2200/tcp), HTTP (port 80/tcp), and NTP (port 123/udp).
    - Checking the ufw current status: sudo ufw status
    - Deny incomming requests: sudo ufw default deny incoming
    - Allow outgoing requests: sudo ufw default allow outgoing
    - Configure ssh service: sudo ufw allow 2200/tcp
    - Configure HTTP: sudo ufw allow www
    - Configure NTP: sudo ufw allow ntp/udp
    - Enable ufw: sudo ufw enable
    - Verify the ufw status: sudo ufw status


_Warning: When changing the SSH port, make sure that the firewall is open for port 2200 first, so that you don't lock yourself out of the server. When you change the SSH port, the VM instance will no longer be accessible through the web app 'Connect using SSH' button. The button assumes the default port is being used._


## Give grader user and personal user access.
We need to create two users accounts. One for project revision and another one for personal use on my local machine. As a Google Ubuntu user:

* Create a new user account named *grader*: sudo adduser grader
* Choose a password and full name (grader)

_Note: You make sure that sshd_config file require a password authentication: PasswordAuthentication yes_

* Give grader the permission to sudo: sudo cp /etc/sudoers.d/google_sudoers /etc/sudoers.d/grader
* sudo nano /etc/sudoers.d/grader, put grader save and exit.
After that, we will now be able to use sudo command as grader user.

* Create an SSH key pair for grader using the ssh-keygen tool:
    - On the local machine create a directory called .ssh.
    - On your terminal run: ssh-keygen and change last part of the suggested name by grader.
    - Log in on another terminal as grader user: ssh grader@35.247.193.231 -p 2200
    - mkdir .ssh
    - touch .ssh/authorized_keys
    -  Back on your local terminal machine: cat .ssh/grader.pub
    -  Back on the server as grader user paste the .pub content file and save it: nano .ssh/authorized_keys
*  Setup specific file permission:
   *  chmod 700 .ssh (Owner can only write, read and exec)
   *  chmod 644 .ssh/authorized_keys (Owner can write and read while the other users can only write)
* Finally on the other terminal we need to log in as grader user using key par authentication:
  * ssh grader@35.247.193.231  -p 2200 -i ~/.ssh/grader
* Now, we will need to follow  the previous steps  using your own account name instead.
  
### Forcing Key based authentication
We will force all no Google users to be only able to log in using key pair:

* On a Google Cloud terminal logged in as ubuntu user: sudo nano /etc/ssh/sshd_config
* Change Password Authentication to *no*, save and exit.
* Restart the ssh service: sudo service ssh restart 

### Disable SSH login as Root user
* On your terminal as ubuntu user we need to edit sshd_config file: sudo nano /etc/ssh/sshd_config
* In the authentication section change: _PermitRootLogin yes_ to _PermitRootLogin no_, save and exit.
* Finally, restart ssh service: sudo service ssh restart

## Prepare to deploy your project.

* Configure the local timezone to UTC. On your terminal as ubuntu user:
*  sudo timedatectl set-timezone UTC

### Install and configure Apache to serve a Python mod_wsgi application: 
 * sudo apt-get install apache2
 * sudo apt-get install libapache2-mod-wsgi-py

If you are running Debian or Ubuntu Linux with Apache 2.4 system packages, regardless of which Apache MPM is being used, you would need to install both:

* sudo apt-get install apache2-dev

### Install and configure PostgreSQL:
* sudo apt-get install postgresql
* Change the postgres user’s Linux password: sudo passwd postgres

* Do not allow remote connections 
 We can double check that no remote connections are allowed by looking in the host based authentication file:
 sudo nano /etc/postgresql/9.5/main/pg_hba.conf
* Update that file using these information:  

```
    local   all             all                                     md5 

    host    all             all             127.0.0.1/32            md5

    host    all             all             ::1/128                 md5
```


* Create a new database user named catalog that has limited permissions to your catalog application database. Logged in as postgres user:
* CREATE USER catalog WITH CREATEDB,LOGIN
* Set password: \password catalog
* Create Database for the catalog app: logged as catalog user: createdb catalogitems 
    * We can access to the catalog database using: psql -h localhost -U catalog *catalogitems*

## Deploy the Item Catalog project.
*  Install git: As ubuntu user, sudo apt-get install git
* Install pip: sudo apt-get install python-pip
* Install virtualenv: pip install virtualenv
 
* Create the configuration file for the catalog website: 
    * sudo cp /etc/apache2/sites-available/000-default.conf catalog.conf
    * Update the file according to:

```
 ServerName www.35.247.193.231.xip.io
 DocumentRoot /var/www/catalog-linux-server
 WSGIScriptAlias / /var/www/catalog-linux-server/catalogapp.wsgi
 <Directory /var/www/catalog-linux-server>
 Order allow,deny
 Allow from all
 </Directory>

```

* Save and exit.

* Clone and setup your Item Catalog project from the Github catalog project repository:  
    - clone the Item catalog project: cd /var/www then  sudo git clone https://github.com/lmoscoted/catalog-linux-server.git

* Inside project directory create a virtual environment:
 - sudo virtualenv env
 - Activate environment: source env/bin/activate
* _Install all needed modules_ inside the environment:
 - First we have to get all modules from our Linux VM where early developed our project. On the terminal: pip freeze > requirements.txt
 - Now,  inside the current directory project (/var/www): pip install -r requirements.txt
 - Install psql connexion module: pip install psycopg2 psycopg2-binary


### Set it up in the server 
In these final steps, we will ensure that our server  functions correctly when visiting your server’s IP address in a browser. And we will  make sure that your *.git* directory is not publicly accessible via a browser. 

* Set permission for .git directory:
    - Inside the project directory : sudo chmod -Rf 770 .git

* Create WSGI file for the project: 
    - sudo nano /var/www/catalog-linux-server/catalogapp.wsgi
    - Add the following code lines:
    
    ```
    import sys 
    sys.insert(0,"/var/www/catalog-linux-server")
    from init import app as application
    ```

    - Disable the default website: sudo a2dissite 000-default.conf
    - Restart Apache: sudo service apache2 restart
    - Enable the project site: sudo a2ensite catalog.conf
    - Restart Apache: sudo service apache2 restart
* Update all the url for the Oauth credential with the domain (www.35.247.193.231.xip.io) in Google Cloud and download the new json file.
* Change in the application file:
    - Update the engine creation for the Postgres Db using dialect+driver://username:password@host:port/database:
        -  `engine = create_engine('postgresql://catalog:2018catitem@localhost/catalogitems')`
    - Import psycopg2 module
    - Place the full path for client_secrets.json file: `/var/www/catalog-linux-server/client_secrets.json` both in gconnect mehtod and client_secrets data load.
    - Change the host field  in app.run to 0.0.0.0
    - Changes in the login.html file: Update the client id. 
    - Restart the apache service: sudo service apache2 restart
    - Finally, point your browser out  to www.35.247.193.231.xip.io 


# References
* [How do I change my timezone to UTC/GMT?
](https://askubuntu.com/questions/138423/how-do-i-change-my-timezone-to-utc-gmt).

* [Change the SSH port for your Linux server
](https://cl.godaddy.com/help/cambiar-el-puerto-de-ssh-para-su-servidor-linux-7306).


* [Check running services on Linux
](https://support.rackspace.com/how-to/checking-running-services-on-linux/).

* [Disable remote SSH login as root user
](https://askubuntu.com/questions/27559/how-do-i-disable-remote-ssh-login-as-root-from-a-server
).
* [How to change root password in Ubuntu Linux
](https://www.cyberciti.biz/faq/change-root-password-ubuntu-linux/
).
* [How do I change my timezone to UTC/GMT?
](https://askubuntu.com/questions/138423/how-do-i-change-my-timezone-to-utc-gmt
)

* [mod_wsgi](https://pypi.org/project/mod_wsgi/)

* [How to install pip on Ubuntu 16.04](https://www.rosehosting.com/blog/how-to-install-pip-on-ubuntu-16-04/)

* [mod_wsgi express: 'mod_wsgi.server' Documentation?](https://groups.google.com/forum/#!topic/modwsgi/YMt8VyrIvqA)

* [Start / Stop and Restart Apache 2 Web Server Command](https://www.cyberciti.biz/faq/star-stop-restart-apache2-webserver/)

* [Install mod wsgi on Ubuntu](https://stackoverflow.com/questions/44914961/install-mod-wsgi-on-ubuntu-with-python-3-6-apache-2-4-and-django-1-11)

* [How to install Postgresql on Ubuntu](https://www.linode.com/docs/databases/postgresql/how-to-install-postgresql-on-ubuntu-16-04/)

* [How to secure Postgresl on an Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-secure-postgresql-on-an-ubuntu-vps)

* [Postgres and Python](https://linuxhint.com/postgresql_python/)

* [Psycopg2 Tutorial](https://wiki.postgresql.org/wiki/Psycopg2_Tutorial)

* [Engines for sqlalchemy](https://docs.sqlalchemy.org/en/latest/core/engines.html)

* [What is virtualenv](https://pythontips.com/2013/07/30/what-is-virtualenv/)
* [Virtual environments in python](https://docs.python-guide.org/dev/virtualenvs/)

* [How i can get a list of locally installed python modules](https://stackoverflow.com/questions/739993/how-can-i-get-a-list-of-locally-installed-python-modules)
* [How to deploying python flask on apache2 ubuntu 16.04](https://www.youtube.com/watch?v=wq0saslschw)

* [How to find apache http server log files](https://blog.codeasite.com/how-do-i-find-apache-http-server-log-files)

* [How to fix http error code 500](https://www.ionos.com/community/server-cloud-infrastructure/apache/how-to-fix-http-error-code-500-internal-server-error/)

* [curl usage](https://gist.github.com/subfuzion/08c5d85437d5d4f00e58)

* [How to fix: “UnicodeDecodeError: 'ascii' codec can't decode byte”
](https://stackoverflow.com/questions/21129020/) 
* [How to fix unicode error ascii codec can't decode byte](how-to-fix-unicodedecodeerror-ascii-codec-cant-decode-byte)

* [Unicode strings type ](https://python-para-impacientes.blogspot.com/2014/07/tipos-de-cadenas-unicode-byte-y.html)









