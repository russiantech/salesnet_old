from flask import redirect, render_template, request, jsonify, make_response, Blueprint, url_for, flash, session
from flask_login import current_user, login_required

from  sqlalchemy.sql.expression import func, select
from sqlalchemy import exc

from web.models import (
    db, User, Listing, Cate, Order
)

from web.account.forms import OrderForm, payOptionChoice

from web.utils.slug import slugify
from web.utils.cate import categ

endpoint = Blueprint('endpoint', __name__)

# function which print all the values of nested dictionary
def printNested(nesteddict):
    # Traverse the dictionary
    for key, value in nesteddict.items():
        # If the value is of the dictionary type, then print
        # all of the keys and values within the nested dictionary.
        if isinstance(value, dict):
            for pair in printNested(value):
                yield (key, *pair)
        else:
            yield(key, value)

# given nested_dictionary
nesteddict = {
    'hello':    {'www': 100, 'yyy': 'Helloworld'},
    'this':    {'www': 'vikram', 'age': 20, 'DOB': 'FEB'},
    'BTechGeeks':    {'PLACE': 'HYDERABAD', 'PINCODE': 500000,
                      'PYTHON': {'FUNCTIONS': 'Built in', 'year': 1999}},
}
# passing nested dictionary to printNested Function using loop
for pair in printNested(nesteddict):
    #print(pair)
    pass

@endpoint.route('/<r>/cate', methods=['POST', 'GET']) # -> basket, merged with checkout in same route
def cate(r=None):

    try:
        cate = Cate.query.order_by(Cate.id).all()
        cate = [ {'id': c.id, 'parent': c.parent, 'name': c.name, 'lev': c.lev } for c in cate ]

        cat = { 
        #0: { 'id': 0, 'parent': 0, 'name': "Root node", 'sub': [] }
        }

        for c in cate:
            cat.setdefault(c['parent'], { 'sub': [] })
            cat.setdefault(c['id'], { 'sub': [] })
            cat[c['id']].update(c)
            cat[c['parent']]['sub'].append(cat[c['id']])

        #return cat
        return jsonify(cate)
    
    except Exception as e:
        print(e)
        db.session.rollback()
        flash(f"Oops an error occured, pls try again-> ", "primary")
        return jsonify( { 
            'response': f'ooops!!!, an error occured, kindly try again({e})',
            'flash':'alert-primary' })


@endpoint.route('/ordering', methods=['POST', 'GET']) # -> basket, merged with checkout in same route
def place_order():
    
    form = OrderForm()

    form.order_amt.data = 500

    cart = session.get('basket', {})
    
    try:

        if len(cart) < 1 :
            return jsonify( { 
                'response': f'Your Shopping Basket Is Empty, Browse Salesnet & Add Listing(s) To Contine',
                'flash':'alert-primary',
                'link': f'{url_for("main.index")}',
                #'receipt': f'{url_for("cart.ordered", o_id=session["recent_order"])}'
                             })
        
        if form.validate_on_submit():

            ordered = Order( 
                
                usr_id = current_user.id \
                    if current_user.is_authenticated else 0, #so that even-if you're not logged in, you can still place orders
                
                order_item = cart, #bcos from up, if no carted-item, it won't run

                email=form.email.data, 
                phone=form.phone.data,
                name=form.name.data, 
                adrs=form.adrs.data, 
                country=form.country.data, 
                state=form.state.data, 
                zipcode=form.zipcode.data, 
                #order_amt=form.order_amt.data, 
                pment_option=form.pment_option.data, 

                )

            db.session.add(ordered)
            db.session.commit()
            db.session.flush()
            
            db.session.refresh(ordered) #refresh so-i-can-get-the-last/new-insert-id

            pay = payOptionCheck( form.pment_option.data, amt=int(float(form.order_amt.data)) )

            session['recent_order'] = ordered.order_id #save-order-id in session so it can be retrieved from exception block incase or of IntegrityError
            session['pay_link'] = pay #save-payment-link in session so it can be retrieved from exception block incase for the front-end

            #if len(session['basket']) > 0 :
            del session['basket']  #remove it from cart if saved to db as order
            
            #return pay if pay and ordered.order_id else redirect(url_for('cart.ordered', o_id=ordered.order_id)) 

            if pay and ordered.order_id:
                return jsonify( { 
                'response': f'Success!!!, Your Order Was Placed, Contine To {which_option(ordered.pment_option)} ',
                'flash':'alert-success',
                'link': f'{pay}',
                 'receipt': f'{url_for("cart.ordered", o_id=ordered.order_id)}' })
            
        flash(f'{form.errors}', 'info')
        return jsonify( { 
                'response': f'{form.errors}',
                'flash':'alert-primary'
                             }) 
        
    except exc.IntegrityError as e:
            print(e)
            recent_order = session.get("recent_order", False )
            pay_link = session.get("pay_link", False )
                                  
            db.session.rollback()
            return jsonify( { 
                'response': f'This order (#{ recent_order }) has been recorded already,\
                proceed to making payments/geting receipt',
                'flash':'alert-primary',
                'link': f'{ pay_link or url_for("cart.ordered", o_id=recent_order)   }',
                'receipt': f'{url_for("cart.ordered", o_id=recent_order )}'
                             })
    
    except Exception as e:
            print(e)
            db.session.rollback()
            flash(f"Oops an error occured, pls try again-> ", "primary")
            return jsonify( { 
                'response': f'ooops!!!, an error occured, kindly try again({e})',
                'flash':'alert-primary' })








