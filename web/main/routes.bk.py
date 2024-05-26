
from flask import (g, redirect, render_template, stream_template, request, Blueprint, url_for, jsonify, current_app, session)
from web.extensions import cache, db
from web.models import User, Item, Category
from web.utils import categorylist
from flask_login import current_user, login_required
from  sqlalchemy.sql.expression import func

import sys, traceback
from web.account.forms import PostForm
#from os import environ
main = Blueprint('main', __name__)


from flask_wtf import FlaskForm
from wtforms_alchemy import QuerySelectField


def categories_to_nested_list(categories):
    category_list = {}
    root = { 'id': 0, 'parent': 0, 'name': "Root-Node", 'sub': [] }
    
    for category in categories:
        category_list[category['id']] = { 'id': category['id'], 'name': category['name'], 'sub': [] }
        parent_id = category['parent']
        if parent_id in category_list:
            category_list[parent_id]['sub'].append(category_list[category['id']])
        else:
            root['sub'].append(category_list[category['id']])
    
    #return root['sub']
    return root['sub']



# Example usage
category_query = [
    { 'id': 1, 'parent': 0, 'name': "Category 1" },
    { 'id': 2, 'parent': 1, 'name': "Subcategory 1.1" },
    { 'id': 3, 'parent': 2, 'name': "Sub-subcategory 1.1.1" },
    # ... more categories ...
]




#categories_query = Category.query.filter_by(parent_id=None).all()


def build_category_tree(categories, parent_id=None):
    nested_list = []
    for category in categories:
        if category.parent_id == parent_id:
            nested_dict = {
                'id': category.id,
                'name': category.name,
                'children': build_category_tree(categories, category.id)
            }
            nested_list.append(nested_dict)
    return nested_list



#nested_list_result = convert_to_nested_list(categories_query)
#print(nested_list_result)

@main.route('/category', methods=['GET', 'POST'])
def your_view_function():
    
    cate = Category.query.order_by(Category.id).all()

    """ num_categories_to_load = 150
    random_categories = (
        Category.query.order_by(func.rand())  # Use func.rand() for MySQL, func.random() for PostgreSQL
        .limit(num_categories_to_load)
        .all()
    )

    nested_list_result = categorylist.build_category_tree(random_categories) """
    #return f"{(nested_list_result)}"
    #return f"{g.categories}"
    form = CategoryForm()
    return render_template('category.html', form=form)

    
@main.route("/")
@main.route("/home")
#@cache.cached(timeout=600)  # Cache for 10 minutes
def index():
    #try:
    items = Item.query.order_by(func.rand()).limit(70)
    context = { 'item': items}

    return render_template('home.html', **context )



@main.route('/shop')
def shop():
    page = request.args.get('page', 1, type=int)
    items = Products.query.paginate(page=page, per_page=6)
    return render_template("shop.html", items = items)

@main.route('/shop/<int:pid>')
def single(pid):
    items = Products.query.order_by(func.rand()).limit(7)
    item = Products.query.filter_by(id=pid).first_or_404()
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


