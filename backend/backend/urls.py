# -*- coding: utf-8 -*-

"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


# -- stdlib --
# -- third party --
from django.contrib import admin
from django.urls import path
from graphene_django.views import GraphQLView

# -- own --
from .graphql import schema
from schema_graph.views import Schema
from .view import MessagePackGraphQLView


# -- code --
admin.site.site_header = '东方符斗祭后台'


urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql', GraphQLView.as_view(schema=schema, graphiql=True)),
    path('graphql-msgpack', MessagePackGraphQLView.as_view(schema=schema)),
    path(".dev/schema/", Schema.as_view()),
]

import os
if os.uname()[:2] == ('Linux', 'Proton'):
    from . import debug
    urlpatterns += [
        path('.debug/console/<tb>', debug.debug_page),
        path('.debug/static/<path:filename>', debug.static_files),
        path('.debug/traceback/<tb>', debug.traceback),
        path('.debug/frame/<frame>/exec', debug.frame_exec),
    ]
