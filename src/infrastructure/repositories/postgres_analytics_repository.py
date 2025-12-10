"""PostgreSQL analytics repository implementation."""

import psycopg2
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, date

from ...domain.value_objects import Analytics
from ...domain.repositories.analytics_repository import AnalyticsRepository
from ...domain.repositories.click_repository import ClickRepository
from ...domain.repositories.campaign_repository import CampaignRepository
from ...domain.value_objects import Money


class PostgresAnalyticsRepository(AnalyticsRepository):
    """PostgreSQL implementation of AnalyticsRepository."""

    def __init__(self,
                 click_repository: ClickRepository,
                 campaign_repository: CampaignRepository,
                 host: str = "localhost", port: int = 5432, database: str = "supreme_octosuccotash_db",
                 user: str = "app_user", password: str = "app_password"):
        self._click_repository = click_repository
        self._campaign_repository = campaign_repository
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password,
            'client_encoding': 'utf8'
        }
        self._connection = None
        self._initialize_db()

    def _get_connection(self):
        """Get database connection."""
        if self._connection is None:
            self._connection = psycopg2.connect(**self.connection_params)
        return self._connection

    def _initialize_db(self) -> None:
        """Initialize database schema for analytics caching."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create analytics cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_cache (
                cache_key TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                granularity TEXT NOT NULL,
                clicks INTEGER DEFAULT 0,
                unique_clicks INTEGER DEFAULT 0,
                conversions INTEGER DEFAULT 0,
                revenue_amount DECIMAL(10,2) DEFAULT 0.0,
                revenue_currency TEXT DEFAULT 'USD',
                cost_amount DECIMAL(10,2) DEFAULT 0.0,
                cost_currency TEXT DEFAULT 'USD',
                ctr DECIMAL(5,4) DEFAULT 0.0,
                cr DECIMAL(5,4) DEFAULT 0.0,
                epc_amount DECIMAL(10,2) DEFAULT 0.0,
                epc_currency TEXT DEFAULT 'USD',
                roi DECIMAL(10,4) DEFAULT 0.0,
                breakdowns JSONB,
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL
            )
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_campaign_id ON analytics_cache(campaign_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_cache_key ON analytics_cache(cache_key)")

        conn.commit()

    def get_campaign_analytics(self, campaign_id: str, start_date: date,
                              end_date: date, granularity: str = "day") -> Analytics:
        """Get analytics for a campaign within date range."""
        # Check cache first
        cached_analytics = self.get_cached_analytics(campaign_id, start_date, end_date)
        if cached_analytics:
            return cached_analytics

        # Get clicks in date range
        clicks = self._click_repository.get_clicks_in_date_range(
            campaign_id, start_date, end_date
        )

        # Calculate metrics
        valid_clicks = [c for c in clicks if c.is_valid]
        conversions = [c for c in clicks if c.has_conversion]

        total_clicks = len(valid_clicks)
        total_conversions = len(conversions)

        # Get campaign for cost/revenue calculations
        from ...domain.value_objects import CampaignId
        campaign = self._campaign_repository.find_by_id(CampaignId.from_string(campaign_id))

        # Calculate financial metrics
        currency = campaign.payout.currency if campaign and campaign.payout else "USD"

        # Simplified cost calculation (would need actual cost data)
        cost_per_click = 0.50  # Placeholder
        cost_amount = total_clicks * cost_per_click
        cost = Money.from_float(cost_amount, currency)

        # Calculate revenue from conversions
        payout_amount = float(campaign.payout.amount) if campaign and campaign.payout else 0.0
        revenue_amount = total_conversions * payout_amount
        revenue = Money.from_float(revenue_amount, currency)

        # Calculate rates
        ctr = (total_clicks / max(total_clicks, 1)) if total_clicks > 0 else 0.0
        cr = (total_conversions / total_clicks) if total_clicks > 0 else 0.0

        # EPC (Earnings Per Click)
        epc_amount = revenue_amount / total_clicks if total_clicks > 0 else 0.0
        epc = Money.from_float(epc_amount, currency)

        # ROI
        cost_float = float(cost.amount)
        roi = ((revenue_amount - cost_float) / cost_float) if cost_float > 0 else 0.0

        # Create analytics object
        analytics = Analytics(
            campaign_id=campaign_id,
            time_range={
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'granularity': granularity
            },
            clicks=total_clicks,
            unique_clicks=total_clicks,  # Simplified - assuming all clicks are unique
            conversions=total_conversions,
            revenue=revenue,
            cost=cost,
            ctr=ctr,
            cr=cr,
            epc=epc,
            roi=roi,
            breakdowns={'by_date': []}  # Simplified - no breakdowns for now
        )

        # Cache the result
        self.save_analytics_snapshot(analytics)

        return analytics

    def get_aggregated_metrics(self, campaign_id: str, start_date: date,
                              end_date: date) -> Dict[str, Any]:
        """Get aggregated metrics for a campaign."""
        analytics = self.get_campaign_analytics(campaign_id, start_date, end_date)

        return {
            'clicks': analytics.clicks,
            'conversions': analytics.conversions,
            'revenue': analytics.revenue,
            'cost': analytics.cost,
            'profit': analytics.profit,
            'ctr': analytics.ctr,
            'cr': analytics.cr,
            'epc': analytics.epc,
            'roi': analytics.roi,
        }

    def save_analytics_snapshot(self, analytics: Analytics) -> None:
        """Save analytics snapshot for caching."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cache_key = f"{analytics.campaign_id}_{analytics.time_range['start_date']}_{analytics.time_range['end_date']}_{analytics.time_range['granularity']}"
        expires_at = datetime.now() + timedelta(hours=1)

        cursor.execute("""
            INSERT INTO analytics_cache
            (cache_key, campaign_id, start_date, end_date, granularity,
             clicks, unique_clicks, conversions, revenue_amount, revenue_currency,
             cost_amount, cost_currency, ctr, cr, epc_amount, epc_currency, roi,
             breakdowns, created_at, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (cache_key) DO UPDATE SET
                clicks = EXCLUDED.clicks,
                unique_clicks = EXCLUDED.unique_clicks,
                conversions = EXCLUDED.conversions,
                revenue_amount = EXCLUDED.revenue_amount,
                revenue_currency = EXCLUDED.revenue_currency,
                cost_amount = EXCLUDED.cost_amount,
                cost_currency = EXCLUDED.cost_currency,
                ctr = EXCLUDED.ctr,
                cr = EXCLUDED.cr,
                epc_amount = EXCLUDED.epc_amount,
                epc_currency = EXCLUDED.epc_currency,
                roi = EXCLUDED.roi,
                breakdowns = EXCLUDED.breakdowns,
                expires_at = EXCLUDED.expires_at
        """, (
            cache_key, analytics.campaign_id, analytics.time_range['start_date'],
            analytics.time_range['end_date'], analytics.time_range['granularity'],
            analytics.clicks, analytics.unique_clicks, analytics.conversions,
            analytics.revenue.amount, analytics.revenue.currency,
            analytics.cost.amount, analytics.cost.currency,
            analytics.ctr, analytics.cr,
            analytics.epc.amount, analytics.epc.currency,
            analytics.roi,
            json.dumps(analytics.breakdowns),
            datetime.now(),
            expires_at
        ))

        conn.commit()

    def get_cached_analytics(self, campaign_id: str, start_date: date,
                           end_date: date) -> Optional[Analytics]:
        """Get cached analytics if available."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cache_key = f"{campaign_id}_{start_date}_{end_date}_day"
        now = datetime.now()

        cursor.execute("""
            SELECT * FROM analytics_cache
            WHERE cache_key = %s AND expires_at > %s
        """, (cache_key, now))

        row = cursor.fetchone()
        if not row:
            return None

        # Convert tuple to dict for easier access
        columns = [desc[0] for desc in cursor.description]
        row_dict = dict(zip(columns, row))

        # Reconstruct analytics object from cache
        analytics = Analytics(
            campaign_id=row_dict["campaign_id"],
            time_range={
                'start_date': row_dict["start_date"].isoformat(),
                'end_date': row_dict["end_date"].isoformat(),
                'granularity': row_dict["granularity"]
            },
            clicks=row_dict["clicks"],
            unique_clicks=row_dict["unique_clicks"],
            conversions=row_dict["conversions"],
            revenue=Money.from_float(float(row_dict["revenue_amount"]), row_dict["revenue_currency"]),
            cost=Money.from_float(float(row_dict["cost_amount"]), row_dict["cost_currency"]),
            ctr=float(row_dict["ctr"]),
            cr=float(row_dict["cr"]),
            epc=Money.from_float(float(row_dict["epc_amount"]), row_dict["epc_currency"]),
            roi=float(row_dict["roi"]),
            breakdowns=row_dict["breakdowns"]
        )

        return analytics
