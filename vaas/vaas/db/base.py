from django.db.backends.mysql import base, features


class DatabaseFeatures(features.DatabaseFeatures):
    allows_group_by_pk = False

    def allows_group_by_selected_pks_on_model(self, model):
        return False


class DatabaseWrapper(base.DatabaseWrapper):
    features_class = DatabaseFeatures
