#from sqlite3 import IntegrityError
import requests, random
#from sqlalchemy import exc
#from sqlalchemy.exc import IntegrityError
from sqlalchemy import exc

from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from flask_login import current_user
from web.models import db, Listing, Order
from web.cart.forms import OrderForm, pment_option

cart = Blueprint('cart', __name__)

#<action> -> save/remove/update/wipe/_
@cart.route('/<string:action>/basket', methods=['GET','POST'])
def basket(action):

    item, qty = str(request.args.get('item', 0)), int(request.args.get('qty', 1 ))
    
    cart = session.get('basket', {})

    try:
        if action == 'save':
            if Listing.exists(item):
                cart[item] = (cart.get(item, 0) + qty)
                session['basket'] = cart
                return 'Success, You\'ve Added To Your Shopping Basket'
            return 'Failed!, This Item Is Not Found'
        
        if action ==  'update':
            if item in cart and qty is not None:
                cart[item] += qty
                session['basket'] = cart
                return 'Success, You\'ve Updated Your Shopping Basket'
            #if not carted-already, but want-to update, save as new item in cart, with value to be updated with
            elif Listing.exists(item):
                cart[item] = (cart.get(item, 0) + qty)
                session['basket'] = cart
                return 'Success, You\'ve Updated Your Shopping Basket'
            
            return 'Failed, Unable To Update Your Shopping Basket'
        
        if action ==  'remove':
            if item in cart:
                del cart[item]
                session['basket'] = cart
                
                return 'Success, You\'ve Removed From Your Cart'
            return 'Sorry, Unable To Remove From Your Shopping Cart'
        
        if action ==  'wipe':
            if len(cart) > 0 :
                del session['basket']
                return 'Hmm, You\'ve Emptied Your Shopping Basket'
            return 'Sorry, Unable To Wipe-Off Your Shopping Basket'
        
        if action ==  'fetch':
            if len(cart) < 0 :
                return cart
            return 'Sorry, Your Shopping Basket Is Empty Right Now'

            carted = Listing.query.filter(Listing.id.in_(cart.keys())).all()
            sub_total =  sum([c.price * int(cart[str(c.id)]) for c in carted ]) 
            item_count = len(carted) #from-db-count
            baskett = [{ 
                    'item': c.id, 
                    'name': c.name, 
                    'image': c.photos, 
                    'qty':  cart.values() if c.id in cart.keys() else 1 ,
                    'qty':  cart[str(c.id)] ,
                    'price':  c.price, 
                    'total_each':  c.price * int(cart[str(c.id)]) ,
                    'attr': c.attributes[0],
                } for c in carted] , sub_total, item_count
            
            #session['basket'] = cart
            return jsonify(basket)
        session.modified = True
        return jsonify(cart)

    except Exception as e:

        return jsonify(f"{e}")



#<int:o_id> == <int:order_id
@cart.route("/ordered/<int:o_id>", methods=['GET', 'POST'])
def ordered(o_id):

    try:

        order = Order.query.filter( Order.order_id == o_id ).first_or_404()

        dt = order.order_item

        items = Listing.query.filter(Listing.id.in_(dt.keys() )).all()

        sub_total =  sum([i.price * int(dt[str(i.id)]) for i in items ]) 

        item_count = len(items) #from-db-count

        #LEAVE THIS CONTEXT, IN CASE YOU NEED TO USE A JSON ENDPOINT
        """ context = [{ 
                'item': i.id, 
                'name': i.name, 
                'photo': i.photos[0], 
                'qty':  dt[str(i.id)] ,
                'price':  i.price, 
                'total_each':  i.price * int(dt[str(i.id)]) ,
                'attr': i.attributes[0],
            } for i in items] , sub_total, item_count 
        #return f"{context}" 
        #return f"{[item.name for item in items]}"
        
        """

        context = {

            'order_id': order.order_id,
            'order_name': order.name,
            'order_email': order.email,
            'order_phone': order.phone,
            'order_country': order.country,
            'order_state': order.state,
            'order_adrs': order.adrs,
            'order_zipcode': order.zipcode,
            'order_status': order.order_status,

            'order_payment_option':  which_option(order.pment_option), 
            'order_created': order.created,

            'sub_total': sub_total,
            'item_count': item_count,

            'order_item': [{ 
                'item': i.id, 
                'name': i.name, 
                'photo': i.photos[0], 
                'qty':  dt[str(i.id)],
                'price':  i.price, 
                'total_each':  i.price * int(dt[str(i.id)]),
                'attr': i.attributes[0],
            } for i in items ]
        }

    except Exception as e:
        return f"{e}"
    
    return render_template('invoice.html', **context )


""" class ExampleException(Exception):
    def __init__(self, foo):
        self.foo = foo
        try:
            raise ExampleException("Bar!")
        except ExampleException as e:
            print e.foo """

""" class CustomIntegrity(exc.IntegrityError):
    def __init__(self, orderd_id):
        self.orderd_id = orderd_id
        
        try:
            raise CustomException("Bar!")
        except CustomException as e:
            print e.ordered_id """

#create order
""" 
class CustomIntegrity(exc.IntegrityError):
    def __init__(self, oid):
        self.oid = oid
        #return redirect(url_for('cart.ordered', o_id=orderd_id)) """


""" from weasyprint import HTML

def htmlpdf(html_url):
    HTML(html_url).write_pdf( html_url + '.pdf' ) """

@cart.route('/basket', methods=['GET','POST'])
def baskt():
    form = OrderForm()
    cart = session.get('basket', {})

    #order_id = random.randint(0, 999999) #this-one-changes-often, so not suitable, there's a default one generated @ db level
    
    try:
        if form.validate_on_submit():

            ordered = Order( 
                
                usr_id = current_user.id \
                    if current_user.is_authenticated else 0, #so that even-if you're not logged in, you can still place orders
                
                order_item = cart, #bcos from up, if no carted-item, it won't run

                #order_id=order_id, 

                email=form.email.data, 
                phone=form.phone.data,
                name=form.name.data, 
                adrs=form.adrs.data, 
                country=form.country.data, 
                state=form.state.data, 
                zipcode=form.zipcode.data, 
                #ordert_amt=form.ordert_amt.data, 
                pment_option=form.pment_option.data, 

                )

            db.session.add(ordered)
            db.session.commit()
            db.session.flush()
            
            db.session.refresh(ordered) #refresh so-i-can-get-the-last/new-insert-id

            pay = payment_option( form.pment_option.data, amt=int(float(form.ordert_amt.data)) )

            session['recent_order'] = ordered.order_id #save-order-id in session so it can be retrieved from exception block incase or of IntegrityError

            if len(session['basket']) > 0 :
                del session['basket']  #remove it from cart if saved to db as order
            return pay if pay and ordered.order_id else redirect(url_for('cart.ordered', o_id=ordered.order_id)) 
        
    except exc.IntegrityError as e:
            print(e)
            db.session.rollback()
            #cart = session.get('recent_order', {})
            flash(f"Success !!!, You're Order Was Placed ", "info")
            return redirect(url_for('cart.ordered', o_id=session.get('recent_order', 0))) 
            #return f"Order Already Placed Successfully {session['recent_order']}"
    
    except Exception as e:
            print(e)
            db.session.rollback()
            flash(f"Oops an error occured, pls try again-> ", "info")
            return f"\n Error!!! Kindly Try Again"

    return render_template('basket.html', cart=cart, form=form)



@cart.route("/order", methods=['GET', 'POST'])
def order():
    form = OrderInfoForm() 
    """if request.method == "POST":
        flash(form.data, 'warning')""" 
    try:
        if form.validate_on_submit():
            order_info = Orderinfo( 
                usr = current_user.id if current_user.is_authenticated else None, #so that even-if you're not logged in, you can still place orders
                email=form.email.data, 
                phone=form.phone.data,
                name=form.name.data, 
                state=form.state.data, 
                bustop=form.bustop.data, 
                street=form.street.data, 
                )

            db.session.add(order_info)
            db.session.commit()
            flash('Order Details Recorded !', category='success')
            #return redirect(request.referrer)
            return "Order Details Recorded !"
    except Exception as e:
        return f"{e}"
    
    return render_template('checkout.html', form=form)