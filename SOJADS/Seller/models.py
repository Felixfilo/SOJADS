from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class Product(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    description = models.TextField()
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES, null=True, blank=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sales_count = models.PositiveIntegerField(default=0)

    @property
    def sale_price(self):
        """Calculates sale price after applying the discount."""
        if not self.discount:
            return self.price
        if self.discount_type == 'percentage':
            return self.price * (1 - self.discount / 100)
        elif self.discount_type == 'fixed':
            return self.price - self.discount
        return self.price
    
    def __str__(self):
        return self.product_name
    
    
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='product_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    
    def __str__(self):
        return f"Images for {self.product.product_name}"
    
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', related_name='reviews', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
class Reply(models.Model):
    user = models.ForeignKey(User, related_name='seller_replies', on_delete=models.CASCADE)
    review = models.ForeignKey(Review, related_name='replies', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Replies'