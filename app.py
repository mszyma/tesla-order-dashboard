#!/usr/bin/env python3
"""
Tesla Order Status Web Dashboard

A Flask web application that provides a beautiful dashboard for Tesla order tracking
with real-time data refresh capabilities.
"""

import os
import hmac
import secrets
import json
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, flash, redirect, url_for, session, Response
from flask_babel import Babel, _, get_locale, ngettext
import threading
import logging

# Import our existing Tesla modules
from tesla_order_analyzer import TeslaOrderAnalyzer
from tesla_insights_generator import TeslaInsightsGenerator
from tesla_dashboard import TeslaDashboard

# Import Tesla API functionality
import base64
import hashlib
import requests
import urllib.parse
from tesla_stores import TeslaStore

app = Flask(__name__)
# Without SECRET_KEY a random key is generated at startup (sessions reset on restart).
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

DASHBOARD_USER = os.environ.get('DASHBOARD_USER', 'admin')
DASHBOARD_PASSWORD = os.environ.get('DASHBOARD_PASSWORD')


@app.before_request
def require_auth():
    """HTTP Basic Auth for every route except /health.

    Without DASHBOARD_PASSWORD the app only answers direct requests from
    localhost; anything behind a proxy (e.g. Railway) is refused.
    """
    if request.path == '/health':
        return None
    if not DASHBOARD_PASSWORD:
        behind_proxy = bool(os.environ.get('RAILWAY_ENVIRONMENT')
                            or request.headers.get('X-Forwarded-For'))
        if request.remote_addr in ('127.0.0.1', '::1') and not behind_proxy:
            return None
        return Response('DASHBOARD_PASSWORD is not set. Set the DASHBOARD_PASSWORD '
                        'environment variable to use this dashboard remotely.', 503)
    auth = request.authorization
    if (auth and auth.username is not None and auth.password is not None
            and hmac.compare_digest(auth.username.encode(), DASHBOARD_USER.encode())
            and hmac.compare_digest(auth.password.encode(), DASHBOARD_PASSWORD.encode())):
        return None
    return Response('Authentication required', 401,
                    {'WWW-Authenticate': 'Basic realm="Tesla Order Dashboard"'})

# Configure Babel for internationalization
app.config['LANGUAGES'] = {
    'en': 'English',
    'pl': 'Polski'
}
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'

def get_locale():
    # 1. Check if language is specified in session
    if 'language' in session:
        return session['language']
    # 2. Check if language is in URL parameters
    if request.args.get('lang'):
        session['language'] = request.args.get('lang')
        return session['language']
    # 3. Use browser's preferred language if available
    return request.accept_languages.best_match(app.config['LANGUAGES'].keys()) or 'en'

babel = Babel(app, locale_selector=get_locale)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tesla API Constants
CLIENT_ID = 'ownerapi'
REDIRECT_URI = 'https://auth.tesla.com/void/callback'
AUTH_URL = 'https://auth.tesla.com/oauth2/v3/authorize'
TOKEN_URL = 'https://auth.tesla.com/oauth2/v3/token'
SCOPE = 'openid email offline_access'
CODE_CHALLENGE_METHOD = 'S256'
APP_VERSION = '9.99.9-9999'

# File paths
TOKEN_FILE = 'tesla_tokens.json'
ORDERS_FILE = 'tesla_orders.json'
CACHE_FILE = 'dashboard_cache.json'


class TeslaAPIClient:
    """Tesla API client for web dashboard"""

    def __init__(self):
        self.tokens = self.load_tokens()
        self.cache = self.load_cache()

    def load_tokens(self):
        """Load Tesla API tokens (from TESLA_TOKENS_JSON env var or tesla_tokens.json)"""
        env_tokens = os.environ.get('TESLA_TOKENS_JSON')
        if env_tokens:
            try:
                return json.loads(env_tokens)
            except Exception as e:
                logger.error(f"Error parsing TESLA_TOKENS_JSON: {e}")
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading tokens: {e}")
        return None

    def load_cache(self):
        """Load dashboard cache"""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                    # Check if cache is still valid (1 hour)
                    cache_time = datetime.fromisoformat(
                        cache.get('timestamp', '2000-01-01'))
                    if datetime.now() - cache_time < timedelta(hours=1):
                        return cache
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
        return None

    def save_cache(self, data):
        """Save dashboard cache"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            with open(CACHE_FILE, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def is_token_valid(self, access_token):
        """Check if token is valid"""
        try:
            jwt_decoded = json.loads(base64.b64decode(
                access_token.split('.')[1] + '==').decode('utf-8'))
            return jwt_decoded['exp'] > time.time()
        except Exception:
            return False

    def refresh_tokens(self, refresh_token):
        """Refresh Tesla API tokens"""
        token_data = {
            'grant_type': 'refresh_token',
            'client_id': CLIENT_ID,
            'refresh_token': refresh_token,
        }
        response = requests.post(TOKEN_URL, data=token_data)
        response.raise_for_status()
        return response.json()

    def retrieve_orders(self, access_token):
        """Retrieve orders from Tesla API"""
        headers = {'Authorization': f'Bearer {access_token}'}
        api_url = 'https://owner-api.teslamotors.com/api/1/users/orders'
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        return response.json()['response']

    def get_order_details(self, order_id, access_token):
        """Get detailed order information"""
        headers = {'Authorization': f'Bearer {access_token}'}
        api_url = f'https://akamai-apigateway-vfx.tesla.com/tasks?deviceLanguage=en&deviceCountry=DE&referenceNumber={order_id}&appVersion={APP_VERSION}'
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        return response.json()

    def refresh_order_data(self):
        """Refresh order data from Tesla API"""
        try:
            if not self.tokens:
                return {'error': 'No Tesla tokens found. Run "python3 tesla_order_status.py" once to log in '
                         '(creates tesla_tokens.json) or set the TESLA_TOKENS_JSON environment variable.'}

            access_token = self.tokens.get('access_token')
            refresh_token = self.tokens.get('refresh_token')

            # Check if access token is valid
            if not self.is_token_valid(access_token):
                logger.info("Access token expired, refreshing...")
                token_response = self.refresh_tokens(refresh_token)
                access_token = token_response['access_token']
                self.tokens['access_token'] = access_token
                # Save updated tokens
                with open(TOKEN_FILE, 'w') as f:
                    json.dump(self.tokens, f)

            # Retrieve orders
            orders = self.retrieve_orders(access_token)

            # Get detailed information for each order
            detailed_orders = []
            for order in orders:
                order_id = order['referenceNumber']
                order_details = self.get_order_details(order_id, access_token)
                detailed_order = {
                    'order': order,
                    'details': order_details
                }
                detailed_orders.append(detailed_order)

            # Save orders to file
            with open(ORDERS_FILE, 'w') as f:
                json.dump(detailed_orders, f)

            logger.info(
                f"Successfully refreshed data for {len(detailed_orders)} orders")
            return {'success': True, 'orders_count': len(detailed_orders)}

        except Exception as e:
            logger.error(f"Error refreshing order data: {e}")
            return {'error': str(e)}


# Initialize Tesla API client
tesla_client = TeslaAPIClient()


@app.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        # Check if we have cached data
        if tesla_client.cache:
            dashboard_data = tesla_client.cache['data']
        else:
            # Generate dashboard data
            dashboard_data = generate_dashboard_data()
            if dashboard_data:
                tesla_client.save_cache(dashboard_data)

        return render_template('dashboard.html', data=dashboard_data)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('error.html', error=str(e))


@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """Refresh Tesla order data"""
    try:
        # Refresh data from Tesla API
        result = tesla_client.refresh_order_data()

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400

        # Generate new dashboard data
        dashboard_data = generate_dashboard_data()
        if dashboard_data:
            tesla_client.save_cache(dashboard_data)

        return jsonify({
            'success': True,
            'message': f"Data refreshed successfully. Found {result['orders_count']} orders.",
            'data': dashboard_data
        })

    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/status')
def get_status():
    """Get current order status"""
    try:
        if not os.path.exists(ORDERS_FILE):
            return jsonify({'error': 'No order data available'}), 404

        dashboard_data = generate_dashboard_data()
        return jsonify(dashboard_data)

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/insights')
def get_insights():
    """Get processed insights"""
    try:
        if not os.path.exists(ORDERS_FILE):
            return jsonify({'error': 'No order data available'}), 404

        generator = TeslaInsightsGenerator()
        facts = generator.generate_interesting_facts()
        return jsonify({'facts': facts})

    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/set_language/<language>')
def set_language(language=None):
    """Set the session language"""
    if language in app.config['LANGUAGES']:
        session['language'] = language
    return redirect(request.referrer or url_for('dashboard'))


def generate_dashboard_data():
    """Generate comprehensive dashboard data"""
    try:
        if not os.path.exists(ORDERS_FILE):
            return None

        # Initialize analyzers
        analyzer = TeslaOrderAnalyzer()
        insights_generator = TeslaInsightsGenerator()
        dashboard_generator = TeslaDashboard()

        dashboard_data = {
            'orders': [],
            'insights': {
                'timeline': insights_generator.calculate_order_timeline_insights(),
                'financial': insights_generator.analyze_financial_insights(),
                'delivery': insights_generator.analyze_delivery_insights(),
                'progress': insights_generator.analyze_task_progress_insights(),
                'vehicle': insights_generator.analyze_vehicle_insights()
            },
            'facts': insights_generator.generate_interesting_facts(),
            'last_updated': datetime.now().isoformat()
        }

        # Process each order
        for order_data in analyzer.orders_data:
            order = order_data.get('order', {})

            processed_order = {
                'basic_info': {
                    'reference_number': order.get('referenceNumber'),
                    'status': order.get('orderStatus'),
                    'substatus': order.get('orderSubstatus'),
                    'model': order.get('modelCode', '').upper(),
                    'country': order.get('countryCode'),
                    'vin': order.get('vin', 'Not assigned')
                },
                'timeline': [event.__dict__ for event in analyzer.extract_timeline(order_data)],
                'vehicle_config': analyzer.extract_vehicle_config(order_data).__dict__,
                'financial_info': analyzer.extract_financial_info(order_data).__dict__,
                'delivery_info': analyzer.extract_delivery_info(order_data).__dict__,
                'task_status': analyzer.get_task_completion_status(order_data)
            }

            dashboard_data['orders'].append(processed_order)

        return dashboard_data

    except Exception as e:
        logger.error(f"Error generating dashboard data: {e}")
        return None


if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
