def calculate_total_sales(item_id):
    item = Item.query.get(item_id)
    #total_sales = product.price * (product.stock_quantity - product.available_quantity())
    
    total_sales = item.price * (item.instock - item.available_quantity())
    return total_sales
