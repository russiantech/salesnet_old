    
""" from flask import Blueprint
from web.models import Category
cate = Category.query.order_by(Category.id).all()
 """
""" data = [

    { 'id': 1, 'parent': 2, 'name': "Node1" },
    { 'id': 2, 'parent': 5, 'name': "Node2" },
    { 'id': 3, 'parent': 0, 'name': "Node3" },
    { 'id': 5, 'parent': 0, 'name': "Node5" },
    { 'id': 9, 'parent': 1, 'name': "Node9" }
] """


def build_category_tree(categories, parent_id=None):
    """ This will format a multi-level query object into a list of nested dict """
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

    """ SAMPLE FORMATTED CATEGORY FROM build_category_tree(data) """
    """ data = [
        {
            'id': 1,
            'name': 'Services',
            'children': [
                {
                    'id': 40,
                    'name': 'Cleaning',
                    'children': [
                        {
                            'id': 86,
                            'name': 'Industrial',
                            'children': [
                                {'id': 88, 'name': 'External', 'children': []},
                                {'id': 89, 'name': 'Internal', 'children': []}
                            ]
                        },
                        {'id': 87, 'name': 'Interior & Homes', 'children': []}
                    ]
                },
                {'id': 41, 'name': 'IT', 'children': []},
                # ... (other categories)
            ]
        },
        {'id': 2, 'name': 'Free Stuffs', 'children': []},
        {'id': 3, 'name': 'Property', 'children': []},
        # ... (other top-level categories)
    ]
    """




def categorylist(categories):
    category_list = { 
        #0: { 'id': 0, 'parent': 0, 'name': "Root node", 'sub': [] }
    }
    for category in category_list:
        category_list.setdefault(category['parent'], { 'sub': [] })
        category_list.setdefault(category['id'], { 'sub': [] })
        category_list[category['id']].update(category)
        category_list[category['parent']]['sub'].append(category_list[category['id']])

    return category_list


def categ(cate):
    cat = { 
        #0: { 'id': 0, 'parent': 0, 'name': "Root node", 'sub': [] }
    }

    cat = {}
    for c in cate:
        cat.setdefault(c['parent'], { 'sub': [] })
        cat.setdefault(c['id'], { 'sub': [] })
        cat[c['id']].update(c)
        cat[c['parent']]['sub'].append(cat[c['id']])

    return cat

    #return f"{jsonify(cat)}"

#function-calling
""" f = categ(data)
pprint.pprint(f) """

#return f'{f}'


""" $refs = array();
$list = array();

$sql = "SELECT item_id, parent_id, name FROM items ORDER BY name";

/** @var $pdo \PDO */
$result = $pdo->query($sql);

foreach ($result as $row)
{
    $ref = & $refs[$row['item_id']];

    $ref['parent_id'] = $row['parent_id'];
    $ref['name']      = $row['name'];

    if ($row['parent_id'] == 0)
    {
        $list[$row['item_id']] = & $ref;
    }
    else
    {
        $refs[$row['parent_id']]['children'][$row['item_id']] = & $ref;
    }
} """

""" refs = []
list = []
cate_ = None
for c in cate_:
    ref = refs[ c['id'] ]
    ref['parent'] = c['parent']
    ref['name'] = c['name']

    if c['parent'] == None:
        list[ c['id'] ] = ref
    else:
        refs[c['parent']]['child'][c['id']] = ref """




