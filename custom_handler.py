"""LiteLLM custom provider handlers for this project."""

from __future__ import annotations

from typing import Any


__all__ = ["nvidia_flux_kontext"]


class NvidiaFluxKontextHandler:
    """Placeholder handler for the NVIDIA Flux Kontext provider.

    LiteLLM expects a callable object with both sync and async image-generation
    hooks for custom providers. This stub keeps the provider importable and
    surfaces a clear error if the endpoint is invoked before a real
    implementation is wired up.
    """

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.image_generation(*args, **kwargs)

    def image_generation(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError(
            "The NVIDIA Flux Kontext custom provider handler is not implemented yet. "
            "Configure a real implementation before using this model."
        )

    async def aimage_generation(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError(
            "The NVIDIA Flux Kontext custom provider handler is not implemented yet. "
            "Configure a real implementation before using this model."
        )


nvidia_flux_kontext = NvidiaFluxKontextHandler()
