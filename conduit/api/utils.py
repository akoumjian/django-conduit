

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


def get_apps(*args):
    """
    Shim for different Django versions
    """
    selected_apps = []
    try:
        from django.apps import apps
        app_configs = apps.get_app_configs()
        for arg in args:
            app = None
            for app_config in app_configs:
                if app_config.name == arg:
                    app = app_config
            if app is None:
                raise Exception('Could not find app {}'.format(arg))
            selected_apps.append(app)
    except ImportError:
        from django.db.models import loading
        for arg in args:
            app = loading.get_app(arg)
            selected_apps.append(app)

    return selected_apps
