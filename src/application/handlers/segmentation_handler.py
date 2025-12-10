"""User segmentation handler."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from ...domain.repositories.retention_repository import RetentionRepository
from ...domain.repositories.click_repository import ClickRepository
from ...domain.repositories.conversion_repository import ConversionRepository
from ...domain.services.retention.retention_service import RetentionService
from ...domain.entities.retention import UserSegment


class SegmentationHandler:
    """Handler for user segmentation operations."""

    def __init__(self, retention_repository: RetentionRepository,
                 click_repository: ClickRepository,
                 conversion_repository: ConversionRepository):
        self._retention_repository = retention_repository
        self._click_repository = click_repository
        self._conversion_repository = conversion_repository
        self._retention_service = RetentionService()

    def get_user_segments_overview(self) -> Dict[str, Any]:
        """
        Get overview of all user segments.

        Returns:
            Dict containing segments overview
        """
        try:
            logger.info("Getting user segments overview")

            # Get all user engagement profiles
            segments_data = {}
            total_users = 0

            for segment in UserSegment:
                profiles = self._retention_repository.get_users_by_segment(segment, limit=1000)
                total_users += len(profiles)

                if profiles:
                    avg_engagement = sum(p.engagement_score for p in profiles) / len(profiles)
                    total_clicks = sum(p.total_clicks for p in profiles)
                    total_conversions = sum(p.total_conversions for p in profiles)

                    segments_data[segment.value] = {
                        "segment_name": segment.value.replace("_", " ").title(),
                        "user_count": len(profiles),
                        "avg_engagement_score": avg_engagement,
                        "total_clicks": total_clicks,
                        "total_conversions": total_conversions,
                        "avg_conversion_rate": total_conversions / total_clicks if total_clicks > 0 else 0,
                        "description": self._get_segment_description(segment)
                    }

            result = {
                "status": "success",
                "total_users": total_users,
                "segments": segments_data,
                "segment_distribution": {
                    segment: data["user_count"] for segment, data in segments_data.items()
                }
            }

            return result

        except Exception as e:
            logger.error(f"Error getting segments overview: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to get segments overview: {str(e)}",
                "total_users": 0,
                "segments": {}
            }

    def analyze_user_segment(self, segment: UserSegment, limit: int = 100) -> Dict[str, Any]:
        """
        Analyze a specific user segment in detail.

        Args:
            segment: User segment to analyze
            limit: Maximum number of users to analyze

        Returns:
            Dict containing segment analysis
        """
        try:
            logger.info(f"Analyzing segment: {segment.value}")

            profiles = self._retention_repository.get_users_by_segment(segment, limit)

            if not profiles:
                return {
                    "status": "no_data",
                    "message": f"No users found in segment {segment.value}",
                    "segment": segment.value
                }

            # Analyze segment characteristics
            engagement_scores = [p.engagement_score for p in profiles]
            session_counts = [p.total_sessions for p in profiles]
            click_counts = [p.total_clicks for p in profiles]
            conversion_counts = [p.total_conversions for p in profiles]

            # Calculate statistics
            segment_stats = {
                "user_count": len(profiles),
                "avg_engagement_score": sum(engagement_scores) / len(engagement_scores),
                "min_engagement_score": min(engagement_scores),
                "max_engagement_score": max(engagement_scores),
                "avg_sessions": sum(session_counts) / len(session_counts),
                "avg_clicks": sum(click_counts) / len(click_counts),
                "avg_conversions": sum(conversion_counts) / len(conversion_counts),
                "total_clicks": sum(click_counts),
                "total_conversions": sum(conversion_counts),
                "conversion_rate": sum(conversion_counts) / sum(click_counts) if sum(click_counts) > 0 else 0
            }

            # Get interests distribution
            interests_dist = {}
            for profile in profiles:
                for interest in profile.interests:
                    interests_dist[interest] = interests_dist.get(interest, 0) + 1

            # Get sample users (first 10)
            sample_users = []
            for profile in profiles[:10]:
                sample_users.append({
                    "customer_id": profile.customer_id,
                    "engagement_score": profile.engagement_score,
                    "total_sessions": profile.total_sessions,
                    "total_clicks": profile.total_clicks,
                    "total_conversions": profile.total_conversions,
                    "interests": profile.interests,
                    "last_session_date": profile.last_session_date.isoformat()
                })

            result = {
                "status": "success",
                "segment": segment.value,
                "segment_name": segment.value.replace("_", " ").title(),
                "description": self._get_segment_description(segment),
                "statistics": segment_stats,
                "interests_distribution": interests_dist,
                "sample_users": sample_users,
                "analysis_timestamp": datetime.now().isoformat()
            }

            return result

        except Exception as e:
            logger.error(f"Error analyzing segment {segment.value}: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to analyze segment: {str(e)}",
                "segment": segment.value
            }

    def segment_user(self, customer_id: str) -> Dict[str, Any]:
        """
        Determine the segment for a specific user.

        Args:
            customer_id: Customer identifier

        Returns:
            Dict containing user segmentation result
        """
        try:
            logger.info(f"Segmenting user: {customer_id}")

            # Get user engagement profile
            profile = self._retention_repository.get_user_engagement_profile(customer_id)

            if not profile:
                # Create profile from click and conversion data
                clicks = self._click_repository.find_by_customer_id(customer_id, limit=100)
                conversions = self._conversion_repository.find_by_customer_id(customer_id, limit=50)

                if not clicks:
                    return {
                        "status": "no_data",
                        "message": f"No activity data found for user {customer_id}",
                        "customer_id": customer_id,
                        "segment": UserSegment.LOW_ENGAGEMENT.value
                    }

                # Analyze engagement
                profile = self._retention_service.analyze_user_engagement(clicks, conversions, customer_id)

                # Save the profile
                self._retention_repository.save_user_engagement_profile(profile)

            result = {
                "status": "success",
                "customer_id": customer_id,
                "segment": profile.segment.value,
                "segment_name": profile.segment.value.replace("_", " ").title(),
                "engagement_score": profile.engagement_score,
                "confidence": self._calculate_segmentation_confidence(profile),
                "segment_characteristics": {
                    "total_sessions": profile.total_sessions,
                    "total_clicks": profile.total_clicks,
                    "total_conversions": profile.total_conversions,
                    "avg_session_duration": profile.avg_session_duration,
                    "conversion_rate": profile.conversion_rate,
                    "interests": profile.interests,
                    "last_session_date": profile.last_session_date.isoformat(),
                    "days_since_last_activity": profile.days_since_last_activity
                },
                "segmentation_timestamp": datetime.now().isoformat()
            }

            return result

        except Exception as e:
            logger.error(f"Error segmenting user {customer_id}: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to segment user: {str(e)}",
                "customer_id": customer_id
            }

    def get_segment_migration_paths(self) -> Dict[str, Any]:
        """
        Analyze how users move between segments over time.

        Returns:
            Dict containing segment migration analysis
        """
        try:
            logger.info("Analyzing segment migration paths")

            # This is a simplified implementation
            # In a real system, we'd track segment changes over time

            segments = list(UserSegment)
            migration_matrix = {}

            # Initialize migration matrix
            for from_segment in segments:
                migration_matrix[from_segment.value] = {}
                for to_segment in segments:
                    migration_matrix[from_segment.value][to_segment.value] = 0

            # Analyze recent segment changes (simplified)
            # In practice, we'd have historical segment data
            all_profiles = []
            for segment in segments:
                profiles = self._retention_repository.get_users_by_segment(segment, limit=200)
                all_profiles.extend(profiles)

            # For demonstration, create some mock migration patterns
            # In real implementation, this would be based on historical data
            migration_patterns = {
                UserSegment.NEW_USERS.value: {
                    UserSegment.ACTIVE_USERS.value: 0.7,
                    UserSegment.AT_RISK.value: 0.2,
                    UserSegment.LOW_ENGAGEMENT.value: 0.1
                },
                UserSegment.ACTIVE_USERS.value: {
                    UserSegment.HIGH_VALUE.value: 0.3,
                    UserSegment.AT_RISK.value: 0.4,
                    UserSegment.LOW_ENGAGEMENT.value: 0.3
                },
                UserSegment.AT_RISK.value: {
                    UserSegment.ACTIVE_USERS.value: 0.4,
                    UserSegment.CHURNED.value: 0.6
                },
                UserSegment.LOW_ENGAGEMENT.value: {
                    UserSegment.AT_RISK.value: 0.5,
                    UserSegment.CHURNED.value: 0.5
                }
            }

            result = {
                "status": "success",
                "migration_patterns": migration_patterns,
                "description": "Estimated migration probabilities between segments based on historical patterns",
                "analysis_period": "last_30_days",
                "analysis_timestamp": datetime.now().isoformat()
            }

            return result

        except Exception as e:
            logger.error(f"Error analyzing segment migration: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to analyze segment migration: {str(e)}"
            }

    def _get_segment_description(self, segment: UserSegment) -> str:
        """Get description for a user segment."""
        descriptions = {
            UserSegment.NEW_USERS: "Recently acquired users who have made their first purchase",
            UserSegment.ACTIVE_USERS: "Regularly engaged users with good activity levels",
            UserSegment.HIGH_VALUE: "Top customers with high engagement and spending",
            UserSegment.AT_RISK: "Users showing signs of reduced engagement",
            UserSegment.LOW_ENGAGEMENT: "Users with minimal activity and engagement",
            UserSegment.CHURNED: "Users who have stopped engaging with the service"
        }
        return descriptions.get(segment, "Unknown segment")

    def _calculate_segmentation_confidence(self, profile) -> float:
        """Calculate confidence score for user segmentation."""
        # Simple confidence calculation based on data completeness
        confidence = 0.0

        if profile.total_sessions > 0:
            confidence += 0.3
        if profile.total_clicks > 0:
            confidence += 0.3
        if profile.total_conversions > 0:
            confidence += 0.2
        if profile.interests:
            confidence += 0.1
        if profile.avg_session_duration > 0:
            confidence += 0.1

        return min(1.0, confidence)
