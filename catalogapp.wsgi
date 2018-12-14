# import sys 

# sys.path.insert(0, "/var/www/catalog-linux-server")

# from testapp import app as application

from flask import Flask

app = Flask(__name__)

@app.route('/')
def test():
    return "It works !!"

if __name__ =='__main__':
    app.secret_key = 'super_secret_key'
    app.run()

