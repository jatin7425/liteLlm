"""LiteLLM custom provider handlers for this project."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Optional, Tuple

import httpx

from litellm.types.utils import ImageObject, ImageResponse

__all__ = ["nvidia_flux_kontext"]

NVIDIA_GENAI_BASE_URL = "https://ai.api.nvidia.com/v1/genai"
NVIDIA_STATUS_BASE_URL = "https://ai.api.nvidia.com/v1/status"
POLL_INTERVAL_SECONDS = 1.0
MAX_POLL_SECONDS = 180.0


class NvidiaFluxKontextHandler:
    """Handler for NVIDIA-hosted Black Forest Labs FLUX.1 Kontext models.

    Forwards image requests to NVIDIA's `genai` function API
    (https://ai.api.nvidia.com/v1/genai/<model>). NVIDIA's cloud functions can
    reply synchronously (200) or asynchronously (202 + `NVCF-REQID` header,
    which must be polled at /v1/status/<req-id>) - both paths are handled here.
    """

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.image_generation(*args, **kwargs)

    def _build_request(
        self, model: str, prompt: str, optional_params: dict
    ) -> Tuple[str, dict]:
        # litellm has already stripped the "nvidia-flux-kontext/" provider
        # prefix by the time `model` reaches this handler, leaving e.g.
        # "black-forest-labs/flux.1-kontext-dev".
        url = f"{NVIDIA_GENAI_BASE_URL}/{model}"
        payload = {"prompt": prompt, **optional_params}
        return url, payload

    def _headers(self, api_key: Optional[str]) -> dict:
        if not api_key:
            raise ValueError(
                "An NVIDIA NIM API key is required for the nvidia-flux-kontext model."
            )
        return {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _extract_b64_image(self, data: dict) -> str:
        if data.get("artifacts"):
            return data["artifacts"][0]["base64"]
        if data.get("data"):
            return data["data"][0]["b64_json"]
        if isinstance(data.get("image"), str):
            image = data["image"]
            return image.split(",", 1)[1] if image.startswith("data:") else image
        if data.get("images"):
            image = data["images"][0]
            if isinstance(image, str) and image.startswith("data:"):
                return image.split(",", 1)[1]
            return image
        raise ValueError(
            "Unrecognized NVIDIA Flux Kontext response shape "
            f"(keys={list(data.keys())}); update "
            "NvidiaFluxKontextHandler._extract_b64_image() to match this "
            f"payload: {data}"
        )

    def _to_image_response(
        self, model_response: ImageResponse, b64_image: str
    ) -> ImageResponse:
        model_response.data = [ImageObject(b64_json=b64_image)]
        return model_response

    def _poll_sync(
        self, client: httpx.Client, req_id: str, headers: dict
    ) -> httpx.Response:
        status_url = f"{NVIDIA_STATUS_BASE_URL}/{req_id}"
        deadline = time.monotonic() + MAX_POLL_SECONDS
        while time.monotonic() < deadline:
            response = client.get(status_url, headers=headers)
            if response.status_code != 202:
                return response
            time.sleep(POLL_INTERVAL_SECONDS)
        raise TimeoutError(
            f"NVIDIA Flux Kontext request {req_id} did not complete within "
            f"{MAX_POLL_SECONDS}s"
        )

    async def _poll_async(
        self, client: httpx.AsyncClient, req_id: str, headers: dict
    ) -> httpx.Response:
        status_url = f"{NVIDIA_STATUS_BASE_URL}/{req_id}"
        deadline = time.monotonic() + MAX_POLL_SECONDS
        while time.monotonic() < deadline:
            response = await client.get(status_url, headers=headers)
            if response.status_code != 202:
                return response
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
        raise TimeoutError(
            f"NVIDIA Flux Kontext request {req_id} did not complete within "
            f"{MAX_POLL_SECONDS}s"
        )

    def image_generation(
        self,
        model: str,
        prompt: str,
        api_key: Optional[str],
        api_base: Optional[str],
        model_response: ImageResponse,
        optional_params: dict,
        logging_obj: Any,
        timeout: Optional[float] = None,
        client: Optional[httpx.Client] = None,
        **kwargs: Any,
    ) -> ImageResponse:
        url, payload = self._build_request(model, prompt, optional_params)
        headers = self._headers(api_key)
        http_client = client or httpx.Client()
        try:
            response = http_client.post(
                url, headers=headers, json=payload, timeout=timeout
            )
            if response.status_code == 202:
                req_id = response.headers.get("NVCF-REQID")
                if not req_id:
                    raise ValueError(
                        "NVIDIA returned 202 Accepted without an NVCF-REQID "
                        "header to poll."
                    )
                response = self._poll_sync(http_client, req_id, headers)
            response.raise_for_status()
        finally:
            if client is None:
                http_client.close()

        b64_image = self._extract_b64_image(response.json())
        return self._to_image_response(model_response, b64_image)

    async def aimage_generation(
        self,
        model: str,
        prompt: str,
        model_response: ImageResponse,
        api_key: Optional[str],
        api_base: Optional[str],
        optional_params: dict,
        logging_obj: Any,
        timeout: Optional[float] = None,
        client: Optional[httpx.AsyncClient] = None,
        **kwargs: Any,
    ) -> ImageResponse:
        url, payload = self._build_request(model, prompt, optional_params)
        headers = self._headers(api_key)
        http_client = client or httpx.AsyncClient()
        try:
            response = await http_client.post(
                url, headers=headers, json=payload, timeout=timeout
            )
            if response.status_code == 202:
                req_id = response.headers.get("NVCF-REQID")
                if not req_id:
                    raise ValueError(
                        "NVIDIA returned 202 Accepted without an NVCF-REQID "
                        "header to poll."
                    )
                response = await self._poll_async(http_client, req_id, headers)
            response.raise_for_status()
        finally:
            if client is None:
                await http_client.aclose()

        b64_image = self._extract_b64_image(response.json())
        return self._to_image_response(model_response, b64_image)


nvidia_flux_kontext = NvidiaFluxKontextHandler()
