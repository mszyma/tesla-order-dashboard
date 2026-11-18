#!/usr/bin/env python3
"""
Tesla Order Insights Generator

Generates specific insights and interesting findings from Tesla order data.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re


class TeslaInsightsGenerator:
    """Generates interesting insights from Tesla order data"""

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

    def calculate_order_timeline_insights(self) -> Dict[str, Any]:
        """Calculate timeline-based insights"""
        insights = {}

        for order_data in self.orders_data:
            order = order_data.get('order', {})
            ref_number = order.get('referenceNumber', 'Unknown')

            # Get key dates
            reg_details = order_data.get('details', {}).get(
                'tasks', {}).get('registration', {}).get('orderDetails', {})

            order_placed = self._parse_date(reg_details.get('orderPlacedDate'))
            order_booked = self._parse_date(reg_details.get('orderBookedDate'))

            if order_placed and order_booked:
                booking_delay = (
                    order_booked - order_placed).total_seconds() / 60  # in minutes
                insights[f'{ref_number}_booking_delay'] = {
                    'order_placed': order_placed.strftime('%Y-%m-%d %H:%M'),
                    'order_booked': order_booked.strftime('%Y-%m-%d %H:%M'),
                    'delay_minutes': round(booking_delay, 1),
                    'delay_description': self._describe_delay(booking_delay)
                }

            # Calculate days since order
            if order_placed:
                days_since_order = (datetime.now() - order_placed).days
                insights[f'{ref_number}_order_age'] = {
                    'days_since_order': days_since_order,
                    'weeks_since_order': round(days_since_order / 7, 1),
                    'order_date': order_placed.strftime('%Y-%m-%d')
                }

        return insights

    def _describe_delay(self, minutes: float) -> str:
        """Describe delay in human-readable terms"""
        if minutes < 1:
            return "Almost instant"
        elif minutes < 60:
            return f"{int(minutes)} minutes"
        elif minutes < 1440:  # 24 hours
            hours = minutes / 60
            return f"{hours:.1f} hours"
        else:
            days = minutes / 1440
            return f"{days:.1f} days"

    def analyze_financial_insights(self) -> Dict[str, Any]:
        """Generate financial insights"""
        insights = {}

        for order_data in self.orders_data:
            order = order_data.get('order', {})
            ref_number = order.get('referenceNumber', 'Unknown')

            # Get financial details
            final_payment_data = order_data.get('details', {}).get(
                'tasks', {}).get('finalPayment', {}).get('data', {})
            financing_details = final_payment_data.get('financingDetails', {})
            tesla_finance = financing_details.get('teslaFinanceDetails', {})

            total_price = tesla_finance.get('adjustedPurchasePrice', 0)
            down_payment = tesla_finance.get('downpaymentToLessor', 0)
            monthly_payment = tesla_finance.get('monthlyPayment', 0)
            interest_rate = tesla_finance.get('interestRate', 0)
            term_months = int(tesla_finance.get('termsInMonths', 0)) if tesla_finance.get(
                'termsInMonths') else 0

            if total_price and down_payment and monthly_payment and term_months:
                # Calculate total cost of lease
                total_payments = monthly_payment * term_months
                total_cost = down_payment + total_payments

                # Calculate effective cost per month including down payment
                effective_monthly = total_cost / term_months

                # Calculate down payment percentage
                down_payment_pct = (down_payment / total_price) * 100

                # Calculate total interest paid (approximate)
                financed_amount = total_price - down_payment
                total_interest = total_payments - financed_amount

                insights[f'{ref_number}_financial'] = {
                    'total_vehicle_price': f"{total_price:,.2f} PLN",
                    'down_payment': f"{down_payment:,.2f} PLN",
                    'down_payment_percentage': f"{down_payment_pct:.1f}%",
                    'monthly_payment': f"{monthly_payment:,.2f} PLN",
                    'term_months': term_months,
                    'term_years': round(term_months / 12, 1),
                    'total_payments': f"{total_payments:,.2f} PLN",
                    'total_lease_cost': f"{total_cost:,.2f} PLN",
                    'effective_monthly_cost': f"{effective_monthly:,.2f} PLN",
                    'interest_rate': f"{interest_rate:.2f}%",
                    'estimated_total_interest': f"{total_interest:,.2f} PLN",
                    'cost_per_year': f"{(monthly_payment * 12):,.2f} PLN",
                    'cost_per_day': f"{(monthly_payment * 12 / 365):,.2f} PLN"
                }

        return insights

    def analyze_delivery_insights(self) -> Dict[str, Any]:
        """Generate delivery-related insights"""
        insights = {}

        for order_data in self.orders_data:
            order = order_data.get('order', {})
            ref_number = order.get('referenceNumber', 'Unknown')

            # Get delivery details
            delivery_details = order_data.get('details', {}).get('tasks', {}).get(
                'deliveryDetails', {}).get('regData', {}).get('deliveryDetails', {})

            delivery_type = delivery_details.get('deliveryType', 'Unknown')
            pickup_location_id = delivery_details.get('pickupLocationTrtId')

            # Analyze delivery address
            delivery_address_obj = delivery_details.get('address', {})
            if delivery_address_obj:
                city = delivery_address_obj.get('city', '')
                state = delivery_address_obj.get('stateProvince', '')
                country = delivery_address_obj.get('countryCode', '')
                zip_code = delivery_address_obj.get('zipCode', '')

                insights[f'{ref_number}_delivery'] = {
                    'delivery_method': delivery_type.replace('_', ' ').title(),
                    'pickup_location_id': pickup_location_id,
                    'delivery_city': city,
                    'delivery_state': state,
                    'delivery_country': country,
                    'delivery_zip': zip_code,
                    'is_pickup': delivery_type == 'PICKUP_SERVICE_CENTER',
                    'is_home_delivery': 'DELIVERY' in delivery_type.upper()
                }

        return insights

    def analyze_task_progress_insights(self) -> Dict[str, Any]:
        """Analyze task completion progress"""
        insights = {}

        for order_data in self.orders_data:
            order = order_data.get('order', {})
            ref_number = order.get('referenceNumber', 'Unknown')

            tasks = order_data.get('details', {}).get('tasks', {})

            total_tasks = 0
            completed_tasks = 0
            required_tasks = 0
            completed_required_tasks = 0

            task_status = {}

            for task_id, task_data in tasks.items():
                total_tasks += 1
                is_complete = task_data.get('complete', False)
                is_required = task_data.get('required', False)

                if is_complete:
                    completed_tasks += 1

                if is_required:
                    required_tasks += 1
                    if is_complete:
                        completed_required_tasks += 1

                task_status[task_id] = {
                    'name': task_data.get('strings', {}).get('name', task_id.title()),
                    'complete': is_complete,
                    'required': is_required,
                    'status': task_data.get('status', 'N/A'),
                    'enabled': task_data.get('enabled', False)
                }

            completion_pct = (completed_tasks / total_tasks) * \
                100 if total_tasks > 0 else 0
            required_completion_pct = (
                completed_required_tasks / required_tasks) * 100 if required_tasks > 0 else 0

            insights[f'{ref_number}_progress'] = {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'required_tasks': required_tasks,
                'completed_required_tasks': completed_required_tasks,
                'overall_completion_percentage': round(completion_pct, 1),
                'required_completion_percentage': round(required_completion_pct, 1),
                'remaining_tasks': total_tasks - completed_tasks,
                'remaining_required_tasks': required_tasks - completed_required_tasks,
                'task_details': task_status
            }

        return insights

    def analyze_vehicle_insights(self) -> Dict[str, Any]:
        """Analyze vehicle configuration insights"""
        insights = {}

        for order_data in self.orders_data:
            order = order_data.get('order', {})
            ref_number = order.get('referenceNumber', 'Unknown')

            model_code = order.get('modelCode', '').upper()
            mkt_options = order.get('mktOptions', '')

            # Decode options
            options = mkt_options.split(',') if mkt_options else []

            # Analyze options
            has_autopilot = any(
                'APBS' in opt or 'Autopilot' in opt for opt in options)
            has_tow_hitch = any(
                'TW01' in opt or 'Tow' in opt for opt in options)
            has_premium_interior = any(
                'IPB' in opt or 'Premium' in opt for opt in options)

            # Determine wheel type
            wheel_type = 'Standard'
            for opt in options:
                if 'WY19' in opt:
                    wheel_type = '19" Gemini Wheels'
                elif 'W40' in opt:
                    wheel_type = '20" Induction Wheels'
                elif 'W41' in opt:
                    wheel_type = '21" Überturbine Wheels'

            # Determine paint color
            paint_color = 'Standard'
            for opt in options:
                if 'PPSW' in opt:
                    paint_color = 'Pearl White'
                elif 'PPSR' in opt:
                    paint_color = 'Pearl Red'
                elif 'PPSB' in opt:
                    paint_color = 'Pearl Blue'
                elif 'PPSG' in opt:
                    paint_color = 'Pearl Gray'

            insights[f'{ref_number}_vehicle'] = {
                'model': model_code,
                'total_options': len(options),
                'paint_color': paint_color,
                'wheel_type': wheel_type,
                'has_autopilot': has_autopilot,
                'has_tow_hitch': has_tow_hitch,
                'has_premium_interior': has_premium_interior,
                'all_options': options
            }

        return insights

    def generate_interesting_facts(self) -> List[str]:
        """Generate interesting facts about the order"""
        facts = []

        timeline_insights = self.calculate_order_timeline_insights()
        financial_insights = self.analyze_financial_insights()
        delivery_insights = self.analyze_delivery_insights()
        progress_insights = self.analyze_task_progress_insights()
        vehicle_insights = self.analyze_vehicle_insights()

        for order_data in self.orders_data:
            order = order_data.get('order', {})
            ref_number = order.get('referenceNumber', 'Unknown')

            # Timeline facts
            if f'{ref_number}_booking_delay' in timeline_insights:
                delay_info = timeline_insights[f'{ref_number}_booking_delay']
                facts.append(
                    f"⏱️  Your order was booked {delay_info['delay_description']} after placement")

            if f'{ref_number}_order_age' in timeline_insights:
                age_info = timeline_insights[f'{ref_number}_order_age']
                facts.append(
                    f"📅 Your order is {age_info['days_since_order']} days old ({age_info['weeks_since_order']} weeks)")

            # Financial facts
            if f'{ref_number}_financial' in financial_insights:
                fin_info = financial_insights[f'{ref_number}_financial']
                facts.append(
                    f"💰 Your effective monthly cost (including down payment) is {fin_info['effective_monthly_cost']}")
                facts.append(
                    f"💳 You're paying {fin_info['cost_per_day']} per day for your Tesla")
                facts.append(
                    f"📊 Your down payment covers {fin_info['down_payment_percentage']} of the vehicle cost")
                facts.append(
                    f"🏦 Over {fin_info['term_years']} years, you'll pay approximately {fin_info['estimated_total_interest']} in interest")

            # Progress facts
            if f'{ref_number}_progress' in progress_insights:
                prog_info = progress_insights[f'{ref_number}_progress']
                facts.append(
                    f"✅ You've completed {prog_info['completed_tasks']}/{prog_info['total_tasks']} tasks ({prog_info['overall_completion_percentage']}%)")
                facts.append(
                    f"🎯 Required tasks completion: {prog_info['completed_required_tasks']}/{prog_info['required_tasks']} ({prog_info['required_completion_percentage']}%)")

                if prog_info['remaining_required_tasks'] > 0:
                    facts.append(
                        f"⚠️  You have {prog_info['remaining_required_tasks']} required tasks remaining")
                else:
                    facts.append(f"🎉 All required tasks are completed!")

            # Vehicle facts
            if f'{ref_number}_vehicle' in vehicle_insights:
                veh_info = vehicle_insights[f'{ref_number}_vehicle']
                facts.append(
                    f"🚗 Your {veh_info['model']} has {veh_info['total_options']} configuration options")
                facts.append(f"🎨 Paint color: {veh_info['paint_color']}")
                facts.append(f"🛞 Wheels: {veh_info['wheel_type']}")

                if veh_info['has_autopilot']:
                    facts.append(f"🤖 Your vehicle includes Autopilot")
                if veh_info['has_tow_hitch']:
                    facts.append(f"🚛 Your vehicle has a tow hitch")
                if veh_info['has_premium_interior']:
                    facts.append(f"✨ Your vehicle has premium interior")

            # Delivery facts
            if f'{ref_number}_delivery' in delivery_insights:
                del_info = delivery_insights[f'{ref_number}_delivery']
                facts.append(
                    f"📍 Delivery method: {del_info['delivery_method']}")
                facts.append(
                    f"🏢 Pickup location ID: {del_info['pickup_location_id']}")
                facts.append(
                    f"🌍 Delivery location: {del_info['delivery_city']}, {del_info['delivery_country']}")

        return facts

    def generate_comprehensive_insights_report(self) -> str:
        """Generate a comprehensive insights report"""
        report_lines = []
        report_lines.append("🔍 TESLA ORDER INSIGHTS & INTERESTING FACTS")
        report_lines.append("=" * 60)

        # Get all insights
        timeline_insights = self.calculate_order_timeline_insights()
        financial_insights = self.analyze_financial_insights()
        delivery_insights = self.analyze_delivery_insights()
        progress_insights = self.analyze_task_progress_insights()
        vehicle_insights = self.analyze_vehicle_insights()
        interesting_facts = self.generate_interesting_facts()

        # Interesting Facts Section
        report_lines.append("\n🌟 INTERESTING FACTS")
        report_lines.append("-" * 30)
        for fact in interesting_facts:
            report_lines.append(fact)

        # Detailed Insights
        report_lines.append("\n📊 DETAILED INSIGHTS")
        report_lines.append("-" * 30)

        if timeline_insights:
            report_lines.append("\n⏰ Timeline Analysis:")
            for key, value in timeline_insights.items():
                if isinstance(value, dict):
                    report_lines.append(f"  {key}:")
                    for k, v in value.items():
                        report_lines.append(f"    {k}: {v}")

        if financial_insights:
            report_lines.append("\n💰 Financial Analysis:")
            for key, value in financial_insights.items():
                if isinstance(value, dict):
                    report_lines.append(f"  {key.replace('_financial', '')}:")
                    for k, v in value.items():
                        report_lines.append(
                            f"    {k.replace('_', ' ').title()}: {v}")

        if progress_insights:
            report_lines.append("\n📈 Progress Analysis:")
            for key, value in progress_insights.items():
                if isinstance(value, dict) and 'task_details' in value:
                    report_lines.append(f"  {key.replace('_progress', '')}:")
                    report_lines.append(
                        f"    Overall Progress: {value['overall_completion_percentage']}%")
                    report_lines.append(
                        f"    Required Tasks: {value['completed_required_tasks']}/{value['required_tasks']}")

        if vehicle_insights:
            report_lines.append("\n🚗 Vehicle Analysis:")
            for key, value in vehicle_insights.items():
                if isinstance(value, dict):
                    report_lines.append(f"  {key.replace('_vehicle', '')}:")
                    for k, v in value.items():
                        if k != 'all_options':  # Skip the detailed options list
                            report_lines.append(
                                f"    {k.replace('_', ' ').title()}: {v}")

        return "\n".join(report_lines)


def main():
    """Main function to run the insights generator"""
    try:
        generator = TeslaInsightsGenerator()

        # Generate and display insights
        report = generator.generate_comprehensive_insights_report()
        print(report)

        # Save report to file
        with open('tesla_order_insights.txt', 'w') as f:
            f.write(report)
        print(f"\n📄 Insights report saved to: tesla_order_insights.txt")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(
            "Please make sure the tesla_orders.json file exists in the current directory.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
