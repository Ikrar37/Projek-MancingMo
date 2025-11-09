import os
from django.core.management.base import BaseCommand
from products.models import ShippingCost

class Command(BaseCommand):
    help = 'Seed data ongkir untuk kecamatan di Makassar'

    def handle(self, *args, **kwargs):
        # Data ongkir per kecamatan di Makassar
        shipping_data = [
            {'kecamatan': 'Biringkanaya', 'harga': 12000},
            {'kecamatan': 'Bontoala', 'harga': 8000},
            {'kecamatan': 'Kepulauan Sangkarrang', 'harga': 25000},
            {'kecamatan': 'Makassar', 'harga': 9000},
            {'kecamatan': 'Mamajang', 'harga': 8500},
            {'kecamatan': 'Manggala', 'harga': 15000},
            {'kecamatan': 'Mariso', 'harga': 7500},
            {'kecamatan': 'Panakkukang', 'harga': 11000},
            {'kecamatan': 'Rappocini', 'harga': 10000},
            {'kecamatan': 'Tallo', 'harga': 9500},
            {'kecamatan': 'Tamalanrea', 'harga': 13000},
            {'kecamatan': 'Tamalate', 'harga': 10500},
            {'kecamatan': 'Ujung Pandang', 'harga': 7000},
            {'kecamatan': 'Ujung Tanah', 'harga': 8000},
            {'kecamatan': 'Wajo', 'harga': 9000},
        ]
        
        created_count = 0
        updated_count = 0
        
        for data in shipping_data:
            obj, created = ShippingCost.objects.update_or_create(
                kecamatan=data['kecamatan'],
                defaults={'harga': data['harga']}
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created: {data["kecamatan"]} - Rp {data["harga"]}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated: {data["kecamatan"]} - Rp {data["harga"]}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded {created_count} new and updated {updated_count} shipping costs!'
            )
        )