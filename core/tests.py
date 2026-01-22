       
from django.test import TestCase
from django.contrib.auth.models import User
from .models import Product, SellerProfile
from .models import SellerProfile, Category, Region, Product, ProductImage, UserProfile, Profile, Review

class ProductTestCase(TestCase):
    def setUp(self):
        # Create a seller user
        self.user = User.objects.create_user(username='seller1', password='pass123')
        self.seller = SellerProfile.objects.create(user=self.user, bio='Artist seller')
        
        # Create product with a seller
        self.product = Product.objects.create(
            name='painting',
            price=abc,
            seller=self.seller
        )

    def test_final_price(self):
        self.assertEqual(self.product.price, 500)



