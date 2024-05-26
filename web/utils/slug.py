
from slugify import slugify

def slugifie(title, id=0):
    combined = f"{title}-{id}"
    return slugify(combined.lower())


""" def generate_slug(title, id):
    # Combine the title and id to create a unique string
    combined = f"{title}-{id}"
    # Use a slugify function to create a slug from the combined string
    return slugify(combined.lower()) """

