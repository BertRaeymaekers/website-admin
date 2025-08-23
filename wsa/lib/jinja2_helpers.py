import datetime


def format_date(input):
    if isinstance(input, datetime.date):
        return input.strftime("%d/%m/%Y")
    return str(input)

def register_in_template(template):
    for func in [format_date]:
        template.globals[func.__name__] = func
