class OpenEMRRouter:
    """
    A router to control all database operations on models in the
    openemr_db application (OpenEMR Legacy Tables).
    """
    route_app_labels = {'openemr_db'}

    def db_for_read(self, model, **hints):
        """
        Attempts to read openemr_db models go to openemr.
        """
        if model._meta.app_label in self.route_app_labels:
            return 'openemr'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write openemr_db models go to openemr.
        """
        if model._meta.app_label in self.route_app_labels:
            return 'openemr'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the auth or openemr_db apps is
        involved.
        """
        if (
            obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels
        ):
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the openemr_db app only appears in the 'openemr'
        database.
        """
        if app_label in self.route_app_labels:
            return db == 'openemr'
        return None
