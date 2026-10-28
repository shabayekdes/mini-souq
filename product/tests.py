from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Brand, Category, Product


def make_product(name='Shirt', price='10.00', is_sale=False, sale_price='0', category=None, brand=None):
    category = category or Category.objects.create(name='Clothes', image='uploads/category/c.jpg')
    brand = brand or Brand.objects.create(name='Acme', logo='uploads/brands/b.jpg')
    return Product.objects.create(
        name=name,
        slug=name.lower().replace(' ', '-'),
        price=Decimal(price),
        is_sale=is_sale,
        sale_price=Decimal(sale_price),
        category=category,
        brand=brand,
        image='uploads/product/p.jpg',
    )


class ProductModelTests(TestCase):
    def test_current_price_uses_sale_price_only_when_on_sale(self):
        self.assertEqual(make_product('A', price='10.00').current_price, Decimal('10.00'))
        on_sale = make_product('B', price='10.00', is_sale=True, sale_price='7.50')
        self.assertEqual(on_sale.current_price, Decimal('7.50'))

    def test_clean_rejects_invalid_sale_price(self):
        for sale_price in ('0', '10.00', '12.00'):
            product = make_product(f'P{sale_price}', price='10.00')
            product.is_sale = True
            product.sale_price = Decimal(sale_price)
            with self.assertRaises(ValidationError, msg=sale_price):
                product.clean()

    def test_clean_rejects_negative_price(self):
        product = make_product()
        product.price = Decimal('-1')
        with self.assertRaises(ValidationError):
            product.clean()

    def test_url_helpers_reverse(self):
        # Regression: get_add_to_cart_url used a non-existent "checkout:" namespace
        # and Category.get_absolute_url pointed at a product page.
        product = make_product()
        self.assertEqual(product.get_add_to_cart_url(), reverse('add_to_cart', args=[product.pk]))
        self.assertEqual(
            product.category.get_absolute_url(),
            f"{reverse('shop')}?category_id={product.category.pk}",
        )


class ProductDetailsViewTests(TestCase):
    def test_details_page_renders(self):
        product = make_product(is_sale=True, sale_price='5.00')
        response = self.client.get(reverse('product_details', args=[product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.name)

    def test_unknown_product_is_404(self):
        response = self.client.get(reverse('product_details', args=[999]))
        self.assertEqual(response.status_code, 404)
