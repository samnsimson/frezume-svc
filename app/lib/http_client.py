import httpx
import logging
from typing import Any, Dict, Optional, Type, TypeVar, Union
from fastapi import HTTPException

T = TypeVar("T")


class HttpClient:
    def __init__(self, base_url: Optional[str] = None, default_headers: Optional[Dict[str, str]] = None, timeout: float = 30.0):
        self.base_url = base_url
        self.default_headers = default_headers or {}
        self.timeout = timeout

    def _parse_response(self, data: Any, response_type: Type[T]) -> T:
        if hasattr(response_type, 'model_validate'): return response_type.model_validate(data)
        elif hasattr(response_type, 'parse_obj'): return response_type.parse_obj(data)
        elif response_type in (dict, list, str, int, float, bool):
            if not isinstance(data, response_type): raise ValueError(f"Expected {response_type.__name__}, got {type(data).__name__}")
            return data
        elif isinstance(response_type, type):
            if isinstance(data, dict):
                try: return response_type(**data)
                except TypeError: return response_type(data)
            else: return response_type(data)
        return data

    async def _make_request(self, method: str, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, data: Optional[Union[str, bytes, Dict[str, Any]]] = None, files: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None, **kwargs) -> httpx.Response:
        full_url = url if not self.base_url or url.startswith("http") else f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"
        merged_headers = {**self.default_headers, **(headers or {})}
        request_timeout = timeout if timeout is not None else self.timeout
        try:
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                return await client.request(method=method, url=full_url, headers=merged_headers, params=params, json=json, data=data, files=files, **kwargs)
        except httpx.TimeoutException as e:
            logging.error(f"Request timeout: {method} {full_url}")
            raise HTTPException(status_code=504, detail=f"Request timeout: {str(e)}")
        except httpx.RequestError as e:
            logging.error(f"Request error: {method} {full_url} - {str(e)}")
            raise HTTPException(status_code=503, detail=f"Request failed: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error: {method} {full_url} - {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    async def get(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None, **kwargs) -> httpx.Response:
        return await self._make_request("GET", url, headers=headers, params=params, timeout=timeout, **kwargs)

    async def post(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, data: Optional[Union[str, bytes, Dict[str, Any]]] = None, files: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None, **kwargs) -> httpx.Response:
        return await self._make_request("POST", url, headers=headers, params=params, json=json, data=data, files=files, timeout=timeout, **kwargs)

    async def put(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, data: Optional[Union[str, bytes, Dict[str, Any]]] = None, files: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None, **kwargs) -> httpx.Response:
        return await self._make_request("PUT", url, headers=headers, params=params, json=json, data=data, files=files, timeout=timeout, **kwargs)

    async def patch(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, data: Optional[Union[str, bytes, Dict[str, Any]]] = None, timeout: Optional[float] = None, **kwargs) -> httpx.Response:
        return await self._make_request("PATCH", url, headers=headers, params=params, json=json, data=data, timeout=timeout, **kwargs)

    async def delete(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None, **kwargs) -> httpx.Response:
        return await self._make_request("DELETE", url, headers=headers, params=params, timeout=timeout, **kwargs)

    async def get_json(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None, **kwargs) -> Any:
        response = await self.get(url, headers=headers, params=params, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    async def post_json(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, data: Optional[Union[str, bytes, Dict[str, Any]]] = None, timeout: Optional[float] = None, **kwargs) -> Any:
        response = await self.post(url, headers=headers, params=params, json=json, data=data, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    async def put_json(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, data: Optional[Union[str, bytes, Dict[str, Any]]] = None, timeout: Optional[float] = None, **kwargs) -> Any:
        response = await self.put(url, headers=headers, params=params, json=json, data=data, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    async def patch_json(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, data: Optional[Union[str, bytes, Dict[str, Any]]] = None, timeout: Optional[float] = None, **kwargs) -> Any:
        response = await self.patch(url, headers=headers, params=params, json=json, data=data, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    async def delete_json(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None, **kwargs) -> Any:
        response = await self.delete(url, headers=headers, params=params, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    async def get_json_typed(self, url: str, response_type: Type[T], headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None, **kwargs) -> T:
        response = await self.get(url, headers=headers, params=params, timeout=timeout, **kwargs)
        response.raise_for_status()
        return self._parse_response(response.json(), response_type)

    async def post_json_typed(self, url: str, response_type: Type[T], headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, data: Optional[Union[str, bytes, Dict[str, Any]]] = None, timeout: Optional[float] = None, **kwargs) -> T:
        response = await self.post(url, headers=headers, params=params, json=json, data=data, timeout=timeout, **kwargs)
        response.raise_for_status()
        return self._parse_response(response.json(), response_type)

    async def put_json_typed(self, url: str, response_type: Type[T], headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, data: Optional[Union[str, bytes, Dict[str, Any]]] = None, timeout: Optional[float] = None, **kwargs) -> T:
        response = await self.put(url, headers=headers, params=params, json=json, data=data, timeout=timeout, **kwargs)
        response.raise_for_status()
        return self._parse_response(response.json(), response_type)

    async def patch_json_typed(self, url: str, response_type: Type[T], headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, data: Optional[Union[str, bytes, Dict[str, Any]]] = None, timeout: Optional[float] = None, **kwargs) -> T:
        response = await self.patch(url, headers=headers, params=params, json=json, data=data, timeout=timeout, **kwargs)
        response.raise_for_status()
        return self._parse_response(response.json(), response_type)

    async def delete_json_typed(self, url: str, response_type: Type[T], headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None, **kwargs) -> T:
        response = await self.delete(url, headers=headers, params=params, timeout=timeout, **kwargs)
        response.raise_for_status()
        return self._parse_response(response.json(), response_type)
