from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/restaurant')
def showRestaurant():
    restaurants = session.query(Restaurant).all()
    return render_template('restaurants.html', restaurants=restaurants)


@app.route('/restaurant/new', methods=['GET', 'POST'])
def newRestaurant():
    if request.method == 'POST':
        newRestaurant = Restaurant(name=request.form[
            'name'])
        session.add(newRestaurant)
        session.commit()
        flash("New restaurant created!")
        return redirect(url_for('showRestaurant'))
    else:
        return render_template('newRestaurant.html')


@app.route('/restaurant/<int:restaurant_id>/edit', methods=['GET', 'POST'])
def editRestaurant(restaurant_id):
    restaurantToEdit = session.query(
        Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        if request.form['name']:
            restaurantToEdit.name = request.form['name']
        session.add(restaurantToEdit)
        session.commit()
        flash("Restaurant updated!")
        return redirect(url_for('showRestaurant'))
    else:
        return render_template('editRestaurant.html', restaurant=restaurantToEdit)


@app.route('/restaurant/<int:restaurant_id>/delete', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    restaurantToDelete = session.query(
        Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        session.delete(restaurantToDelete)
        session.commit()
        flash("Restaurant deleted!")
        return redirect(url_for('showRestaurant'))
    return render_template('deleteRestaurant.html', restaurant=restaurantToDelete)


@app.route('/restaurant/<int:restaurant_id>')
@app.route('/restaurant/<int:restaurant_id>/menu')
def showMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant.id).all()
    return render_template('menu.html', restaurant=restaurant, items=items)


@app.route('/restaurant/<int:restaurant_id>/menu/new', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    if request.method == 'POST':
        newItem = MenuItem(name=request.form[
                           'name'], restaurant_id=restaurant_id)
        session.add(newItem)
        session.commit()
        flash("New menu item created!")
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template('newMenuItem.html', restaurant_id=restaurant_id)


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    itemToEdit = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        if request.form['name']:
            itemToEdit.name = request.form['name']
        session.add(itemToEdit)
        session.commit()
        flash("Menu item updated!")
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template('editMenuItem.html', restaurant=restaurant, item=itemToEdit)


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    itemToDelete = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash("Menu item deleted!")
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template('deleteMenuItem.html', restaurant_id=restaurant_id, menu_id=menu_id, item=itemToDelete)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
