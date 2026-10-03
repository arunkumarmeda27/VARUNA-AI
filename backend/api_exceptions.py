import logging

from rest_framework.exceptions import NotFound, Throttled, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        if isinstance(exc, ValidationError):
            payload = {
                "status": "ERROR",
                "message": "Invalid request.",
                "errors": response.data,
            }
        elif isinstance(exc, NotFound):
            payload = {
                "status": "ERROR",
                "message": "Requested resource was not found.",
            }
        elif isinstance(exc, Throttled):
            payload = {
                "status": "ERROR",
                "message": "Request limit exceeded.",
            }
        else:
            payload = {
                "status": "ERROR",
                "message": "Request could not be completed.",
            }
        return Response(payload, status=response.status_code, headers=response.headers)

    logger.error(
        "Unhandled API exception",
        exc_info=(type(exc), exc, exc.__traceback__),
        extra={"view": context.get("view"), "request": context.get("request")},
    )
    return Response(
        {
            "status": "ERROR",
            "message": "Request could not be completed.",
        },
        status=500,
    )