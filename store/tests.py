from django.test import TestCase
from django.urls import reverse

from product.models import Brand, Category
from product.tests import make_product

from .views import PRODUCTS_PER_PAGE


class HomeViewTests(TestCase):
    def test_home_renders_without_data(self):
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)

    def test_home_renders_with_products(self):
        make_product()
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)


class ShopViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Shoes', image='c.jpg')
        self.other_category = Category.objects.create(name='Hats', image='c.jpg')
        self.brand = Brand.objects.create(name='Acme', logo='b.jpg')
        self.cheap = make_product('Cheap', price='5.00', category=self.category, brand=self.brand)
        self.pricey = make_product('Pricey', price='50.00', category=self.category, brand=self.brand)
        self.hat = make_product('Hat', price='20.00', category=self.other_category, brand=self.brand)

    def test_filter_by_category(self):
        response = self.client.get(reverse('shop'), {'category_id': self.category.pk})
        self.assertEqual(list(response.context['products']), [self.cheap, self.pricey])

    def test_sort_desc(self):
        response = self.client.get(reverse('shop'), {'sort_by': 'price_desc'})
        self.assertEqual(list(response.context['products']), [self.pricey, self.hat, self.cheap])

    def test_unknown_sort_falls_back_to_default(self):
        response = self.client.get(reverse('shop'), {'sort_by': '"><script>'})
        self.assertEqual(response.context['sort_by'], 'price_asc')
        self.assertNotContains(response, '"><script>')

    def test_empty_filters_are_ignored(self):
        response = self.client.get(reverse('shop'), {'category_id': '', 'brand_id': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 3)

    def test_non_numeric_filter_is_404_not_500(self):
        # Regression: get_object_or_404(..., id='abc') raised ValueError -> 500.
        for param in ('category_id', 'brand_id'):
            response = self.client.get(reverse('shop'), {param: 'abc'})
            self.assertEqual(response.status_code, 404, param)

    def test_unknown_filter_id_is_404(self):
        response = self.client.get(reverse('shop'), {'brand_id': 999})
        self.assertEqual(response.status_code, 404)

    def test_pagination(self):
        for i in range(PRODUCTS_PER_PAGE):
            make_product(f'Extra {i}', category=self.category, brand=self.brand)
        first = self.client.get(reverse('shop'))
        self.assertEqual(len(first.context['products']), PRODUCTS_PER_PAGE)
        second = self.client.get(reverse('shop'), {'page': 2})
        self.assertEqual(len(second.context['products']), 3)
        self.assertContains(first, 'page=2')
