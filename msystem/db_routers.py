class SearchRouter:
    """
    Routes the `search` app models to the `search` database.
    Everything else uses the default database.
    """

    app_label = 'search'   # app name for search module

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return 'search'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return 'search'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations if both models in same DB
        if obj1._meta.app_label == self.app_label and obj2._meta.app_label == self.app_label:
            return True
        if obj1._meta.app_label != self.app_label and obj2._meta.app_label != self.app_label:
            return True
        return False

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Migrate search models only to 'search' DB
        if app_label == self.app_label:
            return db == 'search'

        # All other models → default DB
        return db == 'default'
