"""Dependency injection container and composition root."""

# Infrastructure
from .infrastructure.repositories import (
    InMemoryCampaignRepository,
    InMemoryClickRepository,
    InMemoryAnalyticsRepository,
)
from .infrastructure.external import MockIpGeolocationService

# Domain services
from .domain.services import (
    ClickValidationService,
    CampaignValidationService,
    CampaignPerformanceService,
    CampaignLifecycleService
)

# Application handlers
from .application.handlers import CreateCampaignHandler, TrackClickHandler

# Application queries
from .application.queries import GetCampaignHandler

# Presentation
from .presentation.routes import CampaignRoutes, ClickRoutes


class Container:
    """Dependency injection container."""

    def __init__(self):
        self._singletons = {}

    def get_campaign_repository(self):
        """Get campaign repository."""
        if 'campaign_repository' not in self._singletons:
            self._singletons['campaign_repository'] = InMemoryCampaignRepository()
        return self._singletons['campaign_repository']

    def get_click_repository(self):
        """Get click repository."""
        if 'click_repository' not in self._singletons:
            self._singletons['click_repository'] = InMemoryClickRepository()
        return self._singletons['click_repository']

    def get_analytics_repository(self):
        """Get analytics repository."""
        if 'analytics_repository' not in self._singletons:
            click_repo = self.get_click_repository()
            campaign_repo = self.get_campaign_repository()
            analytics_repo = InMemoryAnalyticsRepository(
                click_repository=click_repo,
                campaign_repository=campaign_repo,
            )
            self._singletons['analytics_repository'] = analytics_repo
        return self._singletons['analytics_repository']

    def get_ip_geolocation_service(self):
        """Get IP geolocation service."""
        if 'ip_geolocation_service' not in self._singletons:
            self._singletons['ip_geolocation_service'] = MockIpGeolocationService()
        return self._singletons['ip_geolocation_service']

    def get_click_validation_service(self):
        """Get click validation service."""
        if 'click_validation_service' not in self._singletons:
            self._singletons['click_validation_service'] = ClickValidationService()
        return self._singletons['click_validation_service']

    def get_campaign_validator(self):
        """Get campaign validation service."""
        if 'campaign_validation_service' not in self._singletons:
            self._singletons['campaign_validation_service'] = CampaignValidationService()
        return self._singletons['campaign_validation_service']

    def get_campaign_performer(self):
        """Get campaign performance service."""
        if 'campaign_performance_service' not in self._singletons:
            self._singletons['campaign_performance_service'] = CampaignPerformanceService()
        return self._singletons['campaign_performance_service']

    def get_campaign_lifecycle_service(self):
        """Get campaign lifecycle service."""
        if 'campaign_lifecycle_service' not in self._singletons:
            self._singletons['campaign_lifecycle_service'] = CampaignLifecycleService()
        return self._singletons['campaign_lifecycle_service']

    def get_create_campaign_handler(self):
        """Get create campaign handler."""
        if 'create_campaign_handler' not in self._singletons:
            self._singletons['create_campaign_handler'] = CreateCampaignHandler(
                campaign_repository=self.get_campaign_repository()
            )
        return self._singletons['create_campaign_handler']

    def get_track_click_handler(self):
        """Get track click handler."""
        if 'track_click_handler' not in self._singletons:
            click_repo = self.get_click_repository()
            campaign_repo = self.get_campaign_repository()
            validation_svc = self.get_click_validation_service()

            track_click_handler = TrackClickHandler(
                click_repository=click_repo,
                campaign_repository=campaign_repo,
                click_validation_service=validation_svc,
            )
            self._singletons['track_click_handler'] = track_click_handler
        return self._singletons['track_click_handler']

    def get_get_campaign_handler(self):
        """Get campaign query handler."""
        if 'get_campaign_handler' not in self._singletons:
            self._singletons['get_campaign_handler'] = GetCampaignHandler(
                campaign_repository=self.get_campaign_repository()
            )
        return self._singletons['get_campaign_handler']

    def get_campaign_routes(self):
        """Get campaign routes."""
        if 'campaign_routes' not in self._singletons:
            create_handler = self.get_create_campaign_handler()
            get_handler = self.get_get_campaign_handler()

            campaign_routes = CampaignRoutes(
                create_campaign_handler=create_handler,
                get_campaign_handler=get_handler,
            )
            self._singletons['campaign_routes'] = campaign_routes
        return self._singletons['campaign_routes']

    def get_click_routes(self):
        """Get click routes."""
        if 'click_routes' not in self._singletons:
            self._singletons['click_routes'] = ClickRoutes(
                track_click_handler=self.get_track_click_handler(),
            )
        return self._singletons['click_routes']



# Global container instance
container = Container()
