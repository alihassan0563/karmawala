from django.core.management.base import BaseCommand
from inventory.models import Category

class Command(BaseCommand):
    help = 'Populate default men\'s clothing categories'

    def handle(self, *args, **options):
        categories = [
            {
                'name': 'Shirts',
                'description': 'Casual shirts, dress shirts, polo shirts, and t-shirts'
            },
            {
                'name': 'Pants',
                'description': 'Jeans, chinos, dress pants, and casual trousers'
            },
            {
                'name': 'Jackets & Coats',
                'description': 'Blazers, leather jackets, winter coats, and casual jackets'
            },
            {
                'name': 'Suits',
                'description': 'Formal suits, business suits, and suit separates'
            },
            {
                'name': 'Shoes',
                'description': 'Dress shoes, casual shoes, sneakers, and boots'
            },
            {
                'name': 'Accessories',
                'description': 'Belts, ties, watches, wallets, and bags'
            },
            {
                'name': 'Underwear & Socks',
                'description': 'Undergarments, socks, and loungewear'
            },
            {
                'name': 'Sportswear',
                'description': 'Athletic wear, gym clothes, and sports accessories'
            },
            {
                'name': 'Traditional Wear',
                'description': 'Kurtas, shalwar kameez, and traditional Pakistani clothing'
            },
            {
                'name': 'Sweaters & Hoodies',
                'description': 'Pullover sweaters, cardigans, hoodies, and sweatshirts'
            }
        ]

        created_count = 0
        for category_data in categories:
            category, created = Category.objects.get_or_create(
                name=category_data['name'],
                defaults={'description': category_data['description']}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new categories')
        )
