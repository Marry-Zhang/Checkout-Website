from flask import Flask
import sqlite3
from flask import Flask, flash, redirect, render_template, request, url_for, g, session
import os
 

app = Flask(__name__)


# the database file we are going to communicate with
DATABASE = './assignment1.db'
# connects to the database
def get_db():
    # if there is a database, use it
    db = getattr(g, '_database', None)
    if db is None:
        # otherwise, create a database to use
        db = g._database = sqlite3.connect(DATABASE)
    return db

# converts the tuples from get_db() into dictionaries
# (don't worry if you don't understand this code)
def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

# given a query, executes and returns the result
# (don't worry if you don't understand this code)
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def change_db(query, args=(), one=False):
    db = get_db()
    cur = db.cursor()
    cur.execute(query, args)
    db.commit()
    cur.close()
    db.close()

# home page
@app.route('/', methods=['GET', 'POST'])
def shopping_cart():
    # get database
    db = get_db()
    db.row_factory = make_dicts

    # make a new cursor from the database connection
    cur = db.cursor()

    items = []
    items_in_cart = []
    # send the list of items to the user to select
    for item in query_db('SELECT * FROM item'):
        items.append(item)

    if request.method == 'POST':
        # get post body
        quantity = request.form.get('quantity')
        item_name = request.form['item-selection']
        tax_rate = query_db('SELECT tax_rate FROM item where item_name = ?', [item_name], one=True)
        item_price = query_db('SELECT item_price FROM item where item_name = ?', [item_name], one=True)
        discount = request.form.get('discount')

        # if item not in cart, write item and quantity into database
        if (query_db('select * from cart where item_name = ? AND discount = ?', [item_name, discount], one=True) == None):
            cur.execute('insert into cart (item_name, cart_quantity, tax_rate, item_price, discount) values (?, ?, ?, ?, ?)', 
            [item_name, quantity, tax_rate.get('tax_rate'),item_price.get('item_price'), discount])
        else:
            original_quantity = query_db('SELECT cart_quantity FROM cart where item_name = ?', [item_name], one=True)
            new_quantity = int(quantity) + int(original_quantity.get('cart_quantity'))
            cur.execute('UPDATE cart SET cart_quantity = ? WHERE item_name = ? AND discount = ?',[new_quantity, item_name, discount])

        # commit the change to the database
        db.commit()
        # close the cursor
        cur.close()
    
    # everything in cart
    for item_in_cart in query_db('SELECT * FROM cart'):
        items_in_cart.append(item_in_cart)

    # close database
    db.close()
    return render_template('shopping_cart.html',items = items, items_in_cart=items_in_cart)

@app.route('/delete')
def delete():
    name = request.args.get('name')
    disc = request.args.get('disc')
    
    change_db('DELETE FROM cart WHERE item_name = ? and discount = ?',[name, disc])
    return redirect(url_for('shopping_cart'))

   
@app.route("/checkout", methods=['GET','POST'])
def checkout():

    if request.method == 'POST':
        change_db("DELETE FROM cart")
        return redirect(url_for('shopping_cart'))
        
    # get database
    db = get_db()
    db.row_factory = make_dicts

    # make a new cursor from the database connection
    cur = db.cursor()

    # read cart data
    cart = query_db("SELECT * FROM cart")
    
    # calculate subtotal, total, etc.
    total_discount = 0
    sub_price = 0
    tax = 0
    total_price = 0
        
    for item in cart:
        sub_price += item['item_price'] * item['cart_quantity']
        tax += item['item_price'] * (1 - item['discount'] )* item['tax_rate'] * item['cart_quantity']
        total_discount += item['item_price'] * item['discount'] * item['cart_quantity']
    
    # round to 2 decimals
    rounded_sub = round(sub_price,2)
    rounded_tax = round(tax, 2)
    rounded_disc = round(total_discount, 2)

    total_price = round((sub_price + tax - total_discount), 2)
    
    
    return render_template("checkout.html", cart = cart, sub_price = rounded_sub, tax = rounded_tax, 
                                total_price = total_price, discount = rounded_disc)


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8888,debug=True)
