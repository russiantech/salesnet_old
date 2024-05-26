import json
from flask_wtf import FlaskForm
from flask import url_for
from flask_login import current_user
from datetime import datetime
from wtforms import ValidationError, StringField, FileField, TextAreaField, SubmitField, SelectField, TelField,\
    IntegerField, DecimalField, HiddenField,DateTimeField, SelectMultipleField, widgets, RadioField, BooleanField
from wtforms.validators import Optional, DataRequired, Length, Email 
from flask_wtf.file import FileField

from wtforms.widgets.core import html_params
from markupsafe import Markup
import re  # Import the regular expressions module
from PIL import Image

state_choice = [('','choose'), ('ls','Lagos'), ('abj','Abuja'), ('ph','Portharcourt'),  ('abia','Abia '), ('cr','Cross River') ]
country_choice = [('','Choose'), ('ng','Nigeria'), ('gh','Ghana'), ('cam','Cameroun'),  ('tg','Togo '), ('us','United States') ]
payOptionChoice = [('fw','Flutterwave'), ('ps','Paystack'), ('pp','Paypal'), ('card','Card payment'),  ('cash','Cash on delivery'), ('chq','Cheque payment') ]

required_file_type = ['mp4', 'svg', 'webp', 'png', 'jpg', 'jpeg', 'gif']

size_choice = [('s','S'), ('m','M'), ('l','L'), ('xl','XL'),  ('xxl','XXL')]
color_choice = [('#ff6191',''), ('#33317d',''), ('#56d4b7',''), ('#009688','')]


amenity_choices = [
    ('wifi', 'WiFi'), ('air-conditioning', 'Air conditioning'), ('balcony', 'Balcony'), ('garage', 'Garage'), ('gym', 'Gym'), ('pets-friendly', 'Pets-friendly'), ('pool', 'Pool'), ('bar', 'Bar'), ('tv', 'TV'),
    ('linens', 'Linens'), ('heating', 'Heating'), ('dishwasher', 'Dishwasher'), ('iron', 'Iron'), ('hair dryer', 'Hair dryer'), ('kitchen', 'Kitchen'), ('breakfast', 'Breakfast'), ('security-cameras', 'Security cameras')
     ]

meet_up_choices = [('door dropoff','Door dropoff'), ('door pickup','Door pickup'), ('public meetup','Public meetup'),('delivery Available','Delivery Available')]

price_interval_choices = [('day','Per Day'), ('week','Per Week'),('month','Per Month'), ('year','Per Year'), ('commission', 'Commission Based'), ('lifetime','Life Time')]
condition_choices = [('new','New'), ('used like new','Used like new'),('faily used','Used good, Used fair')]

current_year = datetime.now().year
end_year = current_year + 1  # Set the maximum year to one year after the current year
year_choices = [(str(year), str(year)) for year in range(2010, end_year)]
fuel_type_choices = [('diesel','Diesel'), ('electric','Electric'),('gasoline','Gasoline'), ('flex','Flex'), ('hybrid','Hybrid'), ('Plug-in-hybrid','Plug-in hybrid'),('other','Other') ]

#********
property_for_choices =  [('rent','For Rent'), ('sale','For Sale')]

#Dynamic-choices:(vehicle, property)
#House, Townhouse, Apartment, Commercial, Daily Rental, New Building, Apartment/condo, Room only
#.Vehicle type(Car/Truck, Motor cycle, Powersport, RV/Camper, Trailer, Boat, Commercial/Industrial, Other)
    #Job type(Contract, Freelance, Full-Time, Internship, Per Time, Temporary)
    #service type[physical,  digital, services, local}), etc.

vehicle_type_choices =  [('car/truck','Car/Truck'), ('motor cycle','Motor cycle'),('powersport','Powersport'),
('rv/camper','RV/Camper'), ('trailer','Trailer'),('Boat','Boat'),('Commercial/Industrial','Commercial/Industrial'), ('Other','Other')]

property_type_choices =  [('house','House'), ('townhouse','Townhouse'),('apartment','Apartment'),
('commercial','Commercial'), ('daily rental','Daily Rental'),('new building','New Building'),('apartment/condo','Apartment/condo'), ('room only','Room only')]

job_type_choices =  [('contract','Contract'), ('freelance','Freelance'),('full-time','Full-Time'),
('internship','Internship'), ('per time','Per Time'),('temporary','Temporary')]

service_type_choices =  [('physical','Physical'), ('digital','Digital'),('local','Local')]


class HierarchicalSelectField(SelectField):
    def __init__(self, *args, **kwargs):
        self.nested_data = kwargs.pop('nested_data')
        super().__init__(*args, **kwargs)
    
    def iter_choices(self, categories, level=0):
        for category in categories:
            yield (category['name'], level)
            if 'children' in category and category['children']:
                yield from self.iter_choices(category['children'], level + 1)

    def process_data(self, value):
        self.data = value

    def __call__(self, **kwargs):
        kwargs.setdefault('id', self.id)
        if 'value' not in kwargs:
            kwargs['value'] = str(self.data)
        if self.data:
            kwargs['selected'] = str(self.data)
        options = []
        for val, level in self.iter_choices(self.nested_data):
            indent = '&nbsp;' * (level * 4)  # Adjust the indentation as needed
            options.append('<option %s>%s%s</option>' % (html_params(value=val), indent, val))
        html = '<select %s>%s</select>' % (html_params(name=self.name, **kwargs), '\n'.join(options))
        return Markup(html)

this_month = datetime.now().strftime('%m')
this_year = datetime.now().strftime('%y') #without-century
current_year_full = datetime.now().strftime('%Y')  # 2023
current_year_short = datetime.now().strftime('%y')  # 10 without century

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

# Custom validator for image dimensions
def validate_image_dimensions(form, field):
    if field.data:
        img = Image.open(field.data)
        width, height = img.size
        if width < 200 or height < 200:
            raise ValidationError('Image dimensions must be at least 200x200 pixels.')

class MultiSelectField(SelectMultipleField):
    option_widget = widgets.CheckboxInput()

##############
class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class MultiColorField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.Input('color')

# //currently not in use
class MultiImageField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.Input('file')
##############

# Function to generate salary ranges
def generate_salary_ranges(start, end, step):
    salary_ranges = []
    while start <= end:
        next_step = start + step
        salary_ranges.append((start, next_step - 1))
        start = next_step
    return salary_ranges

# Generate salary ranges and format them
salary_ranges = generate_salary_ranges(20, 900, 50)
payrange_choices = [f"${start} - ${end}" for start, end in salary_ranges]
#payrange_choices = [f"{start} - {end}" for start, end in salary_ranges]


class PayForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    amt = HiddenField('Amt', validators=[DataRequired()])
    submit = SubmitField('Authorize Payment')

class OrderInfoForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone',  validators=[ DataRequired(), Length(min=2, max=20)])
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=20)])
    state = SelectField('State', choices=state_choice)
    bustop = StringField('Nearest Bus Stop', validators=[DataRequired(), Length(min=2, max=20)])
    street = StringField('Street', validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField('Place My Order Now')

class OrderForm(FlaskForm):
    email = StringField('Valid email address', validators=[DataRequired(), Email()])
    phone = StringField('Active phone number',  validators=[Length(min=2, max=20)])
    name = StringField('Name(s)', validators=[DataRequired(), Length(min=2, max=20)])
    adrs = StringField('Address', validators=[DataRequired(), Length(min=2, max=20)])
    country = SelectField('Country', choices=country_choice, validators=[DataRequired(), Length(min=2, max=20)])
    order_amt = IntegerField('Payment Total', validators=[DataRequired()])
    pment_option = SelectField('Payment Option', choices=payOptionChoice, validators=[DataRequired(), Length(min=2, max=20)])
    state = SelectField('State', choices=state_choice, validators=[DataRequired(), Length(min=2, max=20)])
    zipcode = StringField('Zipcode', validators=[DataRequired(), Length(min=5, max=10)])
    tnc = BooleanField('Terms & Conditions', validators=[DataRequired()])
    submit = SubmitField('Place My Order Now')


class PostForm(FlaskForm):
    title = StringField('Title Ur Listing', validators=[DataRequired(), Length(min=2, max=20)])
    desc = TextAreaField('Describe Ur listing', validators=[DataRequired(), Length(min=0, max=300)])
    price = DecimalField('Price', render_kw={'min': 0}, validators=[DataRequired()])
    currency = SelectField('Currency', choices=[('', 'Select'), ('usd', '$'), ('eur', '€'), ('gbp', '£'), ('jpy', '¥')]) #optional
    cate = SelectField('Classify it', validate_choice = False,  choices = [], validators=[DataRequired()])
    tag = StringField('( Type & make comma to separate tags )')
    #images = MultipleFileField('Photos/Videos') 
    images = HiddenField('Photos/Videos', render_kw={'multiple': True, 'class':'filepond', 'required':True,}) 
    #images = MultipleFileField('Photos/Videos', render_kw={'multiple': True, 'class':'filepond', 'required':True,}) 
    images = FileField('Photos/Videos', render_kw={'multiple': True, 'hidden':True,}) 
    #change-this-bcos-of issues uploading to backend from ordinary filepond field. so the filepond html will upload/preview for frontend users and this file will be read and
    #also assigned to this very input field for upload
    """images = FileField('Photos/Videos', render_kw={'multiple': True, 'name':'images', 'class':'filepond', 'data-max-files':'15'},\
                       validators=[FileAllowed(required_file_type), DataRequired(),  validate_image_dimensions]) """
    negotiable = BooleanField('Negotiable', default=False)
    condition = SelectField('Select Condition', choices=condition_choices, coerce=str)
    meet_up = MultiCheckboxField('Select Delivery Options', choices=meet_up_choices, coerce=str)

    brand = StringField('What Brand Is This Item?(Optional)')
    sku = StringField('Optional. Only visible to you') #optional

    #Items
    stock_qty = IntegerField('Quantity', validators=[Optional()])
    discount = IntegerField('Discount ', validators=[Optional()])
    size = MultiCheckboxField('Size(s)',  choices=size_choice, coerce=str, default=None)
    #color = MultiColorField('Color(s)', choices=color_choice, render_kw={'hidden'}, default=None, validators=[Optional()])
    color2 = MultiColorField('Color(s)', choices=color_choice, validate_choice=False, validators=[Optional()])
    color = MultiColorField('Color(s)', choices=[], render_kw={'hidden':True}, validators=[Optional()])
    
    availability = RadioField('Availability', choices=[('instock', 'In Stock'), ('single', 'Single Item'), ('available', 'Available')], default='available')

    #Location
    region = StringField('(Country / region)') #country
    city = StringField('(Item City)') #state
    street = StringField('(Street address)') #street
    zipcode = StringField('(Zip code)') #zip code
    ip = StringField('Ip address', validators=[ Optional()])

    #Contacts(optional. Defaults to user's details)
    cont_name = StringField('(First & Last name(s))')
    cont_email = StringField('(Contact Email Address)') 
    cont_phone = TelField('(Contact Phone)') 
    company = StringField('(Company)') 

    #dynamically rendered based on category selected cos it differs
    #listing_type = StringField('Listing Type', validators=[Optional()])
    vehicle_type = SelectField('Vehicle Type', choices=vehicle_type_choices)
    property_type = SelectField('Property Type', choices=property_type_choices)
    job_type = SelectField('Job Type', choices=job_type_choices)
    job_level = SelectField('Job Level', default=None, validators=[Optional()], choices=[('Select Level'), ('senior', 'Senior Level'), ('middle', 'Middle Level'), ('junior', 'Junior Level'), ('leadership', 'Leadership Level')])
    service_type = SelectField('Service Type', choices=service_type_choices, default='physical')

    #Property
    pay_interval = SelectField('Choose Payment Interval', choices=price_interval_choices, coerce=str)
    amenities = MultiCheckboxField('Select As Applicable', default=None, choices=amenity_choices, coerce=str)
    property_size = IntegerField('Total area, sq.m', default=None, validators=[Optional()]) #sq.m
    bedrooms = IntegerField('Bed Rooms', default=None, validators=[Optional()]) 
    bathrooms = IntegerField('Bath Rooms', default=None, validators=[Optional()]) 
    property_for  = SelectField('Listed For?', choices=property_for_choices)
    date_available = DateTimeField('Select Date and Time', format='%Y-%m-%d %H:%M:%S', default=datetime.now, validators=[DataRequired()])
    #stock_qty = IntegerField('Quantity', validators=[Optional()])
    

    #Vehicle(S)
    year = SelectField('Select a Year', choices=year_choices)
    fuel_type = SelectField('Select fuel type', choices=fuel_type_choices)
    make = StringField('(Vehicle Making)')
    model = StringField('(Vehicle Model)')
    
    #job-listing
    job_setup = SelectField('Work Setup', choices=[('', 'Select'), ('remote', 'Remote/Online'), ('office', 'Office'), ('hybrid', 'Hybrid')])
    min_qualify = SelectField('Minimum Qualification(s)', choices=[('', 'Select'), ('vocational', 'Vocational Studies'),  ('MD/PHD', 'MD/PHD Degrees'), ('bsc', 'Bsc'), ('ssce', 'SSCE'), ('fslc', 'FSLC'), ('ond/hnd', 'HND/OND')])
    min_exp = SelectField('Minimum Experience', choices=[ (str(i), str(i) + ' Years') for i in range(0, 11) ])
    pay_range = SelectField('Pay Range', choices=[(p_range, p_range) for p_range in payrange_choices])
    #pay_range = SalaryRangeField('Salary/Pay Range', default=None, validators=[Optional()])
    responsibilities = TextAreaField('Responsibilities')
    required_skills  = TextAreaField('Requirement(s) & Skills')

    save_listing = SubmitField('Post & Sell')

    # Additional validation for file size
    def validate_image(self, images):
        if images.data:
            if len(images.data.read()) > MAX_FILE_SIZE_BYTES:
                raise ValidationError('Image size must not exceed 5 MB.')

    def validate_image(form, field):
        if field.data:
            field.data = re.sub(r'[^a-z0-9_.-]', '_', field.data)

    def validate_non_required_integer(self, price):
        if price.data is not None and not isinstance(price.data, int):
            raise ValidationError('Please Enter A Valid Integer.')
        
    def parse_json(self, json_str):
        try:
            if json_str:
                return json.loads(str(json_str))
        except json.JSONDecodeError:
            # Handle the case where json_str is empty or invalid JSON
            return None

    def parse_str(self, str):
        try:
            if str is None or str == "":
                return None
            return str
        except AttributeError:
            # Handle the case where json_str is empty or invalid JSON
            return None
        
    def to_dict(self):
        data = {
            'id': self.id,
            'ip': self.ip,
            'title': self.title,
            'price': self.price,
            'desc': self.desc,
            'cate_id': self.cate_id,
            'condition': self.condition,
            'currency': self.currency,
            'contact': self.parse_json(self.contact)  if self.contact else None,
            'location': self.parse_json(self.location) if self.location else None,
            'images': self.parse_json(self.images) if self.images else None,
            'amenities': self.parse_json(self.amenities)if self.amenities else None,
            'size': self.parse_json(self.size) if self.size else None,
            'color': self.parse_json(self.color) if self.color else None,
            'meet_up': self.meet_up,
            'pay_interval': self.pay_interval,
            'negotiable': self.negotiable,
            'availability': self.availability,
            'listing_type': self.listing_type,
            'listing_brand': self.listing_brand,
            'sku': self.sku,
            'stock_qty': self.stock_qty,
            'company': self.company,
            'discount': self.discount,

            'property_size': self.property_size,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'property_for': self.parse_str(self.property_for),
            'date_available': self.date_available,

            'fuel_type': self.fuel_type,
            'make': self.make,
            'model': self.model,
            'year': self.year,

            'job_level': self.job_level,
            'min_exp': self.min_exp,
            'min_qualify': self.min_qualify,
            'pay_range': self.pay_range,
            'responsibilities': self.responsibilities,
            'required_skills': self.parse_str(self.required_skills),
            'job_setup': self.job_setup,
            'listing_profile': url_for('listing_api.get_listing', id=self.id),

            'page_id': self.page_id,
            'cate_id': self.cate_id,
            'user_id': self.user_id,

            'page': {
                'id': 10,
                #'id':  self.pages.id if self.pages else None,
            },

            'user': {
                #'id':  current_user.id or None,
            },
            
            '_links': {
                'user_profile': url_for('user_api.get_user', id=self.user_id) if self.user_id else None,
                'self': url_for('listing_api.get_listing', id=self.id),
                'followers': url_for('listing_api.get_followers', id=self.id),
                'followed': url_for('listing_api.get_followed', id=self.id)
            }

        }

        return data
