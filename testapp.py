from flask import Flask

app = Flask(__name__)

@app.route('/catalog')
@app.route('/')
def test():
	return "It works !!"

if __name__ =='__main__':
	app.secret_key = 'super_secret_key'
    app.run(host='www.35.247.193.231.xip.io', port=80)

