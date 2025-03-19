"""Daytona Workspace."""

import os
import typing as t
from dataclasses import dataclass

from daytona_sdk import DaytonaConfig

from composio.exceptions import ComposioSDKError
from composio.tools.env.base import RemoteWorkspace, WorkspaceConfigType


try:
    from daytona_sdk import (
        Daytona,
        CodeLanguage as SandboxCodeLanguage,
        SandboxTargetRegion as DaytonaSandboxTargetRegion,
        SandboxResources as DaytonaSandboxResources,
        CreateSandboxParams as CreateDaytonaSandboxParams,
    )

    DAYTONA_INSTALLED = True
except ImportError:
    Sandbox = t.Any
    DAYTONA_INSTALLED = False

TOOLSERVER_PORT = 8000

@dataclass
class Config(WorkspaceConfigType):
    """Daytona workspace configuration."""

    api_key: t.Optional[str] = None
    """Daytona API Key."""

    language: t.Optional[SandboxCodeLanguage] = None
    """Programming language for the Daytona sandbox."""

    id: t.Optional[str] = None
    """Custom identifier for the Daytona sandbox. If not provided, a random ID will be generated."""

    name: t.Optional[str] = None
    """Display name for the Daytona sandbox. Defaults to the sandbox ID if not provided."""

    image: t.Optional[str] = None
    """Custom Docker image to use for the Daytona sandbox."""

    env_vars: t.Optional[t.Dict[str, str]] = None
    """Environment variables to set in the Daytona sandbox."""

    labels: t.Optional[t.Dict[str, str]] = None
    """Custom labels for the Daytona sandbox."""

    public: t.Optional[bool] = None
    """Whether the Daytona sandbox should be public."""

    target: t.Optional[DaytonaSandboxTargetRegion] = None
    """Target location for the Daytona sandbox."""

    resources: t.Optional[DaytonaSandboxResources] = None
    """Resource configuration for the Daytona sandbox."""

    auto_stop_interval: t.Optional[int] = None
    """Interval in minutes after which the Daytona sandbox will automatically stop if no event occurs during that time. Default is 15 minutes. 0 means no auto-stop."""

class DaytonaWorkspace(RemoteWorkspace):
    """Create and manage Daytona workspace."""

    def __init__(self, config: Config):
        """Initialize Daytona workspace."""
        if not DAYTONA_INSTALLED:
            raise ComposioSDKError(
                "`daytona` is required to use daytona workspace, "
                "run `pip3 install composio-core[daytona]` or "
                "`pip3 install daytona-sdk` to install",
            )

        super().__init__(config=config)

        self.daytona = Daytona(config=DaytonaConfig(
            api_key=config.api_key, # type: ignore (will be fixed in next version of daytona-sdk)
            server_url="https://app.daytona.io/api",
         ))
        self.daytona_create_sandbox_params = CreateDaytonaSandboxParams(
            language=config.language, # type: ignore (will be fixed in next version of daytona-sdk)
            id=config.id,
            name=config.name,
            image=config.image,
            env_vars=config.env_vars,
            labels=config.labels,
            public=config.public,
            target=config.target,
            resources=config.resources,
            auto_stop_interval=config.auto_stop_interval,
        )


    def setup(self) -> None:
        """Setup workspace."""

        self.daytona_sandbox = self.daytona.create(params=self.daytona_create_sandbox_params)
        self.url = self.url = f"{self.daytona.server_url}/toolbox/{self.daytona_sandbox.id}/toolbox"
        self.host = self.daytona_sandbox.get_preview_link(TOOLSERVER_PORT)
        self.ports = []
        self._wait()

    def _wait(self) -> None:
        """Wait for the workspace to be ready."""

        timeout = float(os.environ.get("WORKSPACE_WAIT_TIMEOUT", 60.0))
        self.daytona_sandbox.wait_for_sandbox_start(timeout)

    def teardown(self) -> None:
        """Teardown Daytona workspace."""

        super().teardown()
        if hasattr(self, "sandbox") and self.daytona_sandbox is not None:
            self.daytona.remove(self.daytona_sandbox)
