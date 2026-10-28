from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

class Category(models.Model):
	name = models.CharField(max_length=50)
	# home_class = models.CharField(max_length=50)
	order = models.IntegerField(default=0)
	image = models.ImageField(upload_to='uploads/category/')

	def __str__(self):
		return self.name
	def get_absolute_url(self):
		return f'{reverse("shop")}?category_id={self.pk}'

	class Meta:
		verbose_name_plural = 'categories'

class Brand(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='uploads/brands/')
	
    def __str__(self):
        return self.name

class Product(models.Model):
	name = models.CharField(max_length=100)
	slug = models.SlugField(max_length=100, unique=True)
	price = models.DecimalField(default=0, decimal_places=2, max_digits=6)
	category = models.ForeignKey(Category, on_delete=models.CASCADE)
	brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
	description = models.CharField(max_length=250, default='', blank=True, null=True)
	image = models.ImageField(upload_to='uploads/product/')
	# Add Sale Stuff
	is_sale = models.BooleanField(default=False)
	sale_price = models.DecimalField(default=0, decimal_places=2, max_digits=6)

	def __str__(self):
		return self.name
	
	def clean(self):
		# Field-level errors (e.g. an empty price) are reported separately.
		if self.price is None or self.sale_price is None:
			return
		if self.price < 0:
			raise ValidationError({'price': 'Price cannot be negative.'})
		if self.is_sale and not (0 < self.sale_price < self.price):
			raise ValidationError(
				{'sale_price': 'Sale price must be greater than 0 and lower than the regular price.'}
			)

	@property
	def current_price(self):
		"""The price customers actually pay, honouring an active sale."""
		return self.sale_price if self.is_sale else self.price

	def get_absolute_url(self):
		return reverse("product_details", kwargs={'id': self.id})

	def get_add_to_cart_url(self):
		return reverse("add_to_cart", kwargs={'product_id': self.pk})
