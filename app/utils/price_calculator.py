from decimal import Decimal


def calculate_price(project, quantity: int = 1):
    if project.price_type == 'fixed':
        return {
            'unit_price': project.price,
            'total': project.price,
            'quantity': 1
        }
    elif project.price_type == 'unit':
        valid_qty = min(quantity, project.max_quantity or quantity)
        return {
            'unit_price': project.price,
            'total': project.price * valid_qty,
            'quantity': valid_qty
        }
    else:
        raise ValueError("Invalid price_type")
