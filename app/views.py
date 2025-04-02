from django.shortcuts import render,redirect,redirect, get_object_or_404
from .models import *
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from decimal import Decimal
from django.db import transaction
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .payment_api import *
from .send_sms import *

# Create your views here.
def index(request):
    try:
        selected_books = Product.objects.filter(status=True).order_by('-id')[:16]
        nv_bar=Nav_bar.objects.filter(status=True).order_by('-id')
        # If there are fewer than 4 books, fetch books with selected_items=False
        if selected_books.count() < 17:
            remaining_books = Product.objects.filter(status=True).order_by('-id')[:(17 - selected_books.count())]
            latest_books = selected_books | remaining_books  # Combine both querysets
        else:
            latest_books = selected_books

        return render(request,"index.html",{"books":latest_books,"nv_bar":nv_bar,"category":Display_Category.objects.filter(status=True)})
    except:
        return render(request,"index.html",{"books":latest_books,"nv_bar":nv_bar,"category":Display_Category.objects.filter(status=True)})
def category_products(request,id):
    products = Product.objects.filter(status=True,sub_category__category__id=id).order_by('-id')  # Fetch all products, ordered by latest

    # Pagination setup (10 products per page)
    paginator = Paginator(products, 30)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'product_list.html', {'books': page_obj,"category":Display_Category.objects.filter(status=True)})
@csrf_exempt
def search_product(request):
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.filter(name__icontains=query)
        product_list = list(products.values('id', 'name'))
    else:
        product_list = []
    return JsonResponse({'products': product_list})
def register(request):
    if request.method == "POST":
        try:
            if  request.POST["email"] and  request.POST["name"] and request.POST["password"]:
                email = request.POST["email"]
                name = request.POST["name"]
                password = request.POST["password"]
                phone_no = request.POST["phone_no"]
                status = request.POST.get("agree_term", "False") == "on"
                if User.objects.filter(email=request.POST['email']).first():
                    return redirect("login")
                else:
                    if status:
                        base_username = name.lower().replace(" ", "_")  # Example: "John Doe" -> "john_doe"
                        username = base_username
                        counter = 1  # Start from 1
                        # Check if the username already exists and increment the counter if it does
                        while User.objects.filter(username=username).exists():
                            username = f"{base_username}-{counter}"  # Format as username-1, username-2, etc.
                            counter += 1
                        
                        # Create the user with the generated username
                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            first_name=name,
                            password=password
                        )
                        
                        user=authenticate(request, username=username, password=password)
                        login(request, user)
                        UserDetails.objects.create(user=request.user,name=name,email=email,phone_no=phone_no)
                        return redirect("index")
        except:
            return redirect("register")
    return render(request,"register.html",{"category":Display_Category.objects.filter(status=True)})

def contact(request):
    if request.method == 'POST':
        # Get form data from the POST request
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        phone_no = request.POST.get('phone')
        message = request.POST.get('message')

        # Validate phone number (must be exactly 10 digits)
        if len(phone_no) != 10 or not phone_no.isdigit():
            return HttpResponse('Phone number must be exactly 10 digits long and contain only numbers.', status=400)
        try:
            # Create a new Contact instance
            contact = Contact(
                name=name,
                email=email,
                subject=subject,
                phone_no=phone_no,
                message=message
            )
            # Save the contact instance to the database
            contact.save()
            return render(request,"contact.html",{"send_data":"Send Sucessfully..","category":Display_Category.objects.filter(status=True)})  # Replace 'success' with the appropriate URL for success page
        except ValidationError as e:
            return render(request,"contact.html",{"data":"Erorr accored..","category":Display_Category.objects.filter(status=True)})
    return render(request,"contact.html",{"category":Display_Category.objects.filter(status=True)})
def terms_of_use(request):
    return render(request, 'termsofuse.html',{"category":Display_Category.objects.filter(status=True)})

def refund_policy(request):
    return render(request, 'refundpolicy.html',{"category":Display_Category.objects.filter(status=True)})

def privacy_policy(request):
    return render(request, 'privacypolicy.html',{"category":Display_Category.objects.filter(status=True)})

def faqs(request):
    return render(request, 'faqs.html',{"category":Display_Category.objects.filter(status=True)})
def aboutus(request):
    return render(request, 'aboutus.html',{"category":Display_Category.objects.filter(status=True)})

def update_user(request):
    if request.method == "POST":
        # try:
        data=UserDetails.objects.filter(user=request.user).first()
        if  data.email != request.POST["email"]:
            if UserDetails.objects.filter(email=request.POST["email"]).first():
                return render(request,"register.html",{"user_details":UserDetails.objects.filter(user=request.user).first(),"info":"Alerdy Email Registerd..","category":Display_Category.objects.filter(status=True)})
        else:
            email = request.POST["email"]
            name = request.POST["name"]
            password = request.POST["password"]
            phone_no = request.POST["phone_no"]
            status = request.POST.get("agree_term", "False") == "on"
            data=UserDetails.objects.filter(email=request.POST['email']).first()
            user=User.objects.filter(id=data.user.id).first()
            if data and status:
                data.email=email
                data.phone_no=phone_no
                data.name=name
                data.save()
                if password:
                    user.set_password(password)
                    user.save()
                return redirect("index")
            else:
                return redirect("index")
        # except:
        #     return redirect("index")
    return render(request,"register.html",{"user_details":UserDetails.objects.filter(user=request.user).first(),"category":Display_Category.objects.filter(status=True)})
def product_list_all(request):
    products = Product.objects.filter(status=True).order_by('-id')  # Fetch all products, ordered by latest

    # Pagination setup (10 products per page)
    paginator = Paginator(products, 30)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'product_list.html', {'books': page_obj,"category":Display_Category.objects.filter(status=True)})
def shop(request,id):
    product=Product.objects.get(id=id)
    if product:
        request.session['item_id'] = product.id
        images=ProductImage.objects.filter(product=product,status=True)
        return render(request,"shop-single.html",{"product":product,"images":images,"category":Display_Category.objects.filter(status=True)})

        
    return render(request,"shop-single.html",{"product":product,"category":Display_Category.objects.filter(status=True)})
def checkout(request):
    try:
        if request.session.get('item_id'):
            product=Product.objects.get(id=request.session.get('item_id'))
            return render(request,"checkout.html",{"product":product,"category":Display_Category.objects.filter(status=True)})
    except:
        return redirect("index")
    

def billing(request):
    item_id = request.session.get('item_id')  # Retrieve product ID from session
    if not item_id:
        messages.error(request, "No product selected for billing.")
        return redirect('product_list')  # Redirect if no product is selected

    product = get_object_or_404(Product, id=item_id)
    
    if request.method == "POST":
        item_id = request.session.get("item_id")
        if not item_id:
            messages.error(request, "No product selected!")
            return redirect("index")
        customer_name = request.POST.get("fname")
        relation=request.POST.get("relation")
        customer_phone = request.POST.get("phone")
        doorno=request.POST.get("doorno")
        relation_name=request.POST.get("relation_name")
        customer_email = request.POST.get("email")
        address_line1 = request.POST.get("billing_address")
        address_line2 = request.POST.get("billing_address2")
        village = request.POST.get("village")
        city = request.POST.get("city")
        state = request.POST.get("state")
        zipcode = request.POST.get("zipcode")
        additional_notes = request.POST.get("content")
        try:
            if customer_name and customer_phone and customer_email and zipcode  and city and state:
                product = get_object_or_404(Product, id=item_id)
                with transaction.atomic():  # Ensures both records are saved together
            #         # Create order
                    order = Order.objects.create( product=product,status=False)
                    customer=CustomerOrderDetails.objects.create(
                    order=order,
                    relation=relation,
                    relation_name=relation_name,
                    doorno=doorno,
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    customer_email=customer_email,
                    address_line1=address_line1,
                    address_line2=address_line2,
                    village=village,
                    city=city,
                    state=state,
                    zipcode=zipcode,
                    additional_notes=additional_notes,
                    
                )
                Payment_details.objects.create(status=True,customer=customer,transaction_id="1234",price=product.price,discount=product.discount,shipping_charge=product.shipping_charge)
                order.status=True
                order.save()
                json_data=payment_oreder(order.order_number,order.product.total_price(),customer_name,customer_email,customer_phone)
                print(json_data)
                if json_data["status"] == "OK":
                    return redirect(json_data["paymentLink"])
                messages.success(request, "Order placed successfully!")
                return redirect("index")
        except:
            return redirect("billing")
    context = {
        'product': product,"category":Display_Category.objects.filter(status=True)
    }
    return render(request, 'Billing-Details.html', context)


def user_orders_list(request):
    if request.method == "POST":
        mobile_number = request.POST.get("mobile")
        details = Payment_details.objects.filter(customer__customer_phone=mobile_number).order_by("-id")
        print(details)
        return render(request, "yourorders.html", {"orders": details,"mobile":mobile_number,"category":Display_Category.objects.filter(status=True)})
    return render(request, "yourorders.html", {"category":Display_Category.objects.filter(status=True)})
@csrf_exempt
def payment_webhook(request):
    if request.method == "POST":
        data = json.loads(request.body)
        print("Webhook received:", data)
        return JsonResponse({"status": "success"})
import requests
from django.conf import settings
def payment_success(request,order, mobile, amount):
    url = f"https://api.cashfree.com/pg/orders/{order}"
    headers = {
        "x-api-version": "2022-09-01",
        "x-client-id": settings.CASHFREE_APP_ID,
        "x-client-secret": settings.CASHFREE_SECRET_KEY
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            print("Order Details:", data)

            # Ensure the order exists
            order_obj = Order.objects.filter(order_number=order).first()
            if not order_obj:
                print("Error: Order not found")
                return render(request, "error.html", {"error": "Order not found."})

            # Ensure payment data is available
            if "cf_payment_id" not in data and not data["error_details"] is None:
                print("Error: Payment ID not found in response")
                return render(request, "error.html", {"error": "Payment ID not found."})

            # Update Payment details
            order_obj.status = True
            order_obj.save()
            Payment_details.objects.filter(order=order_obj).update(transaction_id=data["cf_payment_id"])
            # Send SMS Confirmation
            send_sms_customer_order(mobile, order_obj, amount)
        else:
            print(f"Error {response.status_code}: {response.json()}")
            return render(request, "error.html", {"error": f"Error: {response.status_code}"})

    except Exception as e:
        print(f"An error occurred: {e}")
        return render(request, "error.html", {"error": str(e)})

    

    # Retrieve Payment Details
    details = Payment_details.objects.filter(customer__order__id=order_obj.id).order_by("-id")

    return render(request, "yourorders.html", {
        "orders": details,
        "category": Display_Category.objects.filter(status=True),
        "success": "Your Order Completed Successfully."
    })
def update_order_status(request):
    if request.method == "POST":
        order_ids = request.POST.getlist('order_ids[]')
        try:
            Order.objects.filter(id__in=order_ids, status=True).update(status=False)
            return JsonResponse({'message': 'Selected orders updated successfully!'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)
