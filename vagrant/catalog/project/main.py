from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Item

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///itemscatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def getUserID(email):
    '''Gets the user ID associated to the user's email'''
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    '''Gets all info about a user from their ID'''
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    '''If a user has not visited the site before, creates them in the database'''
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


@app.route('/login')
def showLogin():
    '''Displays the login page'''
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    '''Connects to the user's Google account'''
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps(
            'Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
           access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps(
            "Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps(
            "Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check to see if user is already logged in
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    login_session['provider'] = 'google'
    login_session['username'] = data["name"]
    login_session['picture'] = data["picture"]
    login_session['email'] = data["email"]

    # See if user ecists, if not make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    '''Disconnects from the user's Google account'''
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        flash("You were not logged in")
    # Execute HTTP GET request to revoke current token.
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's session.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("You have successfully been logged out.")
    return redirect(url_for('showCatalog'))


@app.route('/')
@app.route('/catalog')
def showCatalog():
    '''Shows the item catalog'''
    items = session.query(Item).all()
    if 'username' not in login_session:
        return render_template('publicCatalog.html', items=items)
    else:
        return render_template('catalog.html', items=items)

@app.route('/catalog/new', methods=['GET', 'POST'])
def newItem():
    '''Creates a new item in the database'''
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Item(name=request.form['name'],
            description=request.form['description'],
            price=request.form['price'],
            user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash("New item created!")
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newItem.html')

@app.route('/catalog/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(item_id):
    '''Edits an item in the database'''
    if 'username' not in login_session:
        return redirect('/login')
    itemToEdit = session.query(
        Item).filter_by(id=item_id).one()
    if itemToEdit.user_id != login_session['user_id']:
        flash("You are not authorized to edit this item. Please create your own item in order to edit.")
        return redirect(url_for('showCatalog'))
    if request.method == 'POST':
        if request.form['name']:
            itemToEdit.name = request.form['name']
        if request.form['description']:
            itemToEdit.description = request.form['description']
        if request.form['price']:
            itemToEdit.price = request.form['price']
        session.add(itemToEdit)
        session.commit()
        flash("Item updated!")
        return redirect(url_for('showCatalog'))
    else:
        return render_template('editItem.html', item=itemToEdit)


@app.route('/catalog/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(item_id):
    '''Deletes an item in a database'''
    if 'username' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(
        Item).filter_by(id=item_id).one()
    if itemToDelete.user_id != login_session['user_id']:
        flash("You are not authorized to delete this item. Please create your own item in order to delete.")
        return redirect(url_for('showCatalog'))
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash("Item deleted!")
        return redirect(url_for('showCatalog'))
    return render_template('deleteItem.html', item=itemToDelete)


@app.route('/catalog/JSON')
def catalogJSON():
    '''Creates a JSON object of all items in the database'''
    items = session.query(Item).all()
    return jsonify(Items=[i.serialize for i in items])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
