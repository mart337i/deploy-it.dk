from fastapi import Request

import logging
_logger = logging.getLogger("app")

async def log_request_info(request: Request):
    _logger.debug(
        f"{request.method} request to {request.url} metadata\n"
        f"\tHeaders: {request.headers}\n"
        f"\tPath Params: {request.path_params}\n"
        f"\tQuery Params: {request.query_params}\n"
        f"\tCookies: {request.cookies}\n"
    )