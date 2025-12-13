# Advertising Platform Admin Panel

A comprehensive PyQt6-based admin interface for managing Advertising Platform business tasks and operations.

## Features

- **Dashboard**: Real-time system overview and health monitoring
- **Campaign Management**: Create, edit, pause/resume, and delete advertising campaigns
- **Goal Management**: Manage conversion goals and tracking objectives
- **Analytics**: View campaign performance and real-time metrics
- **Click Tracking**: Monitor and manage click data and user interactions
- **Settings**: Configure API connections and authentication
- **Multi-threaded**: Non-blocking UI with background API operations

## Installation

### Prerequisites

- Python 3.8+
- PyQt6
- Advertising Platform API SDK

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install specific packages:

```bash
pip install PyQt6>=6.5.0 requests>=2.31.0 python-dotenv>=1.0.0 qasync>=0.27.0
```

### Install the SDK

Make sure the Advertising Platform SDK is available:

```bash
# From the parent directory
pip install -e advertising_platform_sdk/
```

## Usage

### Running the Application

```bash
python main.py
```

Or if installed as a package:

```bash
advertising-admin
```

### Connecting to API

1. Launch the admin panel
2. Enter your API base URL (default: `http://127.0.0.1:5000/v1`)
3. Provide authentication credentials (Bearer token or API key)
4. Click "Connect" to establish connection
5. The connection status will show "Connected" when successful

## Interface Overview

### Dashboard Tab

- **System Health**: Real-time API health status
- **Quick Statistics**: Overview of campaigns, goals, and activity
- **Recent Activity**: Log of system events and operations

### Campaigns Tab

- **Campaign List**: Table view of all campaigns with filtering and search
- **Create/Edit**: Dialog forms for campaign management
- **Status Control**: Pause/resume campaigns directly from the interface
- **Bulk Operations**: Select multiple campaigns for batch operations

### Goals Tab

- **Goal Management**: Create and manage conversion goals
- **Campaign Association**: Link goals to specific campaigns
- **Goal Templates**: Use predefined goal templates
- **Performance Tracking**: Monitor goal conversion rates

### Analytics Tab

- **Campaign Analytics**: Detailed performance metrics by campaign
- **Real-time Data**: Live metrics and KPIs
- **Date Range Selection**: Historical data analysis
- **Export Options**: Export analytics data to various formats

### Clicks Tab

- **Click Monitoring**: View all click events and interactions
- **URL Generation**: Create tracking URLs for campaigns
- **Fraud Detection**: Identify suspicious click patterns
- **Geographic Data**: Click source analysis by location

### Settings Tab

- **API Configuration**: Base URL and connection settings
- **Authentication**: Token and key management
- **UI Preferences**: Customize interface appearance
- **Data Refresh**: Configure auto-refresh intervals

## Business Task Management

### Campaign Operations

1. **Create Campaign**:
   - Set campaign name and description
   - Configure budget and bidding strategy
   - Define target audience and geography
   - Set start/end dates

2. **Campaign Optimization**:
   - Monitor performance metrics
   - Adjust budget and targeting
   - A/B test landing pages
   - Scale successful campaigns

3. **Campaign Lifecycle**:
   - Draft → Active → Paused → Completed
   - Automated pause/resume based on performance
   - Archive completed campaigns

### Goal Management

1. **Goal Definition**:
   - Purchase goals with revenue tracking
   - Lead generation goals
   - Custom conversion events
   - Multi-step funnel goals

2. **Goal Optimization**:
   - Analyze conversion paths
   - Identify drop-off points
   - Optimize landing pages
   - Improve call-to-action elements

### Analytics and Reporting

1. **Performance Monitoring**:
   - Real-time dashboard metrics
   - Campaign ROI analysis
   - Traffic source attribution
   - Device and browser breakdown

2. **Business Intelligence**:
   - Customer lifetime value analysis
   - Funnel optimization insights
   - Predictive performance modeling
   - Automated alerts and notifications

### Click and Conversion Tracking

1. **Traffic Management**:
   - Monitor click quality and sources
   - Fraud detection and prevention
   - Bot traffic filtering
   - Geographic targeting validation

2. **Conversion Optimization**:
   - Track conversion paths
   - Identify high-value traffic sources
   - Optimize landing page performance
   - Improve conversion rates

## Advanced Features

### Multi-threading

The admin panel uses background threads for API operations to maintain a responsive UI:

- Non-blocking API calls
- Progress indicators for long operations
- Error handling with user notifications
- Automatic retry logic

### Data Caching

- Local caching of frequently accessed data
- Offline mode for read operations
- Background data synchronization
- Cache invalidation on data changes

### Keyboard Shortcuts

- `Ctrl+R`: Refresh current tab
- `Ctrl+N`: Create new item
- `Ctrl+F`: Focus search/filter
- `F5`: Refresh all data
- `Ctrl+Q`: Quit application

### Themes and Customization

- Light/Dark theme support
- Customizable color schemes
- Font size and family settings
- Layout preferences

## Configuration

### Environment Variables

```bash
# API Configuration
ADVERTISING_API_BASE_URL=http://127.0.0.1:5000/v1
ADVERTISING_API_BEARER_TOKEN=your-jwt-token
ADVERTISING_API_KEY=your-api-key
ADVERTISING_API_TIMEOUT=30

# UI Configuration
ADMIN_PANEL_THEME=dark
ADMIN_PANEL_FONT_SIZE=12
ADMIN_PANEL_AUTO_REFRESH=60
```

### Configuration File

Create a `.env` file in the admin panel directory:

```env
ADVERTISING_API_BASE_URL=http://127.0.0.1:5000/v1
ADVERTISING_API_BEARER_TOKEN=your-jwt-token
ADVERTISING_API_TIMEOUT=30
ADMIN_PANEL_THEME=dark
```

## Development

### Project Structure

```
admin_panel/
├── main.py                 # Main application entry point
├── setup.py               # Package setup script
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── __init__.py           # Package initialization
```

### Adding New Features

1. **New Tab**: Create a new tab class inheriting from QWidget
2. **API Integration**: Use the AdvertisingPlatformClient for API operations
3. **Threading**: Wrap API calls in APIWorker for non-blocking operations
4. **UI Components**: Follow PyQt6 best practices for consistent UI

### Code Style

- Follow PEP 8 Python style guidelines
- Use type hints for better code documentation
- Implement proper error handling
- Add docstrings to all functions and classes

## Troubleshooting

### Connection Issues

1. **API Not Accessible**:
   - Verify API server is running
   - Check network connectivity
   - Confirm correct base URL

2. **Authentication Failed**:
   - Verify bearer token or API key
   - Check token expiration
   - Confirm correct authentication method

### Performance Issues

1. **Slow Loading**:
   - Check network latency
   - Reduce data refresh frequency
   - Enable data caching

2. **UI Freezing**:
   - Ensure API calls are wrapped in threads
   - Check for infinite loops
   - Monitor memory usage

### Common Errors

- **ImportError**: Ensure all dependencies are installed
- **ConnectionError**: Check API server status
- **AuthenticationError**: Verify credentials
- **ValidationError**: Check input data format

## API Documentation

For detailed API documentation, see the [Advertising Platform API Documentation](../openapi.yaml).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- Check the troubleshooting section
- Review the API documentation
- Create an issue on GitHub
- Contact the development team

## Roadmap

### Planned Features

- [ ] Advanced analytics charts and graphs
- [ ] Bulk import/export operations
- [ ] Role-based access control
- [ ] Audit logging and compliance
- [ ] Mobile responsive design
- [ ] Plugin system for extensions
- [ ] API testing tools integration
- [ ] Automated reporting and alerts