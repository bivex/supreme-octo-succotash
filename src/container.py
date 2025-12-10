"""Dependency injection container and composition root."""

import psycopg2.pool

# Infrastructure
from .infrastructure.repositories import (
    SQLiteCampaignRepository,
    SQLiteClickRepository,
    SQLiteAnalyticsRepository,
    SQLiteWebhookRepository,
    SQLiteEventRepository,
    SQLiteConversionRepository,
    SQLitePostbackRepository,
    SQLiteGoalRepository,
    SQLiteLTVRepository,
    SQLiteRetentionRepository,
    SQLiteFormRepository,
    PostgresCampaignRepository,
    PostgresClickRepository,
    PostgresAnalyticsRepository,
    PostgresWebhookRepository,
    PostgresEventRepository,
    PostgresConversionRepository,
    PostgresPostbackRepository,
    PostgresGoalRepository,
    PostgresLandingPageRepository,
    PostgresOfferRepository,
    PostgresLTVRepository,
    PostgresRetentionRepository,
    PostgresFormRepository,
)
from .infrastructure.external import MockIpGeolocationService

# Domain services
from .domain.services import (
    ClickValidationService,
    CampaignValidationService,
    CampaignPerformanceService,
    CampaignLifecycleService
)
from .domain.services.webhook import WebhookService
from .domain.services.event import EventService
from .domain.services.conversion import ConversionService
from .domain.services.postback import PostbackService
from .domain.services.click import ClickGenerationService
from .domain.services.goal import GoalService
from .domain.services.journey import JourneyService

# Application handlers
from .application.handlers import (
    CreateCampaignHandler, UpdateCampaignHandler, PauseCampaignHandler, ResumeCampaignHandler,
    CreateLandingPageHandler, CreateOfferHandler,
    TrackClickHandler, ProcessWebhookHandler, TrackEventHandler, TrackConversionHandler,
    SendPostbackHandler, GenerateClickHandler, ManageGoalHandler, AnalyzeJourneyHandler,
    BulkClickHandler, ClickValidationHandler, FraudHandler, SystemHandler, AnalyticsHandler,
    LTVHandler, RetentionHandler, FormHandler, CohortAnalysisHandler, SegmentationHandler
)

# Application queries
from .application.queries import (
    GetCampaignHandler,
    GetCampaignAnalyticsHandler,
    GetCampaignLandingPagesHandler,
    GetCampaignOffersHandler
)

# Presentation
from .presentation.routes import CampaignRoutes, ClickRoutes, WebhookRoutes, EventRoutes, ConversionRoutes, PostbackRoutes, ClickGenerationRoutes, GoalRoutes, JourneyRoutes, LtvRoutes, FormRoutes, RetentionRoutes, BulkOperationsRoutes, FraudRoutes, SystemRoutes, AnalyticsRoutes


class Container:
    """Dependency injection container."""

    def __init__(self, settings=None):
        self._singletons = {}
        self._settings = settings

    def get_db_connection_pool(self):
        """Get PostgreSQL connection pool."""
        if 'db_connection_pool' not in self._singletons:
            self._singletons['db_connection_pool'] = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=100,
                host="localhost",
                port=5432,
                database="supreme_octosuccotash_db",
                user="app_user",
                password="app_password",
                client_encoding='utf8'
            )
        return self._singletons['db_connection_pool']

    def get_pool_stats(self):
        """Get database connection pool statistics."""
        pool = self.get_db_connection_pool()
        return {
            'minconn': getattr(pool, '_minconn', 'unknown'),
            'maxconn': getattr(pool, '_maxconn', 'unknown'),
            'used': len(getattr(pool, '_used', [])),
            'available': len(getattr(pool, '_pool', [])),
            'total_connections': len(getattr(pool, '_used', [])) + len(getattr(pool, '_pool', []))
        }

    def get_db_connection(self):
        """Get a database connection from the pool."""
        pool = self.get_db_connection_pool()
        return pool.getconn()

    def release_db_connection(self, conn):
        """Release a database connection back to the pool."""
        pool = self.get_db_connection_pool()
        pool.putconn(conn)

    def get_campaign_repository(self):
        """Get campaign repository."""
        if 'campaign_repository' not in self._singletons:
            # Try PostgreSQL first, fallback to SQLite
            try:
                self._singletons['campaign_repository'] = self.get_postgres_campaign_repository()
            except Exception:
                db_path = self._settings.database.get_sqlite_path() if self._settings else ":memory:"
                self._singletons['campaign_repository'] = SQLiteCampaignRepository(db_path)
        return self._singletons['campaign_repository']

    def get_click_repository(self):
        """Get click repository."""
        if 'click_repository' not in self._singletons:
            # Try PostgreSQL first, fallback to SQLite
            try:
                self._singletons['click_repository'] = self.get_postgres_click_repository()
            except Exception:
                db_path = self._settings.database.get_sqlite_path() if self._settings else ":memory:"
                self._singletons['click_repository'] = SQLiteClickRepository(db_path)
        return self._singletons['click_repository']

    def get_analytics_repository(self):
        """Get analytics repository."""
        if 'analytics_repository' not in self._singletons:
            # Try PostgreSQL first, fallback to SQLite
            try:
                self._singletons['analytics_repository'] = self.get_postgres_analytics_repository()
            except Exception:
                click_repo = self.get_click_repository()
                campaign_repo = self.get_campaign_repository()
                db_path = self._settings.database.get_sqlite_path() if self._settings else ":memory:"
                analytics_repo = SQLiteAnalyticsRepository(
                    click_repository=click_repo,
                    campaign_repository=campaign_repo,
                    db_path=db_path,
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

    def get_update_campaign_handler(self):
        """Get update campaign handler."""
        if 'update_campaign_handler' not in self._singletons:
            self._singletons['update_campaign_handler'] = UpdateCampaignHandler(
                campaign_repository=self.get_campaign_repository()
            )
        return self._singletons['update_campaign_handler']

    def get_pause_campaign_handler(self):
        """Get pause campaign handler."""
        if 'pause_campaign_handler' not in self._singletons:
            self._singletons['pause_campaign_handler'] = PauseCampaignHandler(
                campaign_repository=self.get_campaign_repository()
            )
        return self._singletons['pause_campaign_handler']

    def get_resume_campaign_handler(self):
        """Get resume campaign handler."""
        if 'resume_campaign_handler' not in self._singletons:
            self._singletons['resume_campaign_handler'] = ResumeCampaignHandler(
                campaign_repository=self.get_campaign_repository()
            )
        return self._singletons['resume_campaign_handler']

    def get_create_landing_page_handler(self):
        """Get create landing page handler."""
        if 'create_landing_page_handler' not in self._singletons:
            self._singletons['create_landing_page_handler'] = CreateLandingPageHandler(
                landing_page_repository=self.get_postgres_landing_page_repository()
            )
        return self._singletons['create_landing_page_handler']

    def get_create_offer_handler(self):
        """Get create offer handler."""
        if 'create_offer_handler' not in self._singletons:
            self._singletons['create_offer_handler'] = CreateOfferHandler(
                offer_repository=self.get_postgres_offer_repository()
            )
        return self._singletons['create_offer_handler']

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

    def get_get_campaign_analytics_handler(self):
        """Get campaign analytics handler."""
        if 'get_campaign_analytics_handler' not in self._singletons:
            self._singletons['get_campaign_analytics_handler'] = GetCampaignAnalyticsHandler(
                analytics_repository=self.get_postgres_analytics_repository()
            )
        return self._singletons['get_campaign_analytics_handler']

    def get_get_campaign_landing_pages_handler(self):
        """Get campaign landing pages handler."""
        if 'get_campaign_landing_pages_handler' not in self._singletons:
            self._singletons['get_campaign_landing_pages_handler'] = GetCampaignLandingPagesHandler(
                landing_page_repository=self.get_postgres_landing_page_repository()
            )
        return self._singletons['get_campaign_landing_pages_handler']

    def get_get_campaign_offers_handler(self):
        """Get campaign offers handler."""
        if 'get_campaign_offers_handler' not in self._singletons:
            self._singletons['get_campaign_offers_handler'] = GetCampaignOffersHandler(
                offer_repository=self.get_postgres_offer_repository()
            )
        return self._singletons['get_campaign_offers_handler']

    def get_campaign_routes(self):
        """Get campaign routes."""
        if 'campaign_routes' not in self._singletons:
            campaign_routes = CampaignRoutes(self)
            self._singletons['campaign_routes'] = campaign_routes
        return self._singletons['campaign_routes']

    def get_click_routes(self):
        """Get click routes."""
        if 'click_routes' not in self._singletons:
            self._singletons['click_routes'] = ClickRoutes(
                track_click_handler=self.get_track_click_handler(),
            )
        return self._singletons['click_routes']

    def get_webhook_repository(self):
        """Get webhook repository."""
        if 'webhook_repository' not in self._singletons:
            # Try PostgreSQL first, fallback to SQLite
            try:
                self._singletons['webhook_repository'] = self.get_postgres_webhook_repository()
            except Exception:
                db_path = self._settings.database.get_sqlite_path() if self._settings else ":memory:"
                self._singletons['webhook_repository'] = SQLiteWebhookRepository(db_path)
        return self._singletons['webhook_repository']

    def get_webhook_service(self):
        """Get webhook service."""
        if 'webhook_service' not in self._singletons:
            self._singletons['webhook_service'] = WebhookService()
        return self._singletons['webhook_service']

    def get_process_webhook_handler(self):
        """Get process webhook handler."""
        if 'process_webhook_handler' not in self._singletons:
            self._singletons['process_webhook_handler'] = ProcessWebhookHandler(
                webhook_repository=self.get_webhook_repository(),
                webhook_service=self.get_webhook_service()
            )
        return self._singletons['process_webhook_handler']

    def get_webhook_routes(self):
        """Get webhook routes."""
        if 'webhook_routes' not in self._singletons:
            self._singletons['webhook_routes'] = WebhookRoutes(
                process_webhook_handler=self.get_process_webhook_handler(),
            )
        return self._singletons['webhook_routes']

    def get_event_repository(self):
        """Get event repository."""
        if 'event_repository' not in self._singletons:
            # Try PostgreSQL first, fallback to SQLite
            try:
                self._singletons['event_repository'] = self.get_postgres_event_repository()
            except Exception:
                db_path = self._settings.database.get_sqlite_path() if self._settings else ":memory:"
                self._singletons['event_repository'] = SQLiteEventRepository(db_path)
        return self._singletons['event_repository']

    def get_event_service(self):
        """Get event service."""
        if 'event_service' not in self._singletons:
            self._singletons['event_service'] = EventService()
        return self._singletons['event_service']

    def get_track_event_handler(self):
        """Get track event handler."""
        if 'track_event_handler' not in self._singletons:
            self._singletons['track_event_handler'] = TrackEventHandler(
                event_repository=self.get_event_repository(),
                event_service=self.get_event_service()
            )
        return self._singletons['track_event_handler']

    def get_event_routes(self):
        """Get event routes."""
        if 'event_routes' not in self._singletons:
            self._singletons['event_routes'] = EventRoutes(
                track_event_handler=self.get_track_event_handler(),
            )
        return self._singletons['event_routes']

    def get_conversion_repository(self):
        """Get conversion repository."""
        if 'conversion_repository' not in self._singletons:
            # Try PostgreSQL first, fallback to SQLite
            try:
                self._singletons['conversion_repository'] = self.get_postgres_conversion_repository()
            except Exception:
                db_path = self._settings.database.get_sqlite_path() if self._settings else ":memory:"
                self._singletons['conversion_repository'] = SQLiteConversionRepository(db_path)
        return self._singletons['conversion_repository']

    def get_conversion_service(self):
        """Get conversion service."""
        if 'conversion_service' not in self._singletons:
            self._singletons['conversion_service'] = ConversionService(
                click_repository=self.get_click_repository()
            )
        return self._singletons['conversion_service']

    def get_track_conversion_handler(self):
        """Get track conversion handler."""
        if 'track_conversion_handler' not in self._singletons:
            self._singletons['track_conversion_handler'] = TrackConversionHandler(
                conversion_repository=self.get_conversion_repository(),
                click_repository=self.get_click_repository(),
                conversion_service=self.get_conversion_service()
            )
        return self._singletons['track_conversion_handler']

    def get_conversion_routes(self):
        """Get conversion routes."""
        if 'conversion_routes' not in self._singletons:
            self._singletons['conversion_routes'] = ConversionRoutes(
                track_conversion_handler=self.get_track_conversion_handler(),
            )
        return self._singletons['conversion_routes']

    def get_postback_repository(self):
        """Get postback repository."""
        if 'postback_repository' not in self._singletons:
            # Try PostgreSQL first, fallback to SQLite
            try:
                self._singletons['postback_repository'] = self.get_postgres_postback_repository()
            except Exception:
                db_path = self._settings.database.get_sqlite_path() if self._settings else ":memory:"
                self._singletons['postback_repository'] = SQLitePostbackRepository(db_path)
        return self._singletons['postback_repository']

    def get_postback_service(self):
        """Get postback service."""
        if 'postback_service' not in self._singletons:
            self._singletons['postback_service'] = PostbackService()
        return self._singletons['postback_service']

    def get_send_postback_handler(self):
        """Get send postback handler."""
        if 'send_postback_handler' not in self._singletons:
            self._singletons['send_postback_handler'] = SendPostbackHandler(
                postback_repository=self.get_postback_repository(),
                conversion_repository=self.get_conversion_repository(),
                postback_service=self.get_postback_service()
            )
        return self._singletons['send_postback_handler']

    def get_postback_routes(self):
        """Get postback routes."""
        if 'postback_routes' not in self._singletons:
            self._singletons['postback_routes'] = PostbackRoutes(
                send_postback_handler=self.get_send_postback_handler(),
            )
        return self._singletons['postback_routes']

    def get_click_generation_service(self):
        """Get click generation service."""
        if 'click_generation_service' not in self._singletons:
            self._singletons['click_generation_service'] = ClickGenerationService()
        return self._singletons['click_generation_service']

    def get_generate_click_handler(self):
        """Get generate click handler."""
        if 'generate_click_handler' not in self._singletons:
            self._singletons['generate_click_handler'] = GenerateClickHandler(
                click_generation_service=self.get_click_generation_service()
            )
        return self._singletons['generate_click_handler']

    def get_click_generation_routes(self):
        """Get click generation routes."""
        if 'click_generation_routes' not in self._singletons:
            self._singletons['click_generation_routes'] = ClickGenerationRoutes(
                generate_click_handler=self.get_generate_click_handler(),
            )
        return self._singletons['click_generation_routes']

    def get_goal_repository(self):
        """Get goal repository."""
        if 'goal_repository' not in self._singletons:
            # Try PostgreSQL first, fallback to SQLite
            try:
                self._singletons['goal_repository'] = self.get_postgres_goal_repository()
            except Exception:
                db_path = self._settings.database.get_sqlite_path() if self._settings else ":memory:"
                self._singletons['goal_repository'] = SQLiteGoalRepository(db_path)
        return self._singletons['goal_repository']

    def get_ltv_repository(self):
        """Get LTV repository."""
        if 'ltv_repository' not in self._singletons:
            db_path = self._settings.database.get_sqlite_path() if self._settings else ":memory:"
            self._singletons['ltv_repository'] = SQLiteLTVRepository(db_path)
        return self._singletons['ltv_repository']

    def get_retention_repository(self):
        """Get retention repository."""
        if 'retention_repository' not in self._singletons:
            # Try PostgreSQL first, fallback to SQLite
            try:
                self._singletons['retention_repository'] = self.get_postgres_retention_repository()
            except Exception:
                db_path = self._settings.database.get_sqlite_path() if self._settings else ":memory:"
                self._singletons['retention_repository'] = SQLiteRetentionRepository(db_path)
        return self._singletons['retention_repository']

    def get_form_repository(self):
        """Get form repository."""
        if 'form_repository' not in self._singletons:
            # Try PostgreSQL first, fallback to SQLite
            try:
                self._singletons['form_repository'] = self.get_postgres_form_repository()
            except Exception:
                db_path = self._settings.database.get_sqlite_path() if self._settings else ":memory:"
                self._singletons['form_repository'] = SQLiteFormRepository(db_path)
        return self._singletons['form_repository']

    def get_postgres_campaign_repository(self):
        """Get PostgreSQL campaign repository."""
        if 'postgres_campaign_repository' not in self._singletons:
            self._singletons['postgres_campaign_repository'] = PostgresCampaignRepository(container=self)
        return self._singletons['postgres_campaign_repository']

    def get_postgres_click_repository(self):
        """Get PostgreSQL click repository."""
        if 'postgres_click_repository' not in self._singletons:
            self._singletons['postgres_click_repository'] = PostgresClickRepository(container=self)
        return self._singletons['postgres_click_repository']

    def get_postgres_analytics_repository(self):
        """Get PostgreSQL analytics repository."""
        if 'postgres_analytics_repository' not in self._singletons:
            self._singletons['postgres_analytics_repository'] = PostgresAnalyticsRepository(
                click_repository=self.get_postgres_click_repository(),
                campaign_repository=self.get_postgres_campaign_repository(),
                container=self
            )
        return self._singletons['postgres_analytics_repository']

    def get_postgres_webhook_repository(self):
        """Get PostgreSQL webhook repository."""
        if 'postgres_webhook_repository' not in self._singletons:
            self._singletons['postgres_webhook_repository'] = PostgresWebhookRepository(container=self)
        return self._singletons['postgres_webhook_repository']

    def get_postgres_event_repository(self):
        """Get PostgreSQL event repository."""
        if 'postgres_event_repository' not in self._singletons:
            self._singletons['postgres_event_repository'] = PostgresEventRepository(container=self)
        return self._singletons['postgres_event_repository']

    def get_postgres_conversion_repository(self):
        """Get PostgreSQL conversion repository."""
        if 'postgres_conversion_repository' not in self._singletons:
            self._singletons['postgres_conversion_repository'] = PostgresConversionRepository(container=self)
        return self._singletons['postgres_conversion_repository']

    def get_postgres_postback_repository(self):
        """Get PostgreSQL postback repository."""
        if 'postgres_postback_repository' not in self._singletons:
            self._singletons['postgres_postback_repository'] = PostgresPostbackRepository(container=self)
        return self._singletons['postgres_postback_repository']

    def get_postgres_goal_repository(self):
        """Get PostgreSQL goal repository."""
        if 'postgres_goal_repository' not in self._singletons:
            self._singletons['postgres_goal_repository'] = PostgresGoalRepository(container=self)
        return self._singletons['postgres_goal_repository']

    def get_postgres_ltv_repository(self):
        """Get PostgreSQL LTV repository."""
        if 'postgres_ltv_repository' not in self._singletons:
            self._singletons['postgres_ltv_repository'] = PostgresLTVRepository(container=self)
        return self._singletons['postgres_ltv_repository']

    def get_postgres_retention_repository(self):
        """Get PostgreSQL retention repository."""
        if 'postgres_retention_repository' not in self._singletons:
            self._singletons['postgres_retention_repository'] = PostgresRetentionRepository(container=self)
        return self._singletons['postgres_retention_repository']

    def get_postgres_form_repository(self):
        """Get PostgreSQL form repository."""
        if 'postgres_form_repository' not in self._singletons:
            self._singletons['postgres_form_repository'] = PostgresFormRepository(container=self)
        return self._singletons['postgres_form_repository']

    def get_postgres_landing_page_repository(self):
        """Get PostgreSQL landing page repository."""
        if 'postgres_landing_page_repository' not in self._singletons:
            self._singletons['postgres_landing_page_repository'] = PostgresLandingPageRepository(container=self)
        return self._singletons['postgres_landing_page_repository']

    def get_postgres_offer_repository(self):
        """Get PostgreSQL offer repository."""
        if 'postgres_offer_repository' not in self._singletons:
            self._singletons['postgres_offer_repository'] = PostgresOfferRepository(container=self)
        return self._singletons['postgres_offer_repository']

    def get_landing_page_repository(self):
        """Get landing page repository."""
        if 'landing_page_repository' not in self._singletons:
            # Try PostgreSQL first, fallback to SQLite
            try:
                self._singletons['landing_page_repository'] = self.get_postgres_landing_page_repository()
            except Exception:
                db_path = self._settings.database.get_sqlite_path() if self._settings else ":memory:"
                self._singletons['landing_page_repository'] = SQLiteLandingPageRepository(db_path)
        return self._singletons['landing_page_repository']

    def get_offer_repository(self):
        """Get offer repository."""
        if 'offer_repository' not in self._singletons:
            # Try PostgreSQL first, fallback to SQLite
            try:
                self._singletons['offer_repository'] = self.get_postgres_offer_repository()
            except Exception:
                db_path = self._settings.database.get_sqlite_path() if self._settings else ":memory:"
                self._singletons['offer_repository'] = SQLiteOfferRepository(db_path)
        return self._singletons['offer_repository']

    def get_goal_service(self):
        """Get goal service."""
        if 'goal_service' not in self._singletons:
            self._singletons['goal_service'] = GoalService(
                goal_repository=self.get_goal_repository()
            )
        return self._singletons['goal_service']

    def get_manage_goal_handler(self):
        """Get manage goal handler."""
        if 'manage_goal_handler' not in self._singletons:
            self._singletons['manage_goal_handler'] = ManageGoalHandler(
                goal_repository=self.get_goal_repository(),
                goal_service=self.get_goal_service()
            )
        return self._singletons['manage_goal_handler']

    def get_goal_routes(self):
        """Get goal routes."""
        if 'goal_routes' not in self._singletons:
            self._singletons['goal_routes'] = GoalRoutes(
                manage_goal_handler=self.get_manage_goal_handler(),
            )
        return self._singletons['goal_routes']

    def get_journey_service(self):
        """Get journey service."""
        if 'journey_service' not in self._singletons:
            self._singletons['journey_service'] = JourneyService()
        return self._singletons['journey_service']

    def get_analyze_journey_handler(self):
        """Get analyze journey handler."""
        if 'analyze_journey_handler' not in self._singletons:
            self._singletons['analyze_journey_handler'] = AnalyzeJourneyHandler(
                journey_service=self.get_journey_service()
            )
        return self._singletons['analyze_journey_handler']

    def get_journey_routes(self):
        """Get journey routes."""
        if 'journey_routes' not in self._singletons:
            self._singletons['journey_routes'] = JourneyRoutes(
                analyze_journey_handler=self.get_analyze_journey_handler(),
            )
        return self._singletons['journey_routes']

    def get_ltv_routes(self):
        """Get LTV routes."""
        if 'ltv_routes' not in self._singletons:
            self._singletons['ltv_routes'] = LtvRoutes(
                ltv_handler=self.get_ltv_handler()
            )
        return self._singletons['ltv_routes']

    def get_form_routes(self):
        """Get form routes."""
        if 'form_routes' not in self._singletons:
            self._singletons['form_routes'] = FormRoutes(
                form_handler=self.get_form_handler()
            )
        return self._singletons['form_routes']

    def get_retention_routes(self):
        """Get retention routes."""
        if 'retention_routes' not in self._singletons:
            self._singletons['retention_routes'] = RetentionRoutes(
                retention_handler=self.get_retention_handler()
            )
        return self._singletons['retention_routes']

    def get_bulk_click_handler(self):
        """Get bulk click handler."""
        if 'bulk_click_handler' not in self._singletons:
            self._singletons['bulk_click_handler'] = BulkClickHandler()
        return self._singletons['bulk_click_handler']

    def get_click_validation_handler(self):
        """Get click validation handler."""
        if 'click_validation_handler' not in self._singletons:
            self._singletons['click_validation_handler'] = ClickValidationHandler()
        return self._singletons['click_validation_handler']

    def get_bulk_operations_routes(self):
        """Get bulk operations routes."""
        if 'bulk_operations_routes' not in self._singletons:
            bulk_handler = self.get_bulk_click_handler()
            validation_handler = self.get_click_validation_handler()
            self._singletons['bulk_operations_routes'] = BulkOperationsRoutes(bulk_handler, validation_handler)
        return self._singletons['bulk_operations_routes']

    def get_fraud_handler(self):
        """Get fraud handler."""
        if 'fraud_handler' not in self._singletons:
            self._singletons['fraud_handler'] = FraudHandler()
        return self._singletons['fraud_handler']

    def get_fraud_routes(self):
        """Get fraud routes."""
        if 'fraud_routes' not in self._singletons:
            self._singletons['fraud_routes'] = FraudRoutes(self.get_fraud_handler())
        return self._singletons['fraud_routes']

    def get_system_handler(self):
        """Get system handler."""
        if 'system_handler' not in self._singletons:
            self._singletons['system_handler'] = SystemHandler()
        return self._singletons['system_handler']

    def get_system_routes(self):
        """Get system routes."""
        if 'system_routes' not in self._singletons:
            self._singletons['system_routes'] = SystemRoutes(self.get_system_handler())
        return self._singletons['system_routes']

    def get_analytics_handler(self):
        """Get analytics handler."""
        if 'analytics_handler' not in self._singletons:
            self._singletons['analytics_handler'] = AnalyticsHandler()
        return self._singletons['analytics_handler']

    def get_ltv_handler(self):
        """Get LTV handler."""
        if 'ltv_handler' not in self._singletons:
            # Use PostgreSQL repository for production
            self._singletons['ltv_handler'] = LTVHandler(
                ltv_repository=self.get_postgres_ltv_repository()
            )
        return self._singletons['ltv_handler']

    def get_retention_handler(self):
        """Get retention handler."""
        if 'retention_handler' not in self._singletons:
            self._singletons['retention_handler'] = RetentionHandler(
                retention_repository=self.get_postgres_retention_repository(),
                click_repository=self.get_click_repository(),
                conversion_repository=self.get_conversion_repository()
            )
        return self._singletons['retention_handler']

    def get_form_handler(self):
        """Get form handler."""
        if 'form_handler' not in self._singletons:
            self._singletons['form_handler'] = FormHandler(
                form_repository=self.get_postgres_form_repository()
            )
        return self._singletons['form_handler']

    def get_cohort_analysis_handler(self):
        """Get cohort analysis handler."""
        if 'cohort_analysis_handler' not in self._singletons:
            self._singletons['cohort_analysis_handler'] = CohortAnalysisHandler(
                ltv_repository=self.get_postgres_ltv_repository()
            )
        return self._singletons['cohort_analysis_handler']

    def get_segmentation_handler(self):
        """Get segmentation handler."""
        if 'segmentation_handler' not in self._singletons:
            self._singletons['segmentation_handler'] = SegmentationHandler(
                retention_repository=self.get_postgres_retention_repository(),
                click_repository=self.get_click_repository(),
                conversion_repository=self.get_conversion_repository()
            )
        return self._singletons['segmentation_handler']

    def get_analytics_routes(self):
        """Get analytics routes."""
        if 'analytics_routes' not in self._singletons:
            self._singletons['analytics_routes'] = AnalyticsRoutes(self.get_analytics_handler())
        return self._singletons['analytics_routes']



# Global container instance
from .config.settings import settings
container = Container(settings)
