from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from decimal import Decimal
from django.core.exceptions import ValidationError
import os
from barcode import Code128
from barcode.writer import ImageWriter
from io import BytesIO
from django.core.files.base import ContentFile
from django.utils.timezone import now
from datetime import timedelta
import uuid
class Otp(models.Model):
    mobile=models.CharField(max_length=10,blank=False,null=False)
    otp = models.CharField(max_length=6, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "otp"

    def is_valid(self):
        # Check if the OTP is within 5 minutes from creation
        return now() <= self.created_at + timedelta(minutes=5)
class UserDetails(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False, null=False)
    email = models.EmailField(max_length=255, blank=False, null=False,unique=True)
    # RegexValidator to ensure the phone number is exactly 10 digits
    phone_no = models.CharField(
        max_length=10,
        blank=False,
        null=False,
        unique=True,
        validators=[RegexValidator(regex=r'^\d{10}$', message='Phone number must be exactly 10 digits')],
    )
    
    created_at = models.DateTimeField(auto_now_add=True)  # Set when created
    updated_at = models.DateTimeField(auto_now=True)  # Update when modified

    # User tracking
    created_by = models.ForeignKey(User, related_name='contact_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='contact_updated', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table="user_details"

def validate_url(value):
    if not value.startswith('https://'):
        raise ValidationError(f"{value} must start with https://")


class Category(models.Model):
    name=models.CharField(max_length=255,blank=False,null=False)
    image = models.ImageField(upload_to='category/', blank=True, null=True)
    status=models.BooleanField(default=True,blank=False,null=False)
    created_at = models.DateTimeField(auto_now_add=True)  # Set when created
    updated_at = models.DateTimeField(auto_now=True)  # Update when modified

    # User tracking
    created_by = models.ForeignKey(User, related_name='category_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='category_updated', on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        db_table="category"
class Sub_Category(models.Model):
    category=models.ForeignKey(Category,on_delete=models.CASCADE)
    name=models.CharField(max_length=255,blank=False,null=False)
    image = models.ImageField(upload_to='sub_category/', blank=True, null=True)
    status=models.BooleanField(default=True,blank=False,null=False)
    created_at = models.DateTimeField(auto_now_add=True)  # Set when created
    updated_at = models.DateTimeField(auto_now=True)  # Update when modified

    # User tracking
    created_by = models.ForeignKey(User, related_name='sub_category_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='sub_category_updated', on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        db_table="sub_category"
class Product(models.Model):
    name = models.CharField(max_length=255)
    product_type=models.CharField(max_length=255,blank=True,null=True)
    sub_category = models.ForeignKey(Sub_Category, on_delete=models.CASCADE)
    product_quntity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.BooleanField(default=False)
    seller_name_or_shop_name = models.CharField(max_length=255)
    out_of_stock = models.BooleanField(default=False)
    send_notification = models.BooleanField(default=False)
    product_publish_or_unpublish = models.BooleanField(default=True)
    description = models.TextField()
    image = models.ImageField(upload_to='products/')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Set when created
    updated_at = models.DateTimeField(auto_now=True)  # Update when modified
    def get_final_price(self):
        if self.discount > 0:
            return (self.price - (self.price * (self.discount / 100))).quantize(Decimal('1.00'))
        return self.price.quantize(Decimal('1.00'))
    def total_price(self):
        return (self.get_final_price() + self.shipping_charge).quantize(Decimal('1.00'))
    def discount_mount(self):
        return (self.price * (self.discount / 100)).quantize(Decimal('1.00'))
    def __str__(self):
        return self.name
    
    class Meta:
        db_table="product"

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='product_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to="product_related_images/")
    created_at = models.DateTimeField(auto_now_add=True)
    status=models.BooleanField(default=True,blank=False,null=False)
    created_at = models.DateTimeField(auto_now_add=True)  # Set when created
    updated_at = models.DateTimeField(auto_now=True)  # Update when modified
    def __str__(self):
        return f"Image for {self.product.name}"
    
    class Meta:
        db_table = "product_images"

class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=255, unique=True, blank=True)
    status = models.BooleanField(blank=True,null=True)  # False indicates 'Pending'
    weight=models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name='order_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='order_updated', on_delete=models.SET_NULL, null=True, blank=True)
    check_status=models.BooleanField(default=False,null=True,blank=True)
    def save(self, *args, **kwargs):
        if not self.order_number:
            last_order = Order.objects.filter(product=self.product).order_by('-id').first()
            last_order_count = int(last_order.order_number.split('-')[-1]) if last_order and last_order.order_number else 0
            self.order_number = f"{self.product.name}-{last_order_count + 1}"
        super().save(*args, **kwargs)


    class Meta:
        db_table = "orders"

class CustomerOrderDetails(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='order_details')
    user_details=models.ForeignKey(UserDetails,on_delete=models.SET_NULL,blank=True,null=True)
    customer_name = models.CharField(max_length=255)
    relation=models.CharField(max_length=5,blank=True,null=True)
    relation_name=models.CharField(max_length=255,blank=True,null=True)
    customer_phone = models.CharField(max_length=15)
    customer_email = models.EmailField()
    doorno=models.CharField(max_length=255)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    village = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=10)
    additional_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Set when created
    updated_at = models.DateTimeField(auto_now=True)  # Update when modified
    created_by = models.ForeignKey(User, related_name='CustomerOrderDetails_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='CustomerOrderDetails_updated', on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        db_table = "customer_order_details"
class Payment_details(models.Model):
    customer=models.ForeignKey(CustomerOrderDetails, on_delete=models.CASCADE,related_name="coustomer_detatis")
    status = models.BooleanField()
    transaction_id=models.CharField(max_length=255,blank=False,null=False)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2)
    barcode = models.ImageField(upload_to='barcodes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Set when created
    updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        if not self.barcode:
            # Generate barcode
            code = Code128(str(self.id), writer=ImageWriter())
            buffer = BytesIO()
            code.write(buffer)
            filename = f'barcode_{self.id}.png'
            self.barcode.save(filename, ContentFile(buffer.getvalue()), save=False)

        super().save(*args, **kwargs)
    def get_final_price(self):
        if self.discount > 0:
            return (self.price - (self.price * (self.discount / 100))).quantize(Decimal('1.00'))
        return self.price.quantize(Decimal('1.00'))
    def total_price(self):
        return (self.get_final_price() + self.shipping_charge).quantize(Decimal('1.00'))
    def discount_mount(self):
        return (self.price * (self.discount / 100)).quantize(Decimal('1.00'))
 
    class Meta:
        db_table="payment"
class DeliveryDetails(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE)
    addtional=models.TextField(blank=True, null=True)
    status=models.BooleanField(default=True,blank=False,null=False)
    date=models.DateField(blank=True,null=True)
    info=models.TextField(blank=True,null=True)
    sms=models.BooleanField(default=True,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Set when created
    updated_at = models.DateTimeField(auto_now=True)  # Update when modified
    created_by = models.ForeignKey(User, related_name='delivery_details_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='delivery_details_updated', on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        db_table="delivery_details"
class Track(models.Model):
    track_number=models.TextField(blank=False,null=False)
    weight=models.CharField(blank=True,null=False,max_length=5)
    mobile=models.CharField(blank=True,null=True,max_length=12)
    status=models.BooleanField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Set when created
    updated_at = models.DateTimeField(auto_now=True)  # Update when modified
    class Meta:
        db_table="track "
class Nav_bar(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    image=models.ImageField(upload_to='nav_bar/', blank=True, null=True)
    status = models.BooleanField(default=True)
    display=models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)  # Set when created
    updated_at = models.DateTimeField(auto_now=True)  # Update when modified
    url = models.URLField(max_length=255, validators=[validate_url],blank=True,null=True)  # Ensure this line is present
    created_by = models.ForeignKey(User, related_name='nav_bar_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='nav_bar_updated', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = "nav_bar"
class Contact(models.Model):
    name=models.CharField(max_length=255,blank=False,null=False),
    email=models.EmailField(),
    subject=models.TextField(blank=False,null=False),
    phone_no=models.CharField(max_length=15),
    message=models.TextField(blank=False,null=False)
    created_at = models.DateTimeField(auto_now_add=True)  # Set when created
    updated_at = models.DateTimeField(auto_now=True)  # Update when modified
    class Meta:
        db_table="contact_form"

class Display_Category(models.Model):
    category=models.ForeignKey(Category,on_delete=models.CASCADE)
    status=models.BooleanField(blank=False,null=False)
    created_at = models.DateTimeField(auto_now_add=True)  # Set when created
    updated_at = models.DateTimeField(auto_now=True)  # Update when modified
    class Meta:
        db_table="display_category"
class P_Order(models.Model):
    p_order_number = models.CharField(max_length=255, unique=True, blank=True)
    date=models.DateField(blank=True,null=True)
    product_name=models.TextField(blank=True,null=True)
    pay_amount=models.CharField(max_length=6,blank=True,null=True)
    name=models.CharField(max_length=255,blank=True,null=True)
    phone=models.CharField(max_length=15,blank=True,null=True)
    address=models.TextField(blank=True,null=True)
    zip_code=models.CharField(max_length=15,blank=True,null=True)
    quntity=models.CharField(blank=True,max_length=6,null=True)
    pay_status=models.BooleanField(blank=True,null=True)
    transaction_id=models.CharField(blank=True,null=True,max_length=255)
    status=models.BooleanField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Set when created
    updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        if not self.p_order_number:
            self.p_order_number = str(uuid.uuid4()).replace("-", "").upper()[:10]  # Generates a 10-character unique code
        super(P_Order, self).save(*args, **kwargs)
    class Meta:
        db_table="p_order"
    