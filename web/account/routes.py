from flask import g, json, redirect, render_template, stream_template, jsonify, Blueprint, url_for, flash, session, request
from flask_login import current_user
from web.utils.decorators import db_session_management
from web import  main
from web.extensions import db, cache

from web.utils.save_image import uploader
from web.models import Order, Listing
from web.account.forms import OrderForm, PostForm

from web.utils.ip_adrs import user_ip
#from web.utils.categorylist import build_category_tree
from web.utils.slug import slugifie 

def payOptionCheck(option, amt=500):
    try:
        if option : 

            match option:
                case 'fw':
                    return redirect(url_for('pay.payform', amt=amt))
                
                case 'ps':
                    return redirect(url_for('pay.payform', amt=amt))
                
                case 'pp':
                    return redirect(url_for('pay.payform', amt=amt))
                
                case 'cash' | 'chq':
                    pass
                case _:
                    return redirect(url_for('pay.payform', amt=amt))

        flash(f'Amount Or Cart Is Missing', category='danger')
        #return f"Amount Or Cart Is Missing"
        pass
    except Exception as e:

        flash(f'Error Occured {e}', category='info')
        return f"{e}"

def which_option(option):
    try:
        if option : 

            match option:
                case 'fw':
                    return 'Flutterwaves'
                
                case 'ps':
                    return 'Paystack'
                
                case 'pp':
                    return 'Paypal'
                
                case 'cash' | 'chq':
                    return 'Cash/Cheque payment'
                case _:
                    return 'Cash on delivery'

        flash(f'payment option missing', category='danger')
        return f"payment option missing"
    
    except Exception as e:

        flash(f'Error Occured {e}', category='success')
        return f"{e}"
    
acct = Blueprint('acct', __name__)

def exclude_deleted(query):
    return query.filter_by(deleted=False, status=False)

@acct.route('/list', methods=['GET', 'POST'])
def lists():
    form = PostForm()   
    categories = { x['name'] : [ (c['id'], c['name']) for c in x['children'] ] if x['children'] \
                  else [(x['id'], x['name'])] for x in g.categories }
    return render_template('incs/posts.html',form=form)


@acct.route('/post', methods=['POST'])
@db_session_management
def post():

    form = PostForm(request.form)
    referrer = request.headers.get('Referer')

    if form.validate_on_submit():

        saved_images = {i: uploader(x) for i, x in enumerate(request.files.getlist('images')) if x} or None
        colors = {i: color.data for i, color in enumerate(form.color) if color} or None
        sizes = {i: size.data for i, size in enumerate(form.size) if size} or None
        amenities = {i: amenity.data for i, amenity in enumerate(form.amenities) if amenity} or None
        user_id = current_user.pages.id if current_user.is_authenticated else 1
        locations = {'region': form.region.data, 'city': form.city.data, 'street': form.street.data, 'zipcode': form.zipcode.data}
        contacts = {'name': form.cont_name.data, 'email': form.cont_email.data, 'phone': form.cont_phone.data, 'company': form.company.data}
        listing_type = (form.property_type.data or form.vehicle_type.data or form.job_type.data or form.service_type.data or None)

        if request.method == 'POST':

            new_listing = Listing(
                page_id=user_id,
                user_id=user_id,
                cate_id=form.cate.data,
                sku=form.sku.data or None,
                title=form.title.data,  # required
                images=json.dumps(saved_images) if saved_images is not None else None,
                price=form.price.data,  # required
                pay_interval=form.pay_interval.data or None,
                listing_brand=form.brand.data,
                location=json.dumps(locations) or None,
                contact=json.dumps(contacts) or None,
                company=form.company.data or None,  # str
                discount=form.discount.data or None,
                desc=form.desc.data or "...",
                negotiable=form.negotiable.data or False,
                meet_up=form.meet_up.data or None,
                availability=form.availability.data,
                color=json.dumps(colors) if colors else None,
                size=json.dumps(sizes) if sizes else None,
                stock_qty=form.stock_qty.data or 1,
                ip=user_ip(),
                date_available=form.date_available.data or None,
                listing_type=listing_type,
                # //property
                amenities=json.dumps(amenities) or None,
                property_for=form.property_for.data or None,  # int
                # //vehicle
                year=form.year.data or None,  # str
                fuel_type=form.fuel_type.data or None,  # str
                make=form.make.data or None,  # str
                model=form.model.data or None,  # str
                # //jobs
                job_setup=form.job_setup.data or None,  # str
                job_level=form.job_level.data or None,  # str
                min_qualify=form.min_qualify.data or None,  # str
                pay_range=form.pay_range.data or None,  # str
                min_exp=form.min_exp.data or None,  # str
                responsibilities=form.responsibilities.data or None,  # str
                required_skills=form.required_skills.data or None, # str
            )

            db.session.add(new_listing)
            db.session.commit()
            db.session.flush()
            db.session.refresh(new_listing)  # refresh to get the last/new insert id

            # Invalidate the cached product listing to re-cache afresh/updated ones
            cache.delete_memoized(main.routes.index)
            global list_slug, referring_url
            list_slug = slugifie(new_listing.title, new_listing.id)
            referring_url = url_for('main.lists', list_slug=list_slug) or referrer
            return jsonify({
                'response': f'Success!!!, {new_listing.title} now on internet of sales',
                'flash': 'alert-success',
                'link': referring_url  # Assuming referring_url is a valid URL
            })
    
    
@acct.route('/ordering', methods=['POST', 'GET']) # -> basket, merged with checkout in same route
def save_order():
    
    form = OrderForm()

    form.order_amt.data = 500

    cart = session.get('basket', {})
    
    try:

        if len(cart) < 1 :
            return jsonify( { 
                'response': f'Your Shopping Basket Is Empty, Browse Salesnet & Add Listing(s) To Continue',
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
    
@acct.route("/<usr>/account")
@acct.route("/account")
def me(usr=None):
    context = {
        'pname' : 'Account'
    }
    return render_template('account/me3.html')

@acct.route('/browsed')
def history():
    context = {
        'pname' : 'History'
    }
    return render_template("account/history.html", **context)

@acct.route('/<item>/saved')
@acct.route('/saved')
def saved(item=None):
    context = {'pname' : 'Favorite'}
    return render_template("account/saved.html", **context)

@acct.route('/cart', methods=['POST', 'GET']) # -> basket, merged with checkout in same route
def cart():

    form = OrderForm()

    form.order_amt.data = 500

    context = { 'pname' : 'Basket', 'form' : form }

    return render_template("account/cart2.html", **context)

@acct.route('/track')
def track():
    context = {
        'pname' : 'Tracking'
    }
    return render_template("account/track.html", **context)

@acct.route('/invoice')
def invoice():
    context = {
        'pname' : 'Invoice'
    }
    return render_template("account/invoice.html", **context)

@acct.route('/followed')
def followed():
    context = {
        'pname' : 'Followed'
    }
    return render_template("account/followed.html", **context)

@acct.route('/_chat')
def chat():
    context = { 'pname' : 'Chats' }
    return render_template("account/checkout.html", **context)


####### VENDORS ######################

@acct.route('/post1', methods=['GET', 'POST'])
def post1():
    form = PostForm()   

    if request.method == 'POST': #and form.validate_on_submit():
        return f"{form.data}"
        uploaded_photos = request.files.getlist('photos')
        #saved_photos = [ x.filename for x in uploaded_photos]

        return f"{saved_photos, '----->',uploaded_photos}"

        """for photo in uploaded_photos:
            photos = photo.filename
            if photo.filename:
                unique_filename = f"{uuid.uuid4().hex}_{photo.filename}"
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                photo.save(photo_path)
                saved_photos.append(photo_path) """
        
        return render_template('preview.html', saved_photos=saved_photos)

    if request.method == 'POST' and form.validate_on_submit():
            #return f"{form.data}"
        if not form.validate_on_submit():
            return f"{request.files}"

    categories = { x['name'] : [ (c['id'], c['name']) for c in x['children'] ] if x['children'] else [(x['id'], x['name'])] for x in g.categories  }
    form.cate.choices = categories
    context = { 'pname' : 'listing', 'form': form }
    return stream_template("account/posts1.html", **context)

@acct.route("/<usr>/vendor")
@acct.route('/vendor')
def vendor(usr=None):
    context = {
        'pname' : 'Vendor'
    }
    return render_template("account/vendor.html", **context)

@acct.route("/<usr>/shop")
@acct.route('/shop')
def shop(usr=None):
    context = {
        'pname' : 'Neon Shops'
    }
    return render_template("account/shop.html", **context)

@acct.route("/<usr>/brands")
@acct.route('/brands')
def brand(usr=None):
    context = {
        'pname' : 'Brands'
    }
    return render_template("account/brand.html", **context)








