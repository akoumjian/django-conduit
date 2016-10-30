

def get_field_by_name(obj, field_name):
    """
    Handles differences in Django versions
    """
    if hasattr(obj._meta, 'get_field'):
        field = obj._meta.get_field(field_name)
    else:
        field, model, direct, m2m = obj._meta.get_field_by_name(field_name)
    return field


def get_all_field_names(obj):
    """
    Get all field names for a model, despite Django version
    """
    if hasattr(obj._meta, 'get_all_field_names'):
        ## Django < 1.9
        field_names = obj._meta.get_all_field_names()
    else:
        ## Django >= 1.9
        field_names = [f.name for f in obj._meta.get_fields()]
    return field_names
