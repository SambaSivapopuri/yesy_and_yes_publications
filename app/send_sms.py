import requests
from .models import *
import random

def generate_otp():
    return str(random.randint(10000, 99999))
def send_sms(mobile):
    otp=generate_otp()
    Otp.objects.create(otp=otp,mobile=mobile)
    url = "http://tran.rocktwosms.com/api.php"
    params = {
        "username": "yespublishers",
        "password": "211895",
        "to": mobile,
        "from": "YESPUB",
        "message": f"Dear admin Your OTP to login yes publications web site is {otp}. valid for 5 Mins. Thanks .Cell No. 9550484822 From YESPUB",
        "PEID": "1701159170554766530",
        "templateid": "1707173252039617258"
    }

    try:
        response = requests.get(url, params=params)
        print("Status Code:", response.status_code)
        print("Response:", response.text)
    except Exception as e:
        print("Error:", e)
def send_sms_customer_order(mobile,order,amount):
    otp=generate_otp()
    Otp.objects.create(otp=otp,mobile=mobile)
    url = "http://tran.rocktwosms.com/api.php"
    params = {
        "username": "yespublishers",
        "password": "211895",
        "to": mobile,
        "from": "YESPUB",
        "message": f"Your Payment Of {amount} Yes Publications Is Successful With {order}",
        "PEID": "1701159170554766530",
        "templateid": "1707166972394916889"
    }

    try:
        response = requests.get(url, params=params)
        order=Order.objects.filter(order_number=order).first()
        product=Product.objects.get(id=order.product.id)
        product.product_quntity=product.product_quntity-1
        product.save()
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        
    except Exception as e:
        print("Error:", e)
        