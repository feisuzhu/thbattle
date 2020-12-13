
def quirk_fix_autofield_graphql_type():
    from graphene_django.converter import convert_django_field, convert_field_to_int
    from django.db import models

    convert_django_field.register(models.AutoField)(convert_field_to_int)


for n, f in list(locals().items()):
    if n.startswith('quirk_'):
        f()
