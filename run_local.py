#!/usr/bin/env python3
"""
Local development server for Tesla Order Dashboard
Runs on port 8000 to avoid conflicts with macOS AirPlay Receiver
"""

import os
import sys

# Set port to avoid conflicts
os.environ['PORT'] = '8000'

# Import and run the Flask app
if __name__ == '__main__':
    try:
        from app import app
        print("🚗 Tesla Order Dashboard")
        print("=" * 50)
        print("Starting local development server...")
        print("Dashboard will be available at: http://localhost:8000")
        print("Press Ctrl+C to stop the server")
        print("=" * 50)

        app.run(
            debug=True,
            host='0.0.0.0',
            port=8000,
            use_reloader=False  # Avoid double startup messages
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you have Flask installed: pip3 install Flask")
        print("2. Make sure you have tesla_orders.json (run tesla_order_status.py first)")
        print("3. Check that port 8000 is not in use")
        sys.exit(1)
