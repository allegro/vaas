from django.db import connection


def create_model_if_not_exists_factory(table_name, app_label, model_name):
    def create_model_if_not_exists(apps, schema_editor):
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE %s", [table_name])
            exists = cursor.fetchone()

        if not exists:
            Model = apps.get_model(app_label, model_name)
            schema_editor.create_model(Model)
    return create_model_if_not_exists
