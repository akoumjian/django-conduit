class GeoDbRouter(object):
    """
    A router to control all database operations on geomodels in the application.
    """
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'geodb':
            return 'geodefault'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'geodb':
            return 'geodefault'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'geodb' or \
           obj2._meta.app_label == 'geodb':
           return True
        return None

    def allow_syncdb(self, db, model):
        if db == 'geodefault':
            return model._meta.app_label == 'geodb'
        elif model._meta.app_label == 'geodb':
            return False
        return None
