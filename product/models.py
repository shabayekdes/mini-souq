from django.db import models
from django.shortcuts import reverse

# Create your models here.
class Category(models.Model):
	name = models.CharField(max_length=50)
	# home_class = models.CharField(max_length=50)
	order = models.IntegerField(default=0)
	image = models.ImageField(upload_to='uploads/category/')

	def __str__(self):
		return self.name
	def get_absolute_url(self):
		return reverse("product_details", kwargs={"id" : self.pk})

	class Meta:
		verbose_name_plural = 'categories'


class Product(models.Model):
	name = models.CharField(max_length=100)
	slug = models.SlugField(max_length=100, unique=True)
	price = models.DecimalField(default=0, decimal_places=2, max_digits=6)
	category = models.ForeignKey(Category, on_delete=models.CASCADE)
	description = models.CharField(max_length=250, default='', blank=True, null=True)
	image = models.ImageField(upload_to='uploads/product/')
	# Add Sale Stuff
	is_sale = models.BooleanField(default=False)
	sale_price = models.DecimalField(default=0, decimal_places=2, max_digits=6)

	def __str__(self):
		return self.name
	
	def get_absolute_url(self):
		return reverse("product_details", kwargs={'id': self.id})
	def get_add_to_cart_url(self):
	    return reverse("checkout:add_to_cart", kwargs={
            'product_id': self.pk
        })
