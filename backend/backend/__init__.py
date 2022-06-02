def quirk_add_admin_sorting():
    from django.contrib import admin
    from django.apps import apps

    def get_app_list(self, request):
        app_dict = self._build_app_dict(request)

        from django.contrib.admin.sites import site

        app_list = []

        for app_name in app_dict.keys():
            app = app_dict[app_name]
            model_priority = {
                model['object_name']: getattr(
                    site._registry[apps.get_model(app_name, model['object_name'])],
                    'sort_order',
                    20
                ) for model in app['models']
            }
            app['models'].sort(key=lambda x: (model_priority[x['object_name']], x['name'].lower()))
            app_list.append(app)

        def app_order(a):
            return getattr(apps.get_app_config(a['app_label']), 'sort_order', 20)

        app_list = sorted(app_list, key=lambda x: (app_order(x), x['name'].lower()))

        return app_list

    admin.AdminSite.get_app_list = get_app_list


def quirk_fix_autofield_graphql_type():
    from graphene_django.converter import convert_django_field, convert_field_to_int
    from django.db import models

    convert_django_field.register(models.AutoField)(convert_field_to_int)


for n, f in list(locals().items()):
    if n.startswith('quirk_'):
        f()
