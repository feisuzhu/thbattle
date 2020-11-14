# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from django.http import HttpResponse
from django.http.response import HttpResponseBadRequest
from django.views.generic import View
from graphql import get_default_backend
from graphql.error import GraphQLError, format_error as format_graphql_error
from graphql.execution import ExecutionResult
import msgpack

# -- own --


# -- code --
class MessagePackGraphQLView(View):

    schema = None

    def __init__(self, schema):
        self.schema = self.schema or schema
        self.backend = get_default_backend()

    def make_400_message(self, msg):
        return HttpResponseBadRequest(
            content=msgpack.packb({'errors': [{"message": msg}]}),
            content_type='application/msgpack',
        )

    def post(self, request):
        content_type = self.get_content_type(request)
        if content_type != 'application/msgpack':
            return self.make_400_message('Invalid Content-Type')

        r = msgpack.unpackb(request.body)
        print(r)
        query = r.get('query')
        if not query:
            return self.make_400_message('query is missing')

        variables = r.get('variables')

        execution_result = self.execute_graphql_request(request, query, variables)

        status_code = 200
        if execution_result:
            response = {}

            if execution_result.errors:
                response["errors"] = [
                    self.format_error(e) for e in execution_result.errors
                ]

            if execution_result.invalid:
                status_code = 400
            else:
                response["data"] = msgpack.packb(execution_result.data)

            result = msgpack.packb(response)
        else:
            result = None

        return HttpResponse(
            status=status_code, content=result, content_type="application/msgpack"
        )

    def execute_graphql_request(self, context, query, variables):
        try:
            document = self.backend.document_from_string(self.schema, query)
        except Exception as e:
            return ExecutionResult(errors=[e], invalid=True)

        try:
            return document.execute(
                variable_values=variables,
                context_value=context,
            )
        except Exception as e:
            return ExecutionResult(errors=[e], invalid=True)

    @staticmethod
    def format_error(error):
        if isinstance(error, GraphQLError):
            return format_graphql_error(error)

        return {"message": str(error)}

    @staticmethod
    def get_content_type(request):
        meta = request.META
        content_type = meta.get("CONTENT_TYPE", meta.get("HTTP_CONTENT_TYPE", ""))
        return content_type.split(";", 1)[0].lower()
