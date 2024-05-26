
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


@main.route("/", methods=['GET', 'POST'])
def index():
    context = {'item': 'items'}
    return render_template('index.html', **context)

@main.route("/<string:username>/users") #or /account
def user(username):
    return render_template('account.html', pname='Dunistech Services')

@main.route("/<string:username>/settings")
def settings(username):
    return render_template('settings.html', pname='Dunistech Services')

@main.route("/<string:username>/saved")
def saved(username):
    return render_template('saved.html', pname='Dunistech Services')

@main.route("/<string:username>/cart")
def cart(username):
    return render_template('cart.html', pname='Dunistech Services')

@main.route("/<string:username>/checkout")
def checkout(username):
    return render_template('cart.html', pname='Dunistech Services')

@main.route("/<string:username>/orders")
def orders(username):
    return render_template('orders.html', pname='Dunistech Services')

@main.route('/<string:cat>/clasify')
def clasify():
    return render_template("classify.html", pname='IT Sales')

@main.route('/<string:listed>/listing')
def listing(listed):
    return render_template("pages/list.html")

@main.route('/<string:p>/pages')
def page(p):
    return render_template("pages/page.html")

@main.route('/<string:p>/pages_bk')
def page_bk(p):
    return render_template("pages/page_bk_1.html")

@main.route('/signout')
def signout():
    return 'Bye !!!'

@main.route("/services")
def services():
    return render_template('services.html', pname='Dunistech Services')

@main.route("/us")
def us():
    return render_template('us.html', pname='About Us')

@main.route('/intouch')
def intouch():
    return render_template("intouch.html", pname='Reach Us')

@main.route('/blog')
def blog():
    return render_template("blog/blog.html", pname='Dunis Blog')

@main.route('/<string:blogslug>/blog')
def openblog(blogslug):
    return render_template("blog/blog_open.html", pname='Dunis Blog')

@main.route('/privacy')
def privacy():
    return render_template("privacy.html", pname='Privacy Policy')

@main.route('/faqs')
def faqs():
    return render_template("faqs.html", pname='Frequently Asked Questions')

@main.route('/testify')
def testify():
    return render_template("testify.html", pname='Testimonials')

