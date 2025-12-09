"""Domain constants."""

# Campaign validation limits
MAX_CAMPAIGN_NAME_LENGTH = 255
MAX_DESCRIPTION_LENGTH = 1000
MAX_BUDGET_AMOUNT = 1_000_000  # 1M USD

# Click validation limits
MAX_REFERRER_LENGTH = 1000
MAX_HEADER_LENGTH = 1000
FRAUD_SCORE_THRESHOLD = 0.5

# Weight limits
MIN_WEIGHT = 0
MAX_WEIGHT = 100

# Pagination defaults
DEFAULT_PAGE_SIZE = 100
DEFAULT_LIMIT = 50

# Campaign generation
CAMPAIGN_ID_MIN = 1000
CAMPAIGN_ID_MAX = 9999

# Fraud detection
FRAUD_SCORE_LOW = 0.3
FRAUD_SCORE_MEDIUM = 0.5
FRAUD_SCORE_HIGH = 0.8
FRAUD_SCORE_MAX = 1.0

BOT_DETECTION_PATTERNS = [
    'bot', 'crawler', 'spider', 'scraper', 'headless', 'selenium',
    'chrome-lighthouse', 'googlebot', 'bingbot', 'yahoo', 'baidu',
    'yandex', 'duckduckbot', 'facebookexternalhit', 'twitterbot',
    'linkedinbot', 'whatsapp', 'telegrambot'
]

# Click validation
BOT_USER_AGENT_MIN_LENGTH = 10
BOT_USER_AGENT_MAX_SPACES = 20
REFERRER_MAX_LENGTH = 1000
VALID_TRACKING_PATTERN = r'^[a-zA-Z0-9._-]*$'

# Performance thresholds
CAMPAIGN_CLICKS_LOW_THRESHOLD = 1000
CAMPAIGN_CR_VERY_LOW_THRESHOLD = 0.001
ROI_NEGATIVE_THRESHOLD = -0.5
BUDGET_APPROACH_RATIO = 0.95

# Security
RATE_LIMIT_REQUESTS_PER_MINUTE = 1000000
RATE_LIMIT_WINDOW_SECONDS = 60
