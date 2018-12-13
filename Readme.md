# Linux Server Configuration

Item Catalog App is an application that provides a list of items within a variety of categories as well as provide a user registration and authentication system provided by third-party authentication & authorization service (Google). Registered users will have the ability to post, edit and delete their own items/categories. In the same way, by implementing a Local System Permission, an user can only edit or delete an item/category if it has been created by him. Moreover, this app has three JSON endpoints that serves the same information as displayed in the HTML endpoints for an arbitrary item in the catalog. 

ip Address: 35.247.193.231 

_Note_ you need to set up your External Ip address as static.
* Go to he main menu on Google Cloud Platform, select VPC Network
* You need to choose External IP addresses, and on the type section change from ephemeral to static and save.



## Get your server
* Start a new Ubuntu Linux server instance on Amazon Lightsail. There are full details on setting up your Lightsail instance on the next page.
*  Follow the instructions provided to SSH into your server.

### Create Firewall rules for our VM instance
* For that, you have to create a Firewall rule. 
* Go to the main menu on the left-upper side and choose VPC Network.
* Select Firewall rules, and create a Firewall rule.
* You have only to provide a name,_custom-ssh_, specify a port (tcp/2200) and on the Source Ip ranges put 0.0.0.0/0. The remaining fields should not be changed.
* Then, Hit the Create botton. 
* For the incomming requests from web, we need to follow the same previous step, but on the port specification we put tcp/80.
* For the ntp requests we will do the same, specifying udp/123.

## Secure your server.
* Update all currentlyss installed packaptages.
* sudo apt-get updatde
* sudo apt-get upgrade
* Change the SSH port from 22 to 2200. Make sure to configure the Google Cloud Platform  firewall to allow it.

* sudo nano /etc/ssh/sshd_config
* Change port 22 to 2200, save and exit 
* Restart the sshd service by running: sudo server sshd restart
* Check the sshd service status: sudo service sshd status
* Configure the Uncomplicated Firewall (UFW) to only allow incoming connections for SSH (port 2200), HTTP (port 80), and NTP (port 123).
* Checking the ufw current status: sudo ufw status
* Deny incomming requests: sudo ufw default deny incoming
* Allow outgoing requests: sudo ufw default allow outgoing
* Configure ssh service: sudo ufw allow 2200/tcp
* Configure HTTP: sudo ufw allow www
* Configure NTP: sudo ufw allow ntp
* Enable ufw: sudo ufw enable
* Verify the ufw status: sudo ufw status
[coment]: <![](ufw_status.png)>

<img src="ufw_status.png" alt="drawing" width="500" height="200" />



_Warning: When changing the SSH port, make sure that the firewall is open for port 2200 first, so that you don't lock yourself out of the server. When you change the SSH port, the Lightsail instance will no longer be accessible through the web app 'Connect using SSH' button. The button assumes the default port is being used. There are instructions on the same page for connecting from your terminal to the instance. Connect using those instructions and then follow the rest of the steps._

*Note:* When you set up OAuth for your application, you will need a DNS name that refers to your instance's IP address. You can use the xip.io service to get one; this is a public service offered for free by Basecamp. For instance, the DNS name 54.84.49.254.xip.io refers to the server above.

Explore the other tabs of this user interface to find the Lightsail firewall and other settings. You'll need to configure the Lightsail firewall as one step of the project.

When you SSH in, you'll be logged as the ubuntu user. When you want to execute commands as root, you'll need to use the sudo command to do it.

### Forcing Key based authentication
We will force all user to be only able to log in using key pair.
* On a terminal logged as ubuntu user: sudo nano /etc/ssh/sshd_config
* Change Password Authentication to *no*, save and exit.
* Restart the ssh service: sudo service ssh restart 

## Give grader access.
In order for your project to be reviewed, the grader needs to be able to log in to your server.

* Create a new user account named *grader*: sudo adduser grader
* Choose a password and full name (grader)

* Give grader the permission to sudo: sudo cp /etc/sudoers.d/google_sudoers /etc/sudoers.d/grader
* sudo nano /etc/sudoers.d/grader save and exit
After that, we will now be able to use sudo command as grader user.
_Note: You make sure that sshd_config file require a password authentication:
PasswordAuthentication yes

* Create an SSH key pair for grader using the ssh-keygen tool.
* On the local machine create a directory called .ssh.
* On your terminal run: ssh-keygen and change last part of the suggeste name by grader.
* Log in on another terminal as grader: ssh grader@35.247.205.222 -p 2200
* mkdir .ssh
* touch .ssh/authorized_keys
*  Back on your local machine: cat .ssh/grader.pub
*  Back on the server as grader user paste the .pub file and save it: nano .ssh/authorized_keys
*  Setup specific file permission:
   *  chmod 700 .ssh (Owner can only write, read and exec)
   *  chmod 644 .ssh/authorized_keys (Owner can write and read while the other users can only write)
* Finally on the other terminal we need to log in as grader user:
  * ssh grader@35.247.193.231  -p 2200 -i ~/.ssh/grader

## Disable SSH login as Root user
* On your terminal as ubuntu user we need to edit sshd_config file: sudo nano /etc/ssh/sshd_config
* In the authentication section change: PermitRootLogin yes to no, save and exit
* Finally, restart ssh service: sudo service ssh restart

## Prepare to deploy your project.

* Configure the local timezone to UTC: On your terminal as ubuntu user, sudo timedatectl set-timezone UTC

* Install and configure Apache to serve a Python mod_wsgi application: 
 * sudo apt-get install apache2
 * sudo apt-get install libapache2-mod-wsgi-py
 * (3 (My project was built with Python3))
 
 
 

If you are running Debian or Ubuntu Linux with Apache 2.4 system packages, regardless of which Apache MPM is being used, you would need both:

apache2
apache2-dev



sudo apt-get install python-pip

(LoadModule wsgi_module "/home/lmosc/.local/lib/python2.7/site-packages/mod_wsgi/server/mod_wsgi-py27.so"
WSGIPythonHome "/usr")



* Install and configure PostgreSQL:
* sudo apt-get install postgresql
* Change the postgres user’s Linux password: sudo passwd postgres
* Issue the following commands to set a password for the postgres database user. Be sure to replace newpassword with a strong password and keep it in a secure place:
su - postgres
psql -d template1 -c   "ALTER USER postgres WITH PASSWORD 'newpassword';"

Note that this user is distinct from the postgres Linux user. The Linux user is used to access the database, and the PostgreSQL user is used to perform administrative tasks on the databases.

 * Do not allow remote connections 
 We can double check that no remote connections are allowed by looking in the host based authentication file:
 sudo nano /etc/postgresql/9.5/main/pg_hba.conf

local   all             all                                     md5
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5


 * Create a new database user named catalog that has limited permissions to your catalog application database.  
 * CREATE USER catalog WITH CREATEDB,LOGIN
 * Set password: \password catalog
 * psql -h localhost -U catalog *mydatabase*



dialect+driver://username:password@host:port/database
engine = create_engine('postgresql://scott:tiger@localhost/mydatabase')

 
*  Install git: As ubuntu user, sudo apt-get install git
## Deploy the Item Catalog project.
* Install pip: sudo apt-get install python-pip
 * Install virtualenv: pip install virtualenv
 
* Create the configuration file for the catalog website: sudo cp /etc/apache2/sites-available/000-default.conf catalog.conf
'''
 ServerName www.example.com

 WSGIScriptAlias / /var/www/catalog-linux-server/catalogapp.wsgi
 <Directory /var/www/catalog-linux-server>
 Order allow,deny
 Allow from all
 </Directory>

'''
* Clone and setup your Item Catalog project from the Github repository you created earlier in this Nanodegree program.
* cd /var/www
* clone the Item catalog project: sudo git clone https://github.com/lmoscoted/catalog-linux-server.git

* (Inside project directory create a virtual environment) sudo virtualenv env
 * Activate environment: source env/bin/activate
 * _Install all needed modules_ inside the environment
 * First we have to get all modules from our Linux VM where ran our project. On the terminal: pip freeze > requirements.txt
 * Now inside the current directory project: pip install -r requirements.txt



* Set it up in your server so that it functions correctly when visiting your server’s IP address in a browser. Make sure that your *.git* directory is not publicly accessible via a browser! 
    * Create WSGI file to link the application app: sudo nano /var/www/catalog-linux-server/catalogapp.wsgi
    '''
    import sys 
    sys.insert(0,"/var/www/catalog-linux-server")
    from init import app as application
    '''







# How to run it?
 
Firstly, you need to be logged on the linux session by running _vagrant up_ and _vagrant ssh_ inside the vagrant subdirectory on your terminal. Then, You need to change directory to the catalog subdirectory in your Linux VM. You can use either the DB file that I used for this project or you can create a new database with your own data. If you choose to create a new one, you need to edit only the rows from the csv files. Then, inside the catalog folder, you need to run `python database_setup.py`to create the database model for this project. Later, by running `python lotsofcatalogitems.py`, you will populate the database with all data. Finally, you need to run the next command:


```
python application.py
```

After that step, you will be able to access to the website project by typing on your web browser whether _localhost:5000/catalog_ or _localhost:5000_. 


# References
* [How do I change my timezone to UTC/GMT?
](https://askubuntu.com/questions/138423/how-do-i-change-my-timezone-to-utc-gmt).

* [Cambiar el puerto de SSH para su servidor Linux
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
).
https://modwsgi.readthedocs.io/en/develop/
https://pypi.org/project/mod_wsgi/
https://www.rosehosting.com/blog/how-to-install-pip-on-ubuntu-16-04/
https://groups.google.com/forum/#!topic/modwsgi/YMt8VyrIvqA
https://www.cyberciti.biz/faq/star-stop-restart-apache2-webserver/
http://www.learnexia.com/?p=327

https://stackoverflow.com/questions/44914961/install-mod-wsgi-on-ubuntu-with-python-3-6-apache-2-4-and-django-1-11

https://www.linode.com/docs/databases/postgresql/how-to-install-postgresql-on-ubuntu-16-04/

https://www.digitalocean.com/community/tutorials/how-to-secure-postgresql-on-an-ubuntu-vps

https://linuxhint.com/postgresql_python/

https://wiki.postgresql.org/wiki/Psycopg2_Tutorial

https://docs.sqlalchemy.org/en/latest/core/engines.html

https://pythontips.com/2013/07/30/what-is-virtualenv/
https://docs.python-guide.org/dev/virtualenvs/

https://stackoverflow.com/questions/739993/how-can-i-get-a-list-of-locally-installed-python-modules
https://www.youtube.com/watch?v=wq0saslschw








