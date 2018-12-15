from flask import Flask
from flask import render_template
from flask import redirect
from flask import url_for
from flask import request
from flask import flash
from flask import jsonify
from flask import abort
from flask import make_response
from flask import session as login_session
import string
import random
import requests
import json
import httplib2
import psycopg2

from sqlalchemy import create_engine
from sqlalchemy import desc
from sqlalchemy import DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql import func
import datetime
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import *
from oauth2client.client import FlowExchangeError

from database_setup import Base, Category, Item, User

app = Flask(__name__)
# print("OK")
# Google Client ID
CLIENT_ID = json.loads(
    open('/var/www/catalog-linux-server/client_secrets.json', 'r').read())['web']['client_id']
print(CLIENT_ID)
# engine = create_engine(
  #  'postgresql://catalog:2018catitem@localhost/catalogitems',
  #  connect_args={
  #      'check_same_thread': False},
  #  poolclass=StaticPool)  # Which DB python will communicate with
engine = create_engine(
    'postgresql://catalog:2018catitem@localhost/catalogitems',
    poolclass=StaticPool) 

Base.metadata.bind = engine  # Makes connection between class and tables
# print(engine)
#--------------------------------------------------------------------------
# try:
#     conn = psycopg2.connect("dbname='catalogitems' user='catalog'host='localhost' password='2018catitem'")
#     print("connected to the database")
# except:
#     print("unable to connect to the database")


#---------------------------------------------------------------------------

# print("OK")

# Link of communication between our code execution
DBSession = sessionmaker(bind=engine)
session = DBSession()  # interefaz that allow to create DB operations
# print("OK")


# Create random string for the Google Code and CSFR token
def some_random_string():
    random_string = ''.join(
        random.choice(
            string.ascii_uppercase +
            string.digits) for x in xrange(32))
    return random_string

# print("OK")

state = some_random_string()


# CFSR Protection
@app.before_request
def csrf_protect():
    # Only aply for all endpoints except Login endpoint for Google
    if request.method == "POST" and (request.endpoint != 'gconnect'):
        token = state
        # Forbidden action if there is not code or it is fake
        if not token or token != request.form.get('_csrf_token'):
            abort(403)

# Endpint for the login
# print("OK")


@app.route('/login', endpoint='showLogin')
def showLogin():

    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Handle the code sent back from the callback method
# Enpoint for the google login
@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    print("This is the code: "%code)
    try:
        # Upgrade the authorized code into a credentials object
        oauth_flow = flow_from_clientsecrets('/var/www/catalog-linux-server/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
        print(oauth_flow)
        print(credentials)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code. '), 401)
        response.headers['Content-Type'] = 'application/json'
        print('Failed to upgrade the authorization code. ')
        return response
    print("RESPONSE")    
    print(response)    
    # Check that the access token is valid.
    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
        access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    print("Result is %s" % result)
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 50)
        response.headers['Content-Type'] = 'application/json'
    # Verify that the access token is used for intended use
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's ."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check to see if the user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps("Current user is already connected. "), 200)
        response.headers['Content-Type'] = 'application/json'

    # Store the access token in the session for later use.
    login_session['provider'] = 'google'
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = json.loads(answer.text)
    login_session['username'] = data["name"]
    login_session['picture'] = data["picture"]
    login_session['email'] = data['email']

    # See if user exists, if it does not make a new one
    if getUserID(login_session['email']) is None:
        user_id = createUser(login_session)
        login_session['user_id'] = user_id

    login_session['user_id'] = getUserID(login_session['email'])

    output = 'Logged'

    flash("You are now logged in as %s " % login_session['username'])
    return output


# DISCONNECT - Revoke a current user's token and reset their
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Execute HTTP GET request to revoke current token
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid
        response = make_response(
            json.dumps(
                'Failed to revoke token for given user.',
                400))
        response.headers['Content-Type'] = 'application/json'
        return response


# DISCONNECT function for any provider
@app.route('/disconnect')
def disconnect():

    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']

        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have Successfully been logged out. ")
        return redirect(url_for('showCategories'))
    else:
        flash("You are not logged in to begin with!")
        redirect(url_for('showCategories'))


# Making an API Endpoint (GET Request)
@app.route('/catalog/JSON')
def categoriesJSON():
    # print("Test3")
    category_list = session.query(Category)
    # print(iter(category_list))
    # print(type(category_list))
    # print(category_list)

    if not category_list:
        error = [{'Error Message': 'There are not available categories '}]
        return jsonify({'Categories': error})

    return jsonify(Categories=[[i.serialize for i in category_list]])

# API Endpoint for all items from a category


@app.route('/catalog/<string:category_name>/JSON')
def categoryJSON(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    if ((not category) or (not items)):
        error = [{'Error Message': 'There are not available items '}]
        return jsonify({'Items': error})

    return jsonify(Items=[i.serialize for i in items])

# API Endpoint for an arbitrary Item


@app.route('/catalog/<string:category_name>/<string:item_name>/JSON')
def categoryItemsJSON(category_name, item_name):
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter(
        (Item.name == item_name) & (
            Item.category_id == category.id)).one()
    if ((not category) or (not item)):
        error = [{'Error Message': 'Item not found!'}]
        return jsonify({'Item': error})
    return jsonify(Item=item.serialize)

# Main web page

# print("OK")

@app.route('/')
@app.route('/catalog', methods=['GET', 'POST'])
def showCategories():
    # print("OK Main Page")

    categories = session.query(Category).order_by(Category.name)
    # items = session.query(Item).order_by("Item.date_update desc")
    items = session.query(Item).order_by(desc(Item.date_update))
    latest_items = items.limit(10)
    # print(categories)
    category_item = []
    # print("OK2 query Login")
    # Getting the category names for the latest items
    for i in latest_items:
        # print("PRINT 1 FOR")
        cat_name = session.query(Category).filter_by(id=i.category_id).one()
        # print("PRINT 2 FOR")
        category_item.append(cat_name.name)
        # print(i.name)
    # print("OK2 for query")
    # Run public template for unregistered users
    if 'username' not in login_session:
        # print("OK if ")
        return render_template(
            'publiccategories.html',
            categories=categories,
            login_session=login_session,
            latest_items=latest_items,
            category_item=category_item)
    else:
        # print("OK else")
        return render_template(
            'categories.html',
            categories=categories,
            login_session=login_session,
            latest_items=latest_items,
            category_item=category_item)

# Endpoint for a new category


@app.route('/catalog/new', methods=['GET', 'POST'])
def newCategory():
    # Login required for creating a new category
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).order_by(Category.name)

    if request.method == 'POST':
        category_new = Category(
            name=request.form['name'], user_id=getUserID(
                login_session['email']))
        session.add(category_new)
        session.commit()
        flash('Category %s created!' % category_new.name)
        return render_template(
            'newItem.html',
            category_name=category_new.name,
            categories=categories, state=state)
    else:
        return render_template('newcategory.html', categories=categories,
                               state=state)

# Endpoint for creating a category


@app.route('/catalog/<string:category_name>/edit', methods=['GET', 'POST'])
def editCategory(category_name):
    # Login required for this action
    if 'username' not in login_session:
        return redirect('/login')

    category_edit = session.query(Category).filter_by(name=category_name).one()
    categories = session.query(Category).order_by(Category.name)
    # Only category owner can edit categories
    if category_edit.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are no authorized \
                to edit this category. Please create a new category in order \
                to edit');location.href='/catalog';}</script><body \
                onload='myFunction()''>"

    if request.method == 'POST':
        if request.form['name']:
            category_edit.name = request.form['name']
            session.add(category_edit)
            session.commit()
        flash('Category %s successfully edited!' % category_edit.name)
        return redirect(url_for('showCategories'))
    else:
        return render_template(
            'editcategory.html',
            category_name=category_edit.name,
            categories=categories, state=state)

# Endpoint for deleting categories


@app.route('/catalog/<string:category_name>/delete', methods=['GET', 'POST'])
def deleteCategory(category_name):
    # Login required for this action
    if 'username' not in login_session:
        return redirect('/login')

    category_dele = session.query(Category).filter_by(name=category_name).one()
    items_dele = session.query(Item).filter_by(
        category_id=category_dele.id).all()
    categories = session.query(Category).order_by(Category.name)
    # Only category owner can edit categories
    if category_dele.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are no \
                authorized to delete this category. Please access \
                to your own category in order to delete');\
                location.href='/catalog';}</script><body onload=\
                'myFunction()''>"

    if request.method == 'POST':

        session.delete(category_dele)
        # Delete all items from the deleted category
        for i in items_dele:
            session.delete(i)
        session.commit()
        flash('Categoria %s successfully deleted!' % category_dele.name)
        return redirect(url_for('showCategories'))
    else:
        return render_template(
            'deletecategory.html',
            category_name=category_dele.name,
            categories=categories, state=state)

# Endpoint for showing the items from a category


@app.route('/catalog/<string:category_name>/items')
def showItems(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    items_number = len(items)
    categories = session.query(Category).order_by(Category.name)
    # If there are not items, redirect to the new item endpoint
    if not items:
        return "<script>function myFunction() {alert('This category \
                do not have items yet.Please add new items for this \
                category');location.href='/catalog/%s/new';}</script>\
                <body onload='myFunction()''>" % category_name
    # Only registered users can edit, create or delete items
    if 'username' not in login_session:
        return render_template(
            'publicitems.html',
            category_name=category.name,
            items=items,
            categories=categories,
            items_number=items_number)

    else:
        return render_template(
            'items.html',
            category_name=category.name,
            items=items,
            categories=categories,
            items_number=items_number,
            state=state)

# Endpoint for creating a new item


@app.route('/catalog/<string:category_name>/new', methods=['GET', 'POST'])
def newItem(category_name):
    # Login required for this action
    if 'username' not in login_session:
        return redirect('/login')

    category = session.query(Category).filter_by(name=category_name).one()
    categories = session.query(Category).order_by(Category.name)

    # Create a new item for POS requests
    if request.method == 'POST':
        item_new = Item(
            name=request.form['name'],
            description=request.form['description'],
            price=request.form['price'],
            category_id=category.id,
            user_id=getUserID(
                login_session['email']))
        session.add(item_new)
        session.commit()
        flash('Item %s Created!' % item_new.name)
        return redirect(
            url_for(
                'showItems',
                category_name=category.name,
                categories=categories, state=state))
    else:
        return render_template(
            'newItem.html',
            category_name=category.name,
            categories=categories,
            state=state)


# Endpoint for editing a category
@app.route('/catalog/<string:category_name>/<string:item_name>/edit',
           methods=['GET', 'POST'])
def editItem(category_name, item_name):
    # Login required for this action
    if 'username' not in login_session:
        return redirect('/login')

    categories = session.query(Category).order_by(Category.name)
    category = session.query(Category).filter_by(name=category_name).one()
    # Edit item from the desired category
    item_edited = session.query(Item).filter((Item.name == item_name) &
                                             (Item.category_id ==
                                              category.id)).one()
    # Creator item can only edit it
    if item_edited.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are no \
                authorized to edit this item.');location.href=\
                '/catalog/%s/items';}</script><body onload=\
                'myFunction()''>" % category_name

    if request.method == 'POST':
        if request.form.get('name'):
            item_edited.name = request.form['name']
            # Update date for the latest items
            item_edited.date_update = func.now()

        if request.form.get('description'):
            item_edited.description = request.form['description']
            # Update date for the latest items
            item_edited.date_update = func.now()

        if request.form.get('price'):
            item_edited.price = request.form['price']
            # Update date for the latest items
            item_edited.date_update = func.now()

        if request.form.get('picture'):
            item_edited.picture = request.form['picture']
            # Update date for the latest items
            item_edited.date_update = func.now()
        # Update category only if it is updated by the user
        if category_name != categories[int(request.form.get('category'))]:
            item_edited.category = categories[int(
                request.form.get('category'))]
            # Update date for the latest items
            item_edited.date_update = func.now()

        session.add(item_edited)
        session.commit()
        flash('Item %s Edited!' % item_edited.name)
        return redirect(
            url_for(
                'showItems',
                category_name=category.name,
                categories=categories))
    else:
        return render_template(
            'edititem.html',
            category_name=category.name,
            item=item_edited,
            categories=categories,
            state=state)

# Endpoint for deleting an item


@app.route(
    '/catalog/<string:category_name>/<string:item_name>/delete',
    methods=['GET', 'POST'])
def deleteItem(category_name, item_name):
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).order_by(Category.name)
    category = session.query(Category).filter_by(name=category_name).one()
    # Delete the item from the desired category
    item_deleted = session.query(Item).filter(
        (Item.name == item_name) & (
            Item.category_id == category.id)).one()
    # Creator item can only delete it
    if item_deleted.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are no \
                authorized to delete this item.');location.href=\
                '/catalog/%s/items';}</script><body \
                onload='myFunction()''>" % category_name

    if request.method == 'POST':
        session.delete(item_deleted)
        session.commit()
        flash('Item %s successfully deleted!' % item_deleted.name)

        return redirect(
            url_for(
                'showItems',
                category_name=category.name,
                categories=categories))

    else:
        return render_template(
            'deleteitem.html',
            category_name=category.name,
            item=item_deleted,
            categories=categories, state=state)

# Endpoint for showing item information


@app.route('/catalog/<string:category_name>/<string:item_name>')
def infoItem(category_name, item_name):
    category = session.query(Category).filter_by(name=category_name).one()
    # Select the item from the desired category
    item = session.query(Item).filter(
        (Item.name == item_name) & (
            Item.category_id == category.id)).one()
    categories = session.query(Category).order_by(Category.name)
    # Render public template for unregistered users
    if 'username' not in login_session:
        return render_template(
            'publicitem.html',
            category_name=category_name,
            item=item,
            categories=categories)
    else:
        return render_template(
            'item.html',
            category_name=category_name,
            item=item,
            categories=categories)


# Getting user information
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except BaseException:
        return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0')
    # app.run()
