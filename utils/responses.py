import json
import time
from email.utils import formatdate
from fastapi.responses import Response

def current_date_header() -> str:
    """生成符合 GMT 要求的日期头"""
    return formatdate(timeval=None, localtime=False, usegmt=True)

def fixed_json_response(data: dict) -> Response:
    """
    返回标准 JSON 响应，带固定长度的 Content-Length。
    用于普通 JSON 响应。
    """
    body = json.dumps(data)
    headers = {
        "server": "nginx/1.24.0",
        "date": current_date_header(),
        "content-type": "application/json",
        "content-length": str(len(body.encode("utf-8"))),
        "connection": "keep-alive"
    }
    return Response(
        content=body,
        headers=headers,
        media_type="application/json",
        status_code=200
    )

def chunked_response(data: dict) -> Response:
    """
    返回使用 Transfer-Encoding: chunked 的响应。
    注意 chunk 长度按十六进制表示。
    """
    body = json.dumps(data)
    chunked = f"{hex(len(body))[2:]}\r\n{body}\r\n0\r\n\r\n"
    headers = {
        "server": "nginx/1.24.0",
        "date": current_date_header(),
        "content-type": "application/json",
        "transfer-encoding": "chunked",
        "connection": "keep-alive"
    }
    return Response(
        content=chunked,
        headers=headers,
        media_type="application/json",
        status_code=200
    )