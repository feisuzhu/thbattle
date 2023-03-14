# -*- coding: utf-8 -*-

# -- stdlib --
import json

# -- third party --
from django.http import HttpResponse
from django.http.response import HttpResponseBadRequest
from django.views.generic import View
from graphql import parse, validate
from graphql.error import GraphQLError
from graphql.execution import ExecutionResult
import msgpack

# -- own --


# -- code --
class HttpError(Exception):
    def __init__(self, response, *args, **kwargs):
        self.response = response
        self.message = message = json.dumps(msgpack.unpackb(response.content))
        super(HttpError, self).__init__(message, *args, **kwargs)


class MessagePackGraphQLView(View):
    schema = None

    def __init__(self, schema):
        self.schema = self.schema or schema

    def raise400(self, msg):
        raise HttpError(HttpResponseBadRequest(
            content=msgpack.packb({'errors': [{"message": msg}]}),
            content_type='application/msgpack',
        ))

    def post(self, request):
        try:
            data = self.parse_body(request)
            result, status_code = self.get_response(request, data)
            return HttpResponse(
                status=status_code, content=result, content_type="application/msgpack"
            )

        except HttpError as e:
            return e.response

    def get_response(self, request, data):
        query = data.get("query")
        variables = data.get("variables")
        strip = data.get('strip')

        execution_result = self.execute_graphql_request(request, data, query, variables)

        status_code = 200
        if execution_result:
            response = {}

            if execution_result.errors:
                response["errors"] = [
                    self.format_error(e) for e in execution_result.errors
                ]

            if execution_result.errors and any(
                not getattr(e, "path", None) for e in execution_result.errors
            ):
                status_code = 400
            else:
                data = execution_result.data
                if strip:
                    fields = strip.split('.')
                    for f in fields:
                        if data is None:
                            break
                        if not isinstance(data, dict):
                            data = None
                            break

                        data = data.get(f)

                response["data"] = data

            result = msgpack.packb(response)
        else:
            result = None

        return result, status_code

    def parse_body(self, request):
        content_type = self.get_content_type(request)

        if content_type != "application/msgpack":
            self.raise400('Invalid Content-Type')

        return msgpack.unpackb(request.body)

    def execute_graphql_request(self, request, data, query, variables):
        query or self.raise400("Must provide query string.")

        try:
            document = parse(query)
        except Exception as e:
            return ExecutionResult(errors=[e])

        validation_errors = validate(self.schema.graphql_schema, document)
        if validation_errors:
            return ExecutionResult(data=None, errors=validation_errors)

        try:
            options = {
                "source": query,
                "root_value": None,
                "variable_values": variables,
                "operation_name": None,
                "context_value": request,
                "middleware": None,
            }
            return self.schema.execute(**options)
        except Exception as e:
            return ExecutionResult(errors=[e])

    @staticmethod
    def format_error(error):
        if isinstance(error, GraphQLError):
            return error.formatted

        return {"message": str(error)}

    @staticmethod
    def get_content_type(request):
        meta = request.META
        content_type = meta.get("CONTENT_TYPE", meta.get("HTTP_CONTENT_TYPE", ""))
        return content_type.split(";", 1)[0].lower()
