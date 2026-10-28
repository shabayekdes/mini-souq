from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse

from product.tests import make_product

from .models import MAX_QUANTITY_PER_ITEM, Cart, CartItem, Order, OrderItem

User = get_user_model()


class CartTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', 'alice@example.com', 'pw-alice-123!')
        self.other = User.objects.create_user('bob', 'bob@example.com', 'pw-bob-123!')
        self.product = make_product('Shirt', price='10.00')
        self.client.force_login(self.user)

    def add(self, product=None, quantity=1):
        product = product or self.product
        return self.client.post(reverse('add_to_cart', args=[product.pk]), {'quantity': quantity})


class AddToCartTests(CartTestCase):
    def test_requires_login(self):
        self.client.logout()
        response = self.add()
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('account_login'), response.url)
        self.assertFalse(CartItem.objects.exists())

    def test_get_is_not_allowed(self):
        # Regression: a GET (e.g. an <img> on another site) used to modify the cart.
        response = self.client.get(reverse('add_to_cart', args=[self.product.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertFalse(CartItem.objects.exists())

    def test_uses_submitted_quantity_and_accumulates(self):
        # Regression: the quantity field on the product page was ignored.
        self.add(quantity=3)
        self.add(quantity=2)
        self.assertEqual(CartItem.objects.get().quantity, 5)

    def test_rejects_invalid_quantities(self):
        for quantity in (0, -1, 'abc', MAX_QUANTITY_PER_ITEM + 1):
            response = self.add(quantity=quantity)
            self.assertEqual(response.status_code, 302, quantity)
        self.assertFalse(CartItem.objects.exists())

    def test_quantity_is_capped(self):
        self.add(quantity=MAX_QUANTITY_PER_ITEM)
        self.add(quantity=5)
        self.assertEqual(CartItem.objects.get().quantity, MAX_QUANTITY_PER_ITEM)

    def test_unknown_product_is_404(self):
        response = self.client.post(reverse('add_to_cart', args=[999]), {'quantity': 1})
        self.assertEqual(response.status_code, 404)


class CartDetailTests(CartTestCase):
    def test_user_without_cart_sees_empty_cart(self):
        # Regression: get_object_or_404(Cart, ...) returned 404 for new users.
        response = self.client.get(reverse('cart_detail'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_price'], 0)

    def test_total_uses_sale_price(self):
        sale = make_product('Sale', price='20.00', is_sale=True, sale_price='15.00')
        self.add(quantity=2)          # 2 x 10.00
        self.add(sale, quantity=1)    # 1 x 15.00 (not 20.00)
        response = self.client.get(reverse('cart_detail'))
        self.assertEqual(response.context['total_price'], Decimal('35.00'))
        self.assertContains(response, '$35.00')
        self.assertNotContains(response, '$106.94')

    def test_only_own_items_listed(self):
        other_cart = Cart.objects.create(user=self.other)
        CartItem.objects.create(cart=other_cart, product=make_product('Secret'), quantity=1)
        response = self.client.get(reverse('cart_detail'))
        self.assertNotContains(response, 'Secret')


class RemoveFromCartTests(CartTestCase):
    def test_cannot_remove_another_users_item(self):
        # Regression (IDOR): any logged-in user could delete any CartItem by id.
        other_cart = Cart.objects.create(user=self.other)
        item = CartItem.objects.create(cart=other_cart, product=self.product)
        response = self.client.post(reverse('remove_from_cart', args=[item.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(CartItem.objects.filter(pk=item.pk).exists())

    def test_get_is_not_allowed(self):
        self.add()
        item = CartItem.objects.get()
        response = self.client.get(reverse('remove_from_cart', args=[item.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(CartItem.objects.filter(pk=item.pk).exists())

    def test_remove_own_item(self):
        self.add()
        item = CartItem.objects.get()
        response = self.client.post(reverse('remove_from_cart', args=[item.pk]))
        self.assertRedirects(response, reverse('cart_detail'))
        self.assertFalse(CartItem.objects.exists())


class CheckoutTests(CartTestCase):
    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('checkout_page'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('account_login'), response.url)

    def test_empty_cart_redirects_to_shop(self):
        self.assertRedirects(self.client.get(reverse('checkout_page')), reverse('shop'))
        Cart.objects.create(user=self.user)
        self.assertRedirects(self.client.get(reverse('checkout_page')), reverse('shop'))

    def test_checkout_page_shows_real_total(self):
        self.add(quantity=3)
        response = self.client.get(reverse('checkout_page'))
        self.assertEqual(response.context['total_price'], Decimal('30.00'))
        self.assertNotContains(response, '$106.94')

    def test_order_totals_are_computed_on_server(self):
        sale = make_product('Sale', price='20.00', is_sale=True, sale_price='15.00')
        self.add(quantity=2)
        self.add(sale, quantity=1)
        response = self.client.post(reverse('checkout_page'), {
            # Client-submitted values must be ignored.
            'total_amount': '0.01', 'user': self.other.pk,
        })
        self.assertRedirects(response, reverse('order_success'))

        order = Order.objects.get()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total_amount, Decimal('35.00'))
        items = {i.product.name: i for i in OrderItem.objects.filter(order=order)}
        # OrderItem.price stores the unit price.
        self.assertEqual(items['Shirt'].price, Decimal('10.00'))
        self.assertEqual(items['Shirt'].quantity, 2)
        self.assertEqual(items['Sale'].price, Decimal('15.00'))
        self.assertEqual(sum(i.line_total() for i in items.values()), order.total_amount)
        self.assertFalse(CartItem.objects.exists())

    def test_resubmission_does_not_create_second_order(self):
        self.add()
        self.client.post(reverse('checkout_page'))
        response = self.client.post(reverse('checkout_page'))
        self.assertRedirects(response, reverse('shop'))
        self.assertEqual(Order.objects.count(), 1)

    def test_failure_rolls_back_order_and_keeps_cart(self):
        self.add(quantity=2)
        with mock.patch.object(OrderItem.objects, 'bulk_create', side_effect=DatabaseError):
            with self.assertRaises(DatabaseError), self.assertLogs('django.request', 'ERROR'):
                self.client.post(reverse('checkout_page'))
        self.assertFalse(Order.objects.exists())
        self.assertEqual(CartItem.objects.get().quantity, 2)

    def test_order_success_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('order_success')).status_code, 302)


class CartCountContextProcessorTests(CartTestCase):
    def test_cart_count(self):
        self.add()
        self.add(make_product('Other'))
        response = self.client.get(reverse('home'))
        self.assertEqual(response.context['cart_count'], 2)

    def test_anonymous_cart_count_is_zero(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('home')).context['cart_count'], 0)
