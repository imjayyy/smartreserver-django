# shop_api/management/commands/initialize_shops.py
from django.core.management.base import BaseCommand
from shop_api.models import Shop, Service

class Command(BaseCommand):
    help = 'Initialize default shops and services'

    def handle(self, *args, **kwargs):
        # Create a default shop
        shop, created = Shop.objects.get_or_create(
            shop_id="barber_shop_1",
            defaults={
                'shop_name': "Tony's Barber Shop",
                'address': "123 Main St, New York, NY 10001",
                'phone': "+1 (555) 123-4567",
                'operating_hours': {
                    'monday': '9:00 AM - 7:00 PM',
                    'tuesday': '9:00 AM - 7:00 PM',
                    'wednesday': '9:00 AM - 7:00 PM',
                    'thursday': '9:00 AM - 7:00 PM',
                    'friday': '9:00 AM - 8:00 PM',
                    'saturday': '10:00 AM - 6:00 PM',
                    'sunday': 'Closed'
                },
                'reservation_policy': {
                    'max_reservations_per_hour': 5,
                    'cancellation_hours': 24,
                    'deposit_required': False
                },
                'timezone': 'America/New_York'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Created shop: {shop.shop_name}'))
            
            # Create services for the shop
            services = [
                {
                    'service_id': 'haircut_1',
                    'name': 'Standard Haircut',
                    'description': 'Professional haircut with styling',
                    'price': 25.00,
                    'currency': 'USD',
                    'duration_minutes': 30
                },
                {
                    'service_id': 'beard_trim_1',
                    'name': 'Beard Trim',
                    'description': 'Professional beard trimming and shaping',
                    'price': 15.00,
                    'currency': 'USD',
                    'duration_minutes': 20
                },
                {
                    'service_id': 'haircut_beard_1',
                    'name': 'Haircut + Beard',
                    'description': 'Complete grooming package',
                    'price': 35.00,
                    'currency': 'USD',
                    'duration_minutes': 45
                }
            ]
            
            for service_data in services:
                Service.objects.create(
                    shop=shop,
                    **service_data
                )
            
            self.stdout.write(self.style.SUCCESS('✅ Created 3 services for the shop'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ Shop already exists'))
        
        # Create a second shop for testing
        shop2, created2 = Shop.objects.get_or_create(
            shop_id="spa_center_1",
            defaults={
                'shop_name': "Relaxation Spa Center",
                'address': "456 Wellness Ave, Los Angeles, CA 90001",
                'phone': "+1 (555) 987-6543",
                'operating_hours': {
                    'monday': '10:00 AM - 8:00 PM',
                    'tuesday': '10:00 AM - 8:00 PM',
                    'wednesday': '10:00 AM - 8:00 PM',
                    'thursday': '10:00 AM - 8:00 PM',
                    'friday': '10:00 AM - 9:00 PM',
                    'saturday': '9:00 AM - 7:00 PM',
                    'sunday': '11:00 AM - 5:00 PM'
                },
                'reservation_policy': {
                    'max_reservations_per_hour': 8,
                    'cancellation_hours': 48,
                    'deposit_required': True,
                    'deposit_amount': 20.00
                },
                'timezone': 'America/Los_Angeles'
            }
        )
        
        if created2:
            self.stdout.write(self.style.SUCCESS(f'✅ Created second shop: {shop2.shop_name}'))
            
            # Create services for the second shop
            spa_services = [
                {
                    'service_id': 'massage_1',
                    'name': 'Swedish Massage',
                    'description': 'Relaxing full-body massage',
                    'price': 80.00,
                    'currency': 'USD',
                    'duration_minutes': 60
                },
                {
                    'service_id': 'facial_1',
                    'name': 'Anti-Aging Facial',
                    'description': 'Rejuvenating facial treatment',
                    'price': 65.00,
                    'currency': 'USD',
                    'duration_minutes': 45
                },
                {
                    'service_id': 'package_1',
                    'name': 'Spa Day Package',
                    'description': 'Massage + Facial + Manicure',
                    'price': 150.00,
                    'currency': 'USD',
                    'duration_minutes': 120
                }
            ]
            
            for service_data in spa_services:
                Service.objects.create(
                    shop=shop2,
                    **service_data
                )
            
            self.stdout.write(self.style.SUCCESS('✅ Created 3 services for the spa'))
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Successfully initialized shops database!'))
        self.stdout.write(f'Total shops: {Shop.objects.count()}')
        self.stdout.write(f'Total services: {Service.objects.count()}')