"""Fraud detection handler."""

import uuid
import time
from typing import Dict, Any, List, Optional
from loguru import logger


class FraudHandler:
    """Handler for fraud detection operations."""

    def __init__(self):
        """Initialize fraud handler."""
        # Mock storage for fraud rules (in real implementation, this would be a database)
        self._rules = self._initialize_mock_rules()

    def _initialize_mock_rules(self) -> List[Dict[str, Any]]:
        """Initialize mock fraud rules for demonstration."""
        return [
            {
                "id": "fraud_rule_001",
                "name": "Block suspicious user agents",
                "type": "ua_block",
                "action": "block",
                "conditions": {
                    "user_agents": ["bot", "crawler", "spider", "scraper"]
                },
                "priority": 80,
                "isActive": True,
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-15T00:00:00Z"
            },
            {
                "id": "fraud_rule_002",
                "name": "Block Russian traffic",
                "type": "geo_block",
                "action": "block",
                "conditions": {
                    "countries": ["RU"]
                },
                "priority": 90,
                "isActive": True,
                "createdAt": "2024-01-02T00:00:00Z",
                "updatedAt": "2024-01-15T00:00:00Z"
            },
            {
                "id": "fraud_rule_003",
                "name": "Rate limit suspicious IPs",
                "type": "rate_limit",
                "action": "score_increase",
                "conditions": {
                    "rate_limit": {
                        "requests_per_minute": 10,
                        "time_window_seconds": 60
                    }
                },
                "priority": 60,
                "isActive": True,
                "createdAt": "2024-01-03T00:00:00Z",
                "updatedAt": "2024-01-15T00:00:00Z"
            }
        ]

    def list_rules(self, page: int = 1, page_size: int = 20,
                  rule_type: Optional[str] = None, active_only: bool = False) -> Dict[str, Any]:
        """List fraud detection rules with pagination and filtering.

        Args:
            page: Page number (1-based)
            page_size: Number of rules per page
            rule_type: Filter by rule type
            active_only: Only return active rules

        Returns:
            Dict containing rules list and pagination info
        """
        try:
            logger.info(f"Listing fraud rules: page={page}, size={page_size}, type={rule_type}, active_only={active_only}")

            # Filter rules
            filtered_rules = self._rules.copy()

            if rule_type:
                filtered_rules = [r for r in filtered_rules if r['type'] == rule_type]

            if active_only:
                filtered_rules = [r for r in filtered_rules if r['isActive']]

            # Sort by priority (highest first)
            filtered_rules.sort(key=lambda x: x['priority'], reverse=True)

            # Paginate
            total = len(filtered_rules)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_rules = filtered_rules[start_idx:end_idx]

            total_pages = (total + page_size - 1) // page_size  # Ceiling division

            return {
                "status": "success",
                "rules": paginated_rules,
                "pagination": {
                    "page": page,
                    "limit": page_size,
                    "total": total,
                    "totalPages": total_pages,
                    "hasNext": page < total_pages,
                    "hasPrev": page > 1
                }
            }

        except Exception as e:
            logger.error(f"Error listing fraud rules: {e}", exc_info=True)
            return {
                "status": "error",
                "message": "Internal server error",
                "rules": [],
                "pagination": {
                    "page": page,
                    "limit": page_size,
                    "total": 0,
                    "totalPages": 0,
                    "hasNext": False,
                    "hasPrev": False
                }
            }

    def create_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new fraud detection rule.

        Args:
            rule_data: Rule configuration data

        Returns:
            Dict containing created rule or error
        """
        try:
            logger.info("Creating new fraud rule")

            # Validate required fields
            required_fields = ['name', 'type', 'action']
            for field in required_fields:
                if field not in rule_data:
                    return {
                        "error": {"code": "VALIDATION_ERROR", "message": f"Missing required field: {field}"}
                    }

            # Validate rule type
            valid_types = ['ip_block', 'ua_block', 'geo_block', 'rate_limit', 'pattern_match', 'score_threshold']
            if rule_data['type'] not in valid_types:
                return {
                    "error": {"code": "VALIDATION_ERROR", "message": f"Invalid rule type. Must be one of: {', '.join(valid_types)}"}
                }

            # Validate action
            valid_actions = ['block', 'flag', 'score_increase', 'redirect_safe']
            if rule_data['action'] not in valid_actions:
                return {
                    "error": {"code": "VALIDATION_ERROR", "message": f"Invalid action. Must be one of: {', '.join(valid_actions)}"}
                }

            # Check for duplicate names
            existing_names = [r['name'] for r in self._rules]
            if rule_data['name'] in existing_names:
                return {
                    "error": {"code": "CONFLICT", "message": "Rule with this name already exists"}
                }

            # Create new rule
            new_rule = {
                "id": f"fraud_rule_{str(uuid.uuid4())[:8]}",
                "name": rule_data['name'],
                "type": rule_data['type'],
                "action": rule_data['action'],
                "conditions": rule_data.get('conditions', {}),
                "priority": rule_data.get('priority', 50),
                "isActive": rule_data.get('isActive', True),
                "createdAt": f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
                "updatedAt": f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}"
            }

            # Add to storage
            self._rules.append(new_rule)

            logger.info(f"Created fraud rule: {new_rule['id']} - {new_rule['name']}")

            return new_rule

        except Exception as e:
            logger.error(f"Error creating fraud rule: {e}", exc_info=True)
            return {
                "error": {"code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"}
            }
