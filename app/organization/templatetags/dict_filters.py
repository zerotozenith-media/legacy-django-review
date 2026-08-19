from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    # Convert key to integer if it's a string
    key = int(key)
    return dictionary.get(key, None)


@register.filter
def subtract(value, arg):
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return ''


@register.filter
def add(value, arg):
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return ''


@register.filter
def capitalize_words(value):
    return value.replace('_', ' ').title()


@register.filter
def capitalize_and_contrib_type(value):
    new_word = value
    if value == 'offerings_can':
        new_word = "Offering CAD"
    if value == 'offerings_usd':
        new_word = "Offering USD"
    if value == "interec_e_transfer":
        new_word = "Interac Transfer"
    if value == "cheque_deposit":
        new_word = "Cheque Deposit"
    if value == "direct_transfer":
        new_word = "Direct Transfer"
    return new_word
