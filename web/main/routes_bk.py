
from datetime import datetime
from flask import (g, url_for,current_app,   render_template, request, Blueprint)
from flask_babel import _
from sqlalchemy.sql.expression import func
from web.utils.slug import slugifie
from web.models import Listing
from web.extensions import cache
from web.utils.custom_mixins import SearchForm

main = Blueprint('main', __name__) 

from wtforms.fields import FieldList
from wtforms import FileField
from wtforms.widgets import FileInput
from flask_wtf import FlaskForm

class CustomFileInput(FileInput):
    def __call__(self, field, **kwargs):
        if field.data:
            kwargs.setdefault('value', field.data.filename)
        return super().__call__(field, **kwargs)

class PhotoForm(FlaskForm):
    photos = FieldList(FileField('Upload Photo', widget=CustomFileInput()), min_entries=1, max_entries=5)

@main.route('/search')
def search():
    #try:
    searchform = SearchForm()
    if not searchform.validate():
        #return redirect(url_for('main.index'))
        pass
    page = request.args.get('page', 1, type=int)
    posts, total = Listing.search(searchform.q.data, page, current_app.config['POSTS_PER_PAGE'])
    
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=searchform.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts,
                        next_url=next_url, prev_url=prev_url)

    """ except Exception as e:
        return f"{e}"
     """

@main.route("/chatme")
def chatme():
    return render_template('incs/modals/chatme/chatlist.html')

@main.route("/", methods=['GET', 'POST'])
#@main.route("/home")
#@cache.cached(timeout=5)  # Cache the result of the route
#@cache.memoize(timeout=60)
#@db_session_management  # Manage the database session
def index():
    #items = Listing.query.order_by(func.rand()).limit(70)
    context = {'item': 'items'}
    if cache.get(request.base_url):  # Check if the result is in the cache
        print("Cached hit!")
    else:
        print("Cache miss!")
    #print(cache)
    print(f'time-is-({datetime.utcnow()}')  # To check caching; if the time does not change, it's working
    return render_template('index.html', **context)

@main.route('/lists/<string:list_slug>')
def lists(list_slug):
    lists = Listing.query.order_by(func.rand()).limit(7).all()
    list_slug = slugifie(list_slug) #not really paramount
    listed = Listing.query.filter(slugifie(Listing.title, Listing.id) == list_slug ).first_or_404()
    if listed is None:
        return render_template('404.html'), 404
    context = {"listed": listed, "lists": lists}
    return render_template('item_details.html', **context)

#http://localhost:5000/fashionation/sales
#http://localhost:5000/@hacker/pages
@main.route('/<string:salespage>/sales')
def salespage(salespage):
    page = request.args.get('page', 1, type=int)
    listing = Listing.query.filter(Listing.page_id==salespage).paginate(page=page, per_page=6)
    return render_template("salespage.html", listing = listing)

@main.route('/<string:userpage>/pages')
def userspage(userpage):
    page = request.args.get('page', 1, type=int)
    listing = Listing.query.filter(Listing.page_id==userpage).paginate(page=page, per_page=6)
    return render_template("userspage.html", listing = listing)

@main.route('/<string:username>/saved')
def saved(userpage):
    page = request.args.get('page', 1, type=int)
    listing = Listing.query.filter(Listing.page_id==userpage).paginate(page=page, per_page=6)
    return render_template("salespage.html", listing = listing)

@main.route('/shop/<int:pid>')
def single(pid):
    items = Listing.query.order_by(func.rand()).limit(7)
    item = Listing.query.filter_by(id=pid).first_or_404()
    context = {"items":items, "item":item}
    return render_template("single.html", **context)

@main.route("/us")
def us():
    return render_template('us.html', pname='About Us')

@main.route('/intouch')
def intouch():
    return render_template("intouch.html", pname='Reach Us')

@main.route('/terms')
def terms():
    return render_template("terms.html", pname='Terms Of Use')

@main.route('/privacy')
def privacy():
    return render_template("privacy.html", pname='Privacy Policy')

@main.route('/faqs')
def faqs():
    return render_template("faqs.html", pname='Frequently Asked Questions')

@main.route('/testify')
def testify():
    return render_template("testify.html", pname='Testimonials')


