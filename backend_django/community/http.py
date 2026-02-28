from django.http import HttpRequest, JsonResponse


def _request_id(request: HttpRequest) -> str:
    return getattr(request, 'request_id', '')


def api_success(request: HttpRequest, data=None, message: str = 'ok', status: int = 200):
    return JsonResponse(
        {
            'code': 0,
            'message': message,
            'data': data,
            'requestId': _request_id(request),
        },
        status=status,
    )


def api_error(request: HttpRequest, message: str, status: int = 400, code: int | None = None):
    return JsonResponse(
        {
            'code': code if code is not None else status,
            'message': message,
            'data': None,
            'requestId': _request_id(request),
        },
        status=status,
    )
