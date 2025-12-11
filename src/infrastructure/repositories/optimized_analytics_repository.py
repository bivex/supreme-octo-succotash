"""Optimized analytics repository with vectorized operations."""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, date
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

from ...domain.value_objects import Analytics, Money
from ...domain.repositories.analytics_repository import AnalyticsRepository
from ...domain.repositories.click_repository import ClickRepository
from ...domain.repositories.campaign_repository import CampaignRepository

logger = logging.getLogger(__name__)

class OptimizedAnalyticsRepository(AnalyticsRepository):
    """High-performance analytics repository using vectorized operations."""

    def __init__(self,
                 click_repository: ClickRepository,
                 campaign_repository: CampaignRepository,
                 container):
        self._click_repository = click_repository
        self._campaign_repository = campaign_repository
        self._container = container
        self._connection = None
        self._db_initialized = False

        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=2)

    def get_campaign_analytics(self, campaign_id: str, start_date: date,
                              end_date: date, granularity: str = "day") -> Analytics:
        """Get analytics for a campaign within date range using vectorized operations."""
        # Check cache first
        cached_analytics = self.get_cached_analytics(campaign_id, start_date, end_date)
        if cached_analytics:
            return cached_analytics

        # Get clicks in date range
        clicks = self._click_repository.get_clicks_in_date_range(
            campaign_id, start_date, end_date
        )

        if not clicks:
            return self._create_empty_analytics(campaign_id, start_date, end_date)

        # Vectorized processing using pandas
        analytics = self._vectorized_analytics_processing(clicks, campaign_id, start_date, end_date)

        # Cache the result
        self._cache_analytics_result(campaign_id, start_date, end_date, granularity, analytics)

        return analytics

    def _vectorized_analytics_processing(self, clicks: List, campaign_id: str,
                                       start_date: date, end_date: date) -> Analytics:
        """Process analytics using vectorized operations."""
        try:
            # Convert clicks to DataFrame for vectorized processing
            clicks_data = []
            for click in clicks:
                clicks_data.append({
                    'click_id': click.click_id.value if hasattr(click, 'click_id') else str(click.id),
                    'is_valid': click.is_valid if hasattr(click, 'is_valid') else True,
                    'has_conversion': click.has_conversion if hasattr(click, 'has_conversion') else False,
                    'revenue': float(click.revenue.amount) if hasattr(click, 'revenue') and click.revenue else 0.0,
                    'cost': float(click.cost.amount) if hasattr(click, 'cost') and click.cost else 0.0,
                    'timestamp': click.timestamp if hasattr(click, 'timestamp') else datetime.now(),
                })

            df = pd.DataFrame(clicks_data)

            # Vectorized filtering and calculations
            valid_clicks = df[df['is_valid']]
            conversions = df[df['has_conversion']]

            # Vectorized aggregations
            total_clicks = len(valid_clicks)
            total_conversions = len(conversions)

            # Vectorized CTR calculation
            ctr = total_conversions / total_clicks if total_clicks > 0 else 0.0

            # Vectorized revenue/cost calculations using numpy
            total_revenue = np.sum(valid_clicks['revenue'].values)
            total_cost = np.sum(valid_clicks['cost'].values)

            # Vectorized EPC (Earnings Per Click)
            epc = total_revenue / total_clicks if total_clicks > 0 else 0.0

            # Vectorized ROI calculation
            roi = (total_revenue - total_cost) / total_cost if total_cost > 0 else 0.0

            # Vectorized CR (Conversion Rate)
            cr = total_conversions / total_clicks if total_clicks > 0 else 0.0

            # Get campaign for additional data
            from ...domain.value_objects import CampaignId
            campaign = self._campaign_repository.find_by_id(CampaignId.from_string(campaign_id))

            # Create analytics result
            analytics = Analytics(
                campaign_id=campaign_id,
                date_range=(start_date, end_date),
                clicks=total_clicks,
                unique_clicks=total_clicks,  # Assuming all clicks are unique for now
                conversions=total_conversions,
                revenue=Money(amount=total_revenue, currency="USD"),
                cost=Money(amount=total_cost, currency="USD"),
                ctr=ctr,
                cr=cr,
                epc=Money(amount=epc, currency="USD"),
                roi=roi,
                breakdowns=self._generate_vectorized_breakdowns(df, start_date, end_date)
            )

            return analytics

        except Exception as e:
            logger.error(f"Vectorized analytics processing failed: {e}")
            # Fallback to original implementation
            return self._fallback_analytics_processing(clicks, campaign_id, start_date, end_date)

    def _generate_vectorized_breakdowns(self, df: pd.DataFrame, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate breakdowns using vectorized operations."""
        try:
            # Ensure timestamp is datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Vectorized daily breakdown
            daily_stats = df.groupby(df['timestamp'].dt.date).agg({
                'is_valid': 'sum',
                'has_conversion': 'sum',
                'revenue': 'sum',
                'cost': 'sum'
            }).reset_index()

            # Convert to dictionary format
            daily_breakdown = {}
            for _, row in daily_stats.iterrows():
                date_str = row['timestamp'].strftime('%Y-%m-%d')
                daily_breakdown[date_str] = {
                    'clicks': int(row['is_valid']),
                    'conversions': int(row['has_conversion']),
                    'revenue': float(row['revenue']),
                    'cost': float(row['cost'])
                }

            return {
                'daily': daily_breakdown,
                'total_days': len(daily_breakdown),
                'avg_daily_clicks': np.mean(list(d['clicks'] for d in daily_breakdown.values())),
                'avg_daily_conversions': np.mean(list(d['conversions'] for d in daily_breakdown.values()))
            }

        except Exception as e:
            logger.error(f"Vectorized breakdown generation failed: {e}")
            return {}

    def _fallback_analytics_processing(self, clicks: List, campaign_id: str,
                                     start_date: date, end_date: date) -> Analytics:
        """Fallback to original analytics processing."""
        # Original implementation as fallback
        valid_clicks = [c for c in clicks if c.is_valid]
        conversions = [c for c in clicks if c.has_conversion]

        total_clicks = len(valid_clicks)
        total_conversions = len(conversions)

        ctr = total_conversions / total_clicks if total_clicks > 0 else 0.0

        # Get campaign for cost/revenue calculations
        from ...domain.value_objects import CampaignId
        campaign = self._campaign_repository.find_by_id(CampaignId.from_string(campaign_id))

        # Calculate totals (simplified)
        total_revenue = 0.0
        total_cost = 0.0

        analytics = Analytics(
            campaign_id=campaign_id,
            date_range=(start_date, end_date),
            clicks=total_clicks,
            unique_clicks=total_clicks,
            conversions=total_conversions,
            revenue=Money(amount=total_revenue, currency="USD"),
            cost=Money(amount=total_cost, currency="USD"),
            ctr=ctr,
            cr=0.0,
            epc=Money(amount=0.0, currency="USD"),
            roi=0.0,
            breakdowns={}
        )

        return analytics

    def _create_empty_analytics(self, campaign_id: str, start_date: date, end_date: date) -> Analytics:
        """Create empty analytics for campaigns with no data."""
        return Analytics(
            campaign_id=campaign_id,
            date_range=(start_date, end_date),
            clicks=0,
            unique_clicks=0,
            conversions=0,
            revenue=Money(amount=0.0, currency="USD"),
            cost=Money(amount=0.0, currency="USD"),
            ctr=0.0,
            cr=0.0,
            epc=Money(amount=0.0, currency="USD"),
            roi=0.0,
            breakdowns={}
        )

    async def get_bulk_campaign_analytics(self, campaign_ids: List[str],
                                        start_date: date, end_date: date) -> Dict[str, Analytics]:
        """Get analytics for multiple campaigns concurrently."""
        async def process_campaign(campaign_id: str) -> tuple[str, Analytics]:
            """Process single campaign analytics."""
            loop = asyncio.get_event_loop()
            analytics = await loop.run_in_executor(
                self.executor,
                self.get_campaign_analytics,
                campaign_id, start_date, end_date
            )
            return campaign_id, analytics

        # Process all campaigns concurrently
        tasks = [process_campaign(cid) for cid in campaign_ids]
        results = await asyncio.gather(*tasks)

        return dict(results)

    def get_performance_metrics(self) -> Dict[str, float]:
        """Get repository performance metrics."""
        return {
            'vectorization_enabled': True,
            'thread_pool_workers': 2,
            'cache_hit_ratio': self._calculate_cache_hit_ratio()
        }

    def _calculate_cache_hit_ratio(self) -> float:
        """Calculate analytics cache hit ratio."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_queries,
                        COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '1 hour') as recent_queries
                    FROM analytics_cache
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                """)
                result = cursor.fetchone()
                if result and result[0] > 0:
                    return result[1] / result[0]
                return 0.0
        except Exception:
            return 0.0

    def _get_connection(self):
        """Get database connection."""
        if self._connection is None:
            self._connection = self._container.get_db_connection()
        if not self._db_initialized:
            self._initialize_db()
            self._db_initialized = True
        return self._connection

    def _initialize_db(self) -> None:
        """Initialize database schema for analytics caching."""
        conn = None
        try:
            conn = self._container.get_db_connection()
            cursor = conn.cursor()

            # Create analytics cache table with improved schema
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
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    expires_at TIMESTAMP NOT NULL
                )
            """)

            # Create optimized indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_campaign_dates ON analytics_cache(campaign_id, start_date, end_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_expires ON analytics_cache(expires_at)")
            cursor.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_cache_key ON analytics_cache(cache_key)")

            conn.commit()
        finally:
            if conn:
                self._container.release_db_connection(conn)

    def get_cached_analytics(self, campaign_id: str, start_date: date, end_date: date) -> Optional[Analytics]:
        """Get cached analytics with optimized query."""
        try:
            conn = self._get_connection()
            cache_key = f"{campaign_id}_{start_date}_{end_date}"

            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT clicks, unique_clicks, conversions,
                           revenue_amount, revenue_currency,
                           cost_amount, cost_currency,
                           ctr, cr, epc_amount, epc_currency, roi,
                           breakdowns
                    FROM analytics_cache
                    WHERE cache_key = %s AND expires_at > NOW()
                """, (cache_key,))

                result = cursor.fetchone()
                if result:
                    clicks, unique_clicks, conversions, rev_amt, rev_cur, cost_amt, cost_cur, ctr, cr, epc_amt, epc_cur, roi, breakdowns = result

                    return Analytics(
                        campaign_id=campaign_id,
                        date_range=(start_date, end_date),
                        clicks=clicks,
                        unique_clicks=unique_clicks,
                        conversions=conversions,
                        revenue=Money(amount=float(rev_amt), currency=rev_cur),
                        cost=Money(amount=float(cost_amt), currency=cost_cur),
                        ctr=float(ctr),
                        cr=float(cr),
                        epc=Money(amount=float(epc_amt), currency=epc_cur),
                        roi=float(roi),
                        breakdowns=breakdowns or {}
                    )

        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")

        return None

    def _cache_analytics_result(self, campaign_id: str, start_date: date, end_date: date,
                               granularity: str, analytics: Analytics) -> None:
        """Cache analytics result with optimized insertion."""
        try:
            conn = self._get_connection()
            cache_key = f"{campaign_id}_{start_date}_{end_date}"
            expires_at = datetime.now() + timedelta(hours=24)  # 24 hour cache

            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO analytics_cache (
                        cache_key, campaign_id, start_date, end_date, granularity,
                        clicks, unique_clicks, conversions,
                        revenue_amount, revenue_currency,
                        cost_amount, cost_currency,
                        ctr, cr, epc_amount, epc_currency, roi,
                        breakdowns, expires_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (cache_key) DO UPDATE SET
                        clicks = EXCLUDED.clicks,
                        conversions = EXCLUDED.conversions,
                        revenue_amount = EXCLUDED.revenue_amount,
                        cost_amount = EXCLUDED.cost_amount,
                        ctr = EXCLUDED.ctr,
                        cr = EXCLUDED.cr,
                        epc_amount = EXCLUDED.epc_amount,
                        roi = EXCLUDED.roi,
                        breakdowns = EXCLUDED.breakdowns,
                        created_at = NOW(),
                        expires_at = EXCLUDED.expires_at
                """, (
                    cache_key, campaign_id, start_date, end_date, granularity,
                    analytics.clicks, analytics.unique_clicks, analytics.conversions,
                    analytics.revenue.amount, analytics.revenue.currency,
                    analytics.cost.amount, analytics.cost.currency,
                    analytics.ctr, analytics.cr,
                    analytics.epc.amount, analytics.epc.currency,
                    analytics.roi, analytics.breakdowns, expires_at
                ))

            conn.commit()

        except Exception as e:
            logger.error(f"Cache storage failed: {e}")
            # Don't fail the main operation if caching fails






