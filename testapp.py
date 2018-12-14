from flask import Flask

app = Flask(__name__)

# @app.route('/catalog')
@app.route('/')
def test():
    return "It works !!"

if __name__ =='__main_':
    app.secret_key = 'super_secret_key'
    app.run()


