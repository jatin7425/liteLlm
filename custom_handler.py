"""LiteLLM custom provider handlers for this project."""

from typing import Any


__all__ = ["nvidia_flux_kontext"]


def nvidia_flux_kontext(*args: Any, **kwargs: Any) -> Any:
    """Placeholder handler for the NVIDIA Flux Kontext custom provider.

    The import error was caused by the configured provider map pointing to a
    module symbol that did not exist. This stub keeps startup from failing so
    the application can be launched and the real provider implementation can be
    wired in later if needed.
    """
    raise RuntimeError(
        "The NVIDIA Flux Kontext custom provider handler is not implemented yet. "
        "Configure a real implementation before using this model."
    )
