from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Permite {{ meu_dict|get_item:chave }} nos templates."""
    return dictionary.get(key)
