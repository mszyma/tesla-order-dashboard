#!/usr/bin/env python3
"""
Tesla Order Dashboard Generator

Creates a visual dashboard and timeline for Tesla orders.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class TeslaDashboard:
    """Generates a visual dashboard for Tesla orders"""

    def __init__(self, orders_file: str = 'tesla_orders.json'):
        self.orders_file = orders_file
        self.orders_data = self._load_orders()

    def _load_orders(self) -> List[Dict[str, Any]]:
        """Load orders from JSON file"""
        if not os.path.exists(self.orders_file):
            raise FileNotFoundError(
                f"Orders file {self.orders_file} not found")

        with open(self.orders_file, 'r') as f:
            return json.load(f)

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats found in Tesla data"""
        if not date_str or date_str == 'N/A':
            return None

        formats = [
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def create_progress_bar(self, completed: int, total: int, width: int = 30) -> str:
        """Create a visual progress bar"""
        if total == 0:
            return "░" * width

        filled = int((completed / total) * width)
        bar = "█" * filled + "░" * (width - filled)
        percentage = (completed / total) * 100
        return f"{bar} {percentage:.1f}%"

    def create_timeline_visual(self, order_data: Dict[str, Any]) -> List[str]:
        """Create a visual timeline for an order"""
        timeline = []
        order = order_data.get('order', {})

        # Get key dates
        reg_details = order_data.get('details', {}).get(
            'tasks', {}).get('registration', {}).get('orderDetails', {})

        order_placed = self._parse_date(reg_details.get('orderPlacedDate'))
        order_booked = self._parse_date(reg_details.get('orderBookedDate'))

        timeline.append("📅 ORDER TIMELINE")
        timeline.append("─" * 50)

        if order_placed:
            timeline.append(
                f"🚀 {order_placed.strftime('%Y-%m-%d %H:%M')} - Order Placed")

        if order_booked:
            timeline.append(
                f"✅ {order_booked.strftime('%Y-%m-%d %H:%M')} - Order Booked")

        # Add current status
        current_status = order.get('orderStatus', 'Unknown')
        timeline.append(f"📊 Current Status: {current_status}")

        # Add task completion timeline
        tasks = order_data.get('details', {}).get('tasks', {})
        completed_tasks = []
        pending_tasks = []

        for task_id, task_data in tasks.items():
            task_name = task_data.get('strings', {}).get(
                'name', task_id.title())
            if task_data.get('complete'):
                completed_tasks.append(f"✅ {task_name}")
            elif task_data.get('required'):
                pending_tasks.append(f"⏳ {task_name}")

        if completed_tasks:
            timeline.append("\n🎯 COMPLETED TASKS:")
            timeline.extend([f"  {task}" for task in completed_tasks])

        if pending_tasks:
            timeline.append("\n⚠️  PENDING REQUIRED TASKS:")
            timeline.extend([f"  {task}" for task in pending_tasks])

        return timeline

    def create_financial_summary(self, order_data: Dict[str, Any]) -> List[str]:
        """Create a financial summary visualization"""
        summary = []

        # Get financial details
        final_payment_data = order_data.get('details', {}).get(
            'tasks', {}).get('finalPayment', {}).get('data', {})
        financing_details = final_payment_data.get('financingDetails', {})
        tesla_finance = financing_details.get('teslaFinanceDetails', {})

        total_price = tesla_finance.get('adjustedPurchasePrice', 0)
        down_payment = tesla_finance.get('downpaymentToLessor', 0)
        monthly_payment = tesla_finance.get('monthlyPayment', 0)
        interest_rate = tesla_finance.get('interestRate', 0)
        term_months = int(tesla_finance.get('termsInMonths', 0)
                          ) if tesla_finance.get('termsInMonths') else 0

        summary.append("💰 FINANCIAL BREAKDOWN")
        summary.append("─" * 50)

        if total_price:
            summary.append(f"🏷️  Vehicle Price:    {total_price:>15,.2f} PLN")

        if down_payment:
            down_pct = (down_payment / total_price * 100) if total_price else 0
            summary.append(
                f"💳 Down Payment:     {down_payment:>15,.2f} PLN ({down_pct:.1f}%)")

        if monthly_payment and term_months:
            summary.append(
                f"📅 Monthly Payment:  {monthly_payment:>15,.2f} PLN")
            summary.append(
                f"⏰ Term:             {term_months:>15} months ({term_months/12:.1f} years)")

            total_payments = monthly_payment * term_months
            total_cost = down_payment + total_payments

            summary.append(f"💸 Total Payments:   {total_payments:>15,.2f} PLN")
            summary.append(f"💯 Total Cost:       {total_cost:>15,.2f} PLN")

            if interest_rate:
                summary.append(f"📊 Interest Rate:    {interest_rate:>15.2f}%")

        # Add cost per day calculation
        if monthly_payment:
            daily_cost = (monthly_payment * 12) / 365
            summary.append(f"📆 Cost per Day:     {daily_cost:>15,.2f} PLN")

        return summary

    def create_vehicle_summary(self, order_data: Dict[str, Any]) -> List[str]:
        """Create a vehicle configuration summary"""
        summary = []
        order = order_data.get('order', {})

        model_code = order.get('modelCode', '').upper()
        mkt_options = order.get('mktOptions', '')

        summary.append("🚗 VEHICLE CONFIGURATION")
        summary.append("─" * 50)

        summary.append(f"🏷️  Model: Tesla {model_code}")

        # Decode key options
        options = mkt_options.split(',') if mkt_options else []

        # Paint color
        paint_color = "Standard"
        if any('PPSW' in opt for opt in options):
            paint_color = "Pearl White"
        elif any('PPSR' in opt for opt in options):
            paint_color = "Pearl Red"
        elif any('PPSB' in opt for opt in options):
            paint_color = "Pearl Blue"

        summary.append(f"🎨 Paint:        {paint_color}")

        # Wheels
        wheel_type = "Standard"
        if any('WY19' in opt for opt in options):
            wheel_type = "19\" Gemini Wheels"
        elif any('W40' in opt for opt in options):
            wheel_type = "20\" Induction Wheels"

        summary.append(f"🛞 Wheels:       {wheel_type}")

        # Key features
        features = []
        if any('APBS' in opt for opt in options):
            features.append("Autopilot")
        if any('TW01' in opt for opt in options):
            features.append("Tow Hitch")
        if any('IPB' in opt for opt in options):
            features.append("Premium Interior")

        if features:
            summary.append(f"✨ Key Features: {', '.join(features)}")

        summary.append(f"🔧 Total Options: {len(options)}")

        return summary

    def create_delivery_status(self, order_data: Dict[str, Any]) -> List[str]:
        """Create delivery status summary"""
        status = []

        # Get delivery details
        delivery_details = order_data.get('details', {}).get('tasks', {}).get(
            'deliveryDetails', {}).get('regData', {}).get('deliveryDetails', {})
        scheduling = order_data.get('details', {}).get(
            'tasks', {}).get('scheduling', {})

        status.append("🚚 DELIVERY STATUS")
        status.append("─" * 50)

        delivery_type = delivery_details.get('deliveryType', 'Unknown')
        status.append(
            f"📦 Method:       {delivery_type.replace('_', ' ').title()}")

        # Pickup location
        pickup_location_id = delivery_details.get('pickupLocationTrtId')
        if pickup_location_id:
            status.append(f"🏢 Location ID:  {pickup_location_id}")

        # Address
        delivery_address_obj = delivery_details.get('address', {})
        if delivery_address_obj:
            city = delivery_address_obj.get('city', '')
            country = delivery_address_obj.get('countryCode', '')
            if city and country:
                status.append(f"📍 Location:     {city}, {country}")

        # Appointment
        appointment = scheduling.get('deliveryAppointmentDate', '')
        if appointment:
            status.append(f"📅 Appointment:  {appointment}")
        else:
            status.append("📅 Appointment:  Not scheduled")

        # Estimated delivery
        estimated = scheduling.get('estimatedDelivery', '')
        if estimated:
            status.append(f"⏰ Estimated:    {estimated}")

        return status

    def create_task_progress_visual(self, order_data: Dict[str, Any]) -> List[str]:
        """Create a visual task progress summary"""
        progress = []
        tasks = order_data.get('details', {}).get('tasks', {})

        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks.values()
                              if task.get('complete'))
        required_tasks = sum(1 for task in tasks.values()
                             if task.get('required'))
        completed_required = sum(1 for task in tasks.values(
        ) if task.get('complete') and task.get('required'))

        progress.append("📊 TASK PROGRESS")
        progress.append("─" * 50)

        # Overall progress
        overall_bar = self.create_progress_bar(completed_tasks, total_tasks)
        progress.append(
            f"Overall:   {overall_bar} ({completed_tasks}/{total_tasks})")

        # Required tasks progress
        required_bar = self.create_progress_bar(
            completed_required, required_tasks)
        progress.append(
            f"Required:  {required_bar} ({completed_required}/{required_tasks})")

        progress.append("")

        # Individual task status
        task_list = []
        for task_id, task_data in tasks.items():
            task_name = task_data.get('strings', {}).get(
                'name', task_id.title())
            is_complete = task_data.get('complete', False)
            is_required = task_data.get('required', False)

            icon = "✅" if is_complete else (
                "🔄" if task_data.get('enabled') else "⏳")
            required_marker = " *" if is_required else ""

            task_list.append(f"{icon} {task_name}{required_marker}")

        # Sort by completion status
        task_list.sort(key=lambda x: (not x.startswith("✅"), x))
        progress.extend(task_list)

        progress.append("\n* = Required task")

        return progress

    def generate_dashboard(self) -> str:
        """Generate the complete dashboard"""
        dashboard_lines = []

        dashboard_lines.append("╔" + "═" * 78 + "╗")
        dashboard_lines.append(
            "║" + " TESLA ORDER DASHBOARD ".center(78) + "║")
        dashboard_lines.append("╚" + "═" * 78 + "╝")

        for i, order_data in enumerate(self.orders_data, 1):
            order = order_data.get('order', {})
            ref_number = order.get('referenceNumber', 'Unknown')

            dashboard_lines.append(
                f"\n┌─ ORDER {i}: {ref_number} " + "─" * (50 - len(ref_number)))
            dashboard_lines.append("│")

            # Timeline
            timeline = self.create_timeline_visual(order_data)
            for line in timeline:
                dashboard_lines.append(f"│ {line}")

            dashboard_lines.append("│")

            # Task Progress
            progress = self.create_task_progress_visual(order_data)
            for line in progress:
                dashboard_lines.append(f"│ {line}")

            dashboard_lines.append("│")

            # Financial Summary
            financial = self.create_financial_summary(order_data)
            for line in financial:
                dashboard_lines.append(f"│ {line}")

            dashboard_lines.append("│")

            # Vehicle Summary
            vehicle = self.create_vehicle_summary(order_data)
            for line in vehicle:
                dashboard_lines.append(f"│ {line}")

            dashboard_lines.append("│")

            # Delivery Status
            delivery = self.create_delivery_status(order_data)
            for line in delivery:
                dashboard_lines.append(f"│ {line}")

            dashboard_lines.append("└" + "─" * 78)

        # Add footer with generation time
        dashboard_lines.append(
            f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(dashboard_lines)


def main():
    """Main function to run the dashboard generator"""
    try:
        dashboard = TeslaDashboard()

        # Generate and display dashboard
        dashboard_content = dashboard.generate_dashboard()
        print(dashboard_content)

        # Save dashboard to file
        with open('tesla_order_dashboard.txt', 'w') as f:
            f.write(dashboard_content)
        print(f"\n📄 Dashboard saved to: tesla_order_dashboard.txt")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(
            "Please make sure the tesla_orders.json file exists in the current directory.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
