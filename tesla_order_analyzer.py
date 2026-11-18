#!/usr/bin/env python3
"""
Tesla Order Data Analyzer

This script analyzes Tesla order data to extract meaningful insights including:
- Order timeline and milestones
- Financial breakdown and lease details
- Vehicle configuration and options
- Delivery readiness status
- Task completion tracking
- Address and location information
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import re

from tesla_stores import TeslaStore


@dataclass
class TimelineEvent:
    """Represents a timeline event in the order process"""
    date: str
    event: str
    status: str
    details: Optional[str] = None


@dataclass
class VehicleConfiguration:
    """Vehicle configuration and options"""
    model_code: str
    trim_code: str
    market_options: List[str]
    exterior_color: Optional[str] = None
    interior: Optional[str] = None
    wheels: Optional[str] = None
    autopilot: Optional[str] = None


@dataclass
class FinancialBreakdown:
    """Financial information breakdown"""
    order_type: str
    financial_product_type: str
    total_price: Optional[float] = None
    down_payment: Optional[float] = None
    monthly_payment: Optional[float] = None
    interest_rate: Optional[float] = None
    term_months: Optional[int] = None
    amount_due: Optional[float] = None
    reservation_amount: Optional[float] = None
    finance_partner: Optional[str] = None


@dataclass
class DeliveryInfo:
    """Delivery and location information"""
    delivery_type: str
    pickup_location_id: Optional[int] = None
    pickup_location_name: Optional[str] = None
    delivery_address: Optional[str] = None
    appointment_date: Optional[str] = None
    estimated_delivery: Optional[str] = None


class TeslaOrderAnalyzer:
    """Analyzes Tesla order data and extracts meaningful insights"""

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

        # Handle different date formats
        formats = [
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d',
            '%m/%d/%Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def _decode_market_options(self, mkt_options: str) -> List[str]:
        """Decode Tesla market option codes"""
        if not mkt_options:
            return []

        # Common Tesla option codes mapping
        option_codes = {
            'APBS': 'Autopilot',
            'IPB8': 'Interior Premium Black',
            'PPSW': 'Paint Pearl White',
            'SC04': 'Supercharger',
            'MDLY': 'Model Y',
            'WY19P': '19" Gemini Wheels',
            'MTY47': 'Model Y Long Range',
            'STY5S': '5 Seat Interior',
            'CPF0': 'No Cold Weather Package',
            'TW01': 'Tow Hitch',
            'PPSR': 'Paint Pearl Red',
            'PPSB': 'Paint Pearl Blue',
            'PPSG': 'Paint Pearl Gray',
            'W38B': '18" Aero Wheels',
            'W39B': '19" Sport Wheels',
            'W40B': '20" Induction Wheels',
            'W41B': '21" Überturbine Wheels',
            'INBPB': 'All Black Premium Interior',
            'INBPP': 'All Black Partial Premium Interior',
            'INWPW': 'Cream Interior',
        }

        options = mkt_options.split(',')
        decoded_options = []

        for option in options:
            option = option.strip()
            decoded_options.append(option_codes.get(option, option))

        return decoded_options

    def extract_timeline(self, order_data: Dict[str, Any]) -> List[TimelineEvent]:
        """Extract timeline events from order data"""
        timeline = []
        order = order_data.get('order', {})
        details = order_data.get('details', {})
        tasks = details.get('tasks', {})

        # Order placement and booking dates
        reg_details = tasks.get('registration', {}).get('orderDetails', {})
        if reg_details.get('orderPlacedDate'):
            timeline.append(TimelineEvent(
                date=reg_details['orderPlacedDate'],
                event='Order Placed',
                status='COMPLETE',
                details=f"Reference: {order.get('referenceNumber')}"
            ))

        if reg_details.get('orderBookedDate'):
            timeline.append(TimelineEvent(
                date=reg_details['orderBookedDate'],
                event='Order Booked',
                status='COMPLETE',
                details=f"Status: {order.get('orderStatus')}"
            ))

        # Task completion timeline
        task_timeline = [
            ('deliveryDetails', 'Delivery Details'),
            ('tradeIn', 'Trade-In'),
            ('financing', 'Financing'),
            ('registration', 'Registration'),
            ('scheduling', 'Scheduling'),
            ('finalPayment', 'Final Payment'),
            ('deliveryAcceptance', 'Delivery Acceptance'),
        ]

        for task_id, task_name in task_timeline:
            task = tasks.get(task_id, {})
            if task.get('complete'):
                timeline.append(TimelineEvent(
                    # Placeholder since completion dates aren't always available
                    date=datetime.now().isoformat(),
                    event=f'{task_name} Completed',
                    status='COMPLETE',
                    details=f"Task: {task_id}"
                ))

        # Sort timeline by date
        timeline.sort(key=lambda x: self._parse_date(x.date) or datetime.min)
        return timeline

    def extract_vehicle_config(self, order_data: Dict[str, Any]) -> VehicleConfiguration:
        """Extract vehicle configuration details"""
        order = order_data.get('order', {})
        details = order_data.get('details', {})

        model_code = order.get('modelCode', '')
        trim_code = order.get('trimCode', '')
        mkt_options = order.get('mktOptions', '')

        decoded_options = self._decode_market_options(mkt_options)

        # Extract specific configuration details
        exterior_color = next(
            (opt for opt in decoded_options if 'Paint' in opt), None)
        interior = next(
            (opt for opt in decoded_options if 'Interior' in opt), None)
        wheels = next(
            (opt for opt in decoded_options if 'Wheels' in opt), None)
        autopilot = next(
            (opt for opt in decoded_options if 'Autopilot' in opt), None)

        return VehicleConfiguration(
            model_code=model_code,
            trim_code=trim_code,
            market_options=decoded_options,
            exterior_color=exterior_color,
            interior=interior,
            wheels=wheels,
            autopilot=autopilot
        )

    def extract_financial_info(self, order_data: Dict[str, Any]) -> FinancialBreakdown:
        """Extract financial information"""
        details = order_data.get('details', {})
        tasks = details.get('tasks', {})

        financing_task = tasks.get('financing', {})
        final_payment_data = tasks.get('finalPayment', {}).get('data', {})
        financing_details = final_payment_data.get('financingDetails', {})
        tesla_finance = financing_details.get('teslaFinanceDetails', {})

        return FinancialBreakdown(
            order_type=financing_details.get('orderType', 'N/A'),
            financial_product_type=financing_details.get(
                'financialProductType', 'N/A'),
            total_price=tesla_finance.get('adjustedPurchasePrice'),
            down_payment=tesla_finance.get('downpaymentToLessor'),
            monthly_payment=tesla_finance.get('monthlyPayment'),
            interest_rate=tesla_finance.get('interestRate'),
            term_months=int(tesla_finance.get('termsInMonths', 0)
                            ) if tesla_finance.get('termsInMonths') else None,
            amount_due=final_payment_data.get('amountDue'),
            reservation_amount=final_payment_data.get(
                'reservationAmountReceived'),
            finance_partner=tesla_finance.get('financePartnerName')
        )

    def extract_delivery_info(self, order_data: Dict[str, Any]) -> DeliveryInfo:
        """Extract delivery information"""
        details = order_data.get('details', {})
        tasks = details.get('tasks', {})

        delivery_details = tasks.get('deliveryDetails', {}).get(
            'regData', {}).get('deliveryDetails', {})
        scheduling = tasks.get('scheduling', {})
        final_payment_data = tasks.get('finalPayment', {}).get('data', {})

        pickup_location_id = delivery_details.get('pickupLocationTrtId')
        pickup_location_name = None
        if pickup_location_id:
            try:
                pickup_location_name = TeslaStore(pickup_location_id).label
            except:
                pickup_location_name = f"Location ID: {pickup_location_id}"

        # Extract delivery address
        delivery_address_obj = delivery_details.get('address', {})
        delivery_address = None
        if delivery_address_obj:
            address_parts = [
                delivery_address_obj.get('address1', ''),
                delivery_address_obj.get('city', ''),
                delivery_address_obj.get('stateProvince', ''),
                delivery_address_obj.get('zipCode', ''),
                delivery_address_obj.get('countryCode', '')
            ]
            delivery_address = ', '.join(filter(None, address_parts))

        return DeliveryInfo(
            delivery_type=delivery_details.get('deliveryType', 'N/A'),
            pickup_location_id=pickup_location_id,
            pickup_location_name=pickup_location_name,
            delivery_address=delivery_address,
            appointment_date=scheduling.get('deliveryAppointmentDate'),
            estimated_delivery=scheduling.get('estimatedDelivery')
        )

    def get_task_completion_status(self, order_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Get completion status of all tasks"""
        details = order_data.get('details', {})
        tasks = details.get('tasks', {})

        task_status = {}
        for task_id, task_data in tasks.items():
            task_status[task_id] = {
                'id': task_data.get('id', task_id),
                'name': task_data.get('strings', {}).get('name', task_id.title()),
                'complete': task_data.get('complete', False),
                'enabled': task_data.get('enabled', False),
                'required': task_data.get('required', False),
                'status': task_data.get('status', 'N/A'),
                'order': task_data.get('order', 0)
            }

        # Sort by order
        task_status = dict(
            sorted(task_status.items(), key=lambda x: x[1]['order']))
        return task_status

    def generate_comprehensive_report(self) -> str:
        """Generate a comprehensive analysis report"""
        if not self.orders_data:
            return "No order data available."

        report_lines = []
        report_lines.append("="*80)
        report_lines.append("TESLA ORDER COMPREHENSIVE ANALYSIS")
        report_lines.append("="*80)

        for i, order_data in enumerate(self.orders_data, 1):
            order = order_data.get('order', {})

            report_lines.append(
                f"\n{'='*20} ORDER {i}: {order.get('referenceNumber', 'N/A')} {'='*20}")

            # Basic Order Info
            report_lines.append("\n📋 BASIC ORDER INFORMATION")
            report_lines.append("-" * 40)
            report_lines.append(
                f"Reference Number: {order.get('referenceNumber', 'N/A')}")
            report_lines.append(
                f"Status: {order.get('orderStatus', 'N/A')} ({order.get('orderSubstatus', 'N/A')})")
            report_lines.append(
                f"Model: {order.get('modelCode', 'N/A').upper()}")
            report_lines.append(f"Country: {order.get('countryCode', 'N/A')}")
            report_lines.append(
                f"Business Order: {'Yes' if order.get('isB2b') else 'No'}")
            report_lines.append(
                f"Used Vehicle: {'Yes' if order.get('isUsed') else 'No'}")

            # Vehicle Configuration
            config = self.extract_vehicle_config(order_data)
            report_lines.append("\n🚗 VEHICLE CONFIGURATION")
            report_lines.append("-" * 40)
            report_lines.append(f"Model Code: {config.model_code}")
            report_lines.append(f"Trim Code: {config.trim_code}")
            if config.exterior_color:
                report_lines.append(f"Exterior Color: {config.exterior_color}")
            if config.interior:
                report_lines.append(f"Interior: {config.interior}")
            if config.wheels:
                report_lines.append(f"Wheels: {config.wheels}")
            if config.autopilot:
                report_lines.append(f"Autopilot: {config.autopilot}")

            report_lines.append("\nAll Options:")
            for option in config.market_options:
                report_lines.append(f"  • {option}")

            # Financial Information
            financial = self.extract_financial_info(order_data)
            report_lines.append("\n💰 FINANCIAL BREAKDOWN")
            report_lines.append("-" * 40)
            report_lines.append(f"Order Type: {financial.order_type}")
            report_lines.append(
                f"Financial Product: {financial.financial_product_type}")
            if financial.finance_partner:
                report_lines.append(
                    f"Finance Partner: {financial.finance_partner}")
            if financial.total_price:
                report_lines.append(
                    f"Total Price: {financial.total_price:,.2f} PLN")
            if financial.down_payment:
                report_lines.append(
                    f"Down Payment: {financial.down_payment:,.2f} PLN")
            if financial.monthly_payment:
                report_lines.append(
                    f"Monthly Payment: {financial.monthly_payment:,.2f} PLN")
            if financial.interest_rate:
                report_lines.append(
                    f"Interest Rate: {financial.interest_rate:.2f}%")
            if financial.term_months:
                report_lines.append(f"Term: {financial.term_months} months")
            if financial.amount_due:
                report_lines.append(
                    f"Amount Due: {financial.amount_due:,.2f} PLN")
            if financial.reservation_amount:
                report_lines.append(
                    f"Reservation Amount: {financial.reservation_amount:,.2f} PLN")

            # Delivery Information
            delivery = self.extract_delivery_info(order_data)
            report_lines.append("\n🚚 DELIVERY INFORMATION")
            report_lines.append("-" * 40)
            report_lines.append(f"Delivery Type: {delivery.delivery_type}")
            if delivery.pickup_location_name:
                report_lines.append(
                    f"Pickup Location: {delivery.pickup_location_name}")
            if delivery.delivery_address:
                report_lines.append(
                    f"Delivery Address: {delivery.delivery_address}")
            if delivery.appointment_date:
                report_lines.append(
                    f"Appointment Date: {delivery.appointment_date}")
            if delivery.estimated_delivery:
                report_lines.append(
                    f"Estimated Delivery: {delivery.estimated_delivery}")

            # Task Completion Status
            tasks = self.get_task_completion_status(order_data)
            report_lines.append("\n✅ TASK COMPLETION STATUS")
            report_lines.append("-" * 40)
            for task_id, task_info in tasks.items():
                status_icon = "✅" if task_info['complete'] else (
                    "🔄" if task_info['enabled'] else "⏳")
                required_text = " (Required)" if task_info['required'] else ""
                report_lines.append(
                    f"{status_icon} {task_info['name']}: {task_info['status']}{required_text}")

            # Timeline
            timeline = self.extract_timeline(order_data)
            if timeline:
                report_lines.append("\n📅 ORDER TIMELINE")
                report_lines.append("-" * 40)
                for event in timeline:
                    date_obj = self._parse_date(event.date)
                    formatted_date = date_obj.strftime(
                        "%Y-%m-%d %H:%M") if date_obj else event.date
                    details_text = f" - {event.details}" if event.details else ""
                    report_lines.append(
                        f"{formatted_date}: {event.event} ({event.status}){details_text}")

        report_lines.append("\n" + "="*80)
        report_lines.append("END OF ANALYSIS")
        report_lines.append("="*80)

        return "\n".join(report_lines)

    def export_to_json(self, output_file: str = 'tesla_order_analysis.json') -> None:
        """Export structured analysis to JSON"""
        analysis_data = []

        for order_data in self.orders_data:
            order_analysis = {
                'basic_info': {
                    'reference_number': order_data.get('order', {}).get('referenceNumber'),
                    'status': order_data.get('order', {}).get('orderStatus'),
                    'model': order_data.get('order', {}).get('modelCode'),
                    'country': order_data.get('order', {}).get('countryCode'),
                    'is_business': order_data.get('order', {}).get('isB2b'),
                    'is_used': order_data.get('order', {}).get('isUsed')
                },
                'vehicle_config': self.extract_vehicle_config(order_data).__dict__,
                'financial_info': self.extract_financial_info(order_data).__dict__,
                'delivery_info': self.extract_delivery_info(order_data).__dict__,
                'task_status': self.get_task_completion_status(order_data),
                'timeline': [event.__dict__ for event in self.extract_timeline(order_data)]
            }
            analysis_data.append(order_analysis)

        with open(output_file, 'w') as f:
            json.dump(analysis_data, f, indent=2, default=str)

        print(f"Analysis exported to {output_file}")


def main():
    """Main function to run the analyzer"""
    try:
        analyzer = TeslaOrderAnalyzer()

        # Generate and display comprehensive report
        report = analyzer.generate_comprehensive_report()
        print(report)

        # Export structured data
        analyzer.export_to_json()

        # Save report to file
        with open('tesla_order_analysis_report.txt', 'w') as f:
            f.write(report)
        print(f"\nDetailed report saved to: tesla_order_analysis_report.txt")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(
            "Please make sure the tesla_orders.json file exists in the current directory.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
