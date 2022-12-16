from django import template
register = template.Library()


@register.filter
def uglify(string_value):
    x = int()
    output = ''
    for i in string_value:
        x += 1
        if x % 2 == 0:
            output += i.upper()
        else:
            output += i.lower()
    return output
