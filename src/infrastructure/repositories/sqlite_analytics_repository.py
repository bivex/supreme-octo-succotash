"""SQLite analytics repository implementation."""

import sqlite3
from typing import Optional, Dict, Any
from datetime import date

from ...domain.value_objects import Analytics
from ...domain.repositories.analytics_repository import AnalyticsRepository
from ...domain.repositories.click_repository import ClickRepository
from ...domain.repositories.campaign_repository import CampaignRepository
from ...domain.value_objects import Money


class SQLiteAnalyticsRepository(AnalyticsRepository):
    """SQLite implementation of AnalyticsRepository."""

    def __init__(self,
                 click_repository: ClickRepository,
                 campaign_repository: CampaignRepository,
                 db_path: str = ":memory:"):
        self._click_repository = click_repository
        self._campaign_repository = campaign_repository
        self.db_path = db_path
        self._connection = None
        self._initialize_db()

    def _get_connection(self):
        """Get database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
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
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                granularity TEXT NOT NULL,
                clicks INTEGER DEFAULT 0,
                unique_clicks INTEGER DEFAULT 0,
                conversions INTEGER DEFAULT 0,
                revenue_amount REAL DEFAULT 0.0,
                revenue_currency TEXT DEFAULT 'USD',
                cost_amount REAL DEFAULT 0.0,
                cost_currency TEXT DEFAULT 'USD',
                ctr REAL DEFAULT 0.0,
                cr REAL DEFAULT 0.0,
                epc_amount REAL DEFAULT 0.0,
                epc_currency TEXT DEFAULT 'USD',
                roi REAL DEFAULT 0.0,
                breakdowns TEXT,  -- JSON string
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)

        # Create index for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_campaign_id ON analytics_cache(campaign_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_cache_key ON analytics_cache(cache_key)")

        conn.commit()

    def get_campaign_analytics(self, campaign_id: str, start_date: date,
                              end_date: date, granularity: str = "day") -> Analytics:
        """Get analytics for a campaign within date range."""
        # Check cache first
        cache_key = f"{campaign_id}_{start_date}_{end_date}_{granularity}"
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
        import json
        from datetime import datetime, timedelta, timezone

        conn = self._get_connection()
        cursor = conn.cursor()

        cache_key = f"{analytics.campaign_id}_{analytics.time_range['start_date']}_{analytics.time_range['end_date']}_{analytics.time_range['granularity']}"
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

        cursor.execute("""
            INSERT OR REPLACE INTO analytics_cache
            (cache_key, campaign_id, start_date, end_date, granularity,
             clicks, unique_clicks, conversions, revenue_amount, revenue_currency,
             cost_amount, cost_currency, ctr, cr, epc_amount, epc_currency, roi,
             breakdowns, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cache_key, analytics.campaign_id, analytics.time_range['start_date'],
            analytics.time_range['end_date'], analytics.time_range['granularity'],
            analytics.clicks, analytics.unique_clicks, analytics.conversions,
            analytics.revenue.amount, analytics.revenue.currency.value,
            analytics.cost.amount, analytics.cost.currency.value,
            analytics.ctr, analytics.cr,
            analytics.epc.amount, analytics.epc.currency.value,
            analytics.roi,
            json.dumps(analytics.breakdowns),
            datetime.now(timezone.utc).isoformat(),
            expires_at
        ))

        conn.commit()

    def get_cached_analytics(self, campaign_id: str, start_date: date,
                           end_date: date) -> Optional[Analytics]:
        """Get cached analytics if available."""
        import json
        from datetime import datetime, timezone

        conn = self._get_connection()
        cursor = conn.cursor()

        cache_key = f"{campaign_id}_{start_date}_{end_date}_day"
        now = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
            SELECT * FROM analytics_cache
            WHERE cache_key = ? AND expires_at > ?
        """, (cache_key, now))

        row = cursor.fetchone()
        if not row:
            return None

        # Reconstruct analytics object from cache
        analytics = Analytics(
            campaign_id=row["campaign_id"],
            time_range={
                'start_date': row["start_date"],
                'end_date': row["end_date"],
                'granularity': row["granularity"]
            },
            clicks=row["clicks"],
            unique_clicks=row["unique_clicks"],
            conversions=row["conversions"],
            revenue=Money.from_float(row["revenue_amount"], row["revenue_currency"]),
            cost=Money.from_float(row["cost_amount"], row["cost_currency"]),
            ctr=row["ctr"],
            cr=row["cr"],
            epc=Money.from_float(row["epc_amount"], row["epc_currency"]),
            roi=row["roi"],
            breakdowns=json.loads(row["breakdowns"])
        )

        return analytics
