from django.shortcuts import render,redirect
from .models import *
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from .send_sms import *
import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import csv
from datetime import datetime,date
from django.db.models import Count
def get_subcategories(request):
    category_id = request.GET.get('category_id')
    if category_id:
        subcategories = Sub_Category.objects.filter(category_id=category_id,status=True).values('id', 'name')
        return JsonResponse(list(subcategories), safe=False)
    return JsonResponse([], safe=False)
@csrf_exempt
def update_nav_bar(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        status = request.POST.get('status') == 'true'
        url = request.POST.get('url', '')

        try:
            nav_item = Nav_bar.objects.get(id=product_id)
            nav_item.status = status
            nav_item.url = url
            nav_item.save()
            return JsonResponse({'success': True, 'message': 'Data updated successfully'})
        except Nav_bar.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Nav item not found'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def admin_login(request):
    if request.method == "POST":
        mobile=request.POST["mobile"]
        details=UserDetails.objects.filter(phone_no=mobile)
        if details:
            send_sms(mobile)
            return redirect("verify")
        else:
            username = "admin"
            password = "admin"
            user=User.objects.create_superuser(username=username,password=password)
            UserDetails.objects.create(user=user,email="admin@gmail.com",phone_no="9133694958")
            return redirect("admin")
        
    return render(request,"login.html")

def verify_login(request):
    if request.method == "POST":
        try:
            otp=request.POST["otp"]
            otp_data=Otp.objects.filter().last()
            if otp == otp_data.otp:
                if otp_data.is_valid:
                    user_details=UserDetails.objects.get(phone_no=otp_data.mobile)
                    login(request,user_details.user)
                    return redirect("admin")
                else:
                    return render(request,"verify.html",{"data":" Otp Expired.."})
            else:
                return render(request,"verify.html",{"data":"Check Otp.."})
        except:
            return redirect("login")
    return render(request, 'verify.html')
@login_required
def custom_logout(request):
    logout(request)
    return redirect('index')

def save_display_nav_items(request):
    if request.method == 'POST':
        category_id = request.POST.get('nav_id')
        status = request.POST.get('status') == 'true'
        try:
            display_category = Nav_bar.objects.get(id=category_id)
            display_category.display = status
            display_category.save()
            return JsonResponse({'status': 'success', 'message': 'Scrolling status updated successfully.'})
        except Display_Category.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Scrolling not found.'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})
@login_required
def nav_items(request):
    nav_bar = Nav_bar.objects.filter(status=True).order_by("-id")
    paginator = Paginator(nav_bar, 50)  # Show 50 categories per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    if request.method == "POST":
        product=Product.objects.get(id=request.POST["category"])
        Nav_bar.objects.create(name=request.POST["name"],product=product,image=request.FILES.get("img"),
                               display=False,url=f"{request.scheme}://{request.get_host()}/shop/{product.id}/")
        messages.success(request,"Successfully added..")
        return redirect("nav_items")
    return render(request,"admin_templates/menu_items.html",{"page_obj":page_obj,"data":Product.objects.filter(status=True).order_by('-id') })
@login_required
def add_nav_item(request):
    if request.method == "POST":
        product=request.POST["product"]
        img=request.FILES.get("img")
        status = request.POST.get("check", "False") == "on"
        url = f"{request.scheme}://{request.get_host()}/shope/{product}/"
        if product and img and status:
            Nav_bar.objects.create(product__id=product,image=img,display=status,url=url)
            messages.success(request, 'successful Added')
            return redirect("add_nav_item")
        return redirect("add_nav_item")
    return render(request,"admin_templates/add_nav_items.html",{"data":Product.objects.filter(status=True)})
@login_required
def admin_dashboard(request):
    category_count=Category.objects.filter(status=True).count()
    sub_category_count=Sub_Category.objects.filter(status=True).count()
    return render(request, 'admin_templates/index.html',{"category_count":category_count,
                            "sub_category_count":sub_category_count,
                            "product_count":Product.objects.filter(status=True).count(),
                            "order_count":Order.objects.filter(status=True).count(),
                            "completd_order_count":Order.objects.filter(status=True,check_status=True).count(),
                            "pending_order_count":Order.objects.filter(status=True).count()-Order.objects.filter(status=True,check_status=True).count(),
                            "cancel_order_count":Order.objects.filter(status=False).count(),
                            "nav_bar":Nav_bar.objects.filter(status=True).count(),
                            "total_amount":sum([payment.total_price() for payment in Payment_details.objects.all()], Decimal('0.00')),
                            "customers": CustomerOrderDetails.objects.filter().values_list('customer_phone', flat=True).distinct().count()                           
                            })
@login_required
def add_category(request):
    if request.method == "POST":
        name = request.POST["name"]
        status = request.POST.get("check", "False") == "on"# Convert checkbox to boolean
        image = request.FILES.get("img")  # Get image file from request.FILES

        if name:  # Ensure an image is uploaded
            try:
                category=Category.objects.create(name=name, status=status, image=image)
                Display_Category.objects.create(category=category,status=False)
                print("test")
            except:
                return render(request, 'admin_templates/add_category.html',{"error":"Category Exits.."})
        return render(request, 'admin_templates/add_category.html',{"message":f'{name}-Category Added success..'})
    return render(request, 'admin_templates/add_category.html')
@login_required
def category_list(request):
    categories = Category.objects.filter(status=True).order_by("-id")
    
    # Adding sub-category count for each category
    for category in categories:
        category.sub_category_count = Sub_Category.objects.filter(category=category,status=True).count()

    paginator = Paginator(categories, 100)  # Show 50 categories per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_templates/category_list.html', {'page_obj': page_obj})
@login_required
def update_category(request, id):
    category = get_object_or_404(Category, id=id)

    if request.method == "POST":
        name = request.POST.get("name")
        img = request.FILES.get("img")  # New image
        check = request.POST.get("check") == "on"
        remove_image = request.POST.get("remove_image")
        if not Category.objects.filter(name=name).exists():
            # Update fields
            category.name = name
            category.status = check

            # If a new image is uploaded, replace the old image
            if img:
                if category.image:  
                    category.image.delete(save=False)  # Delete the old image
                category.image = img  # Set new image

            # If "Remove Image" is checked but no new image is uploaded, do nothing
            elif remove_image:
                category.image.delete(save=False)  
                category.image = None

            category.save()
            messages.success(request, 'successful Updated')
            return redirect("category_list")  # Redirect to category list
        else:
            messages.error(request, 'Category Already Exists')
            return render(request, "admin_templates/update_category.html", {"category": category})
    return render(request, "admin_templates/update_category.html", {"category": category})


def remove_category(request, id):
    try:
        category = Category.objects.get(id=id)

        # Check if any sub-categories exist
        if not Sub_Category.objects.filter(category=category,status=True).exists():
            category.status = False
            category.save()
            messages.success(request, 'successful Removed')
            return JsonResponse({'message': 'Category status updated to False'}, status=200)
        else:
            return JsonResponse({'error': 'Cannot update category status with sub-categories'}, status=400)

    except Category.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def remove_sub_category(request, id):
    try:
        sub_category = Sub_Category.objects.get(id=id)
        
        # Check if any products exist
        if not Product.objects.filter(sub_category=sub_category,status=True).exists():
            sub_category.status = False
            sub_category.save()
            messages.success(request, 'successful Removed')
            return JsonResponse({'message': 'Sub-Category status updated to False'}, status=200)
        else:
            return JsonResponse({'error': 'Cannot update sub-category status with products'}, status=400)

    except Sub_Category.DoesNotExist:
        return JsonResponse({'error': 'Sub-Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def remove_product(request, id):
    try:
        product = Product.objects.get(id=id,status=True)
        product.status = False
        product.save()
        messages.success(request, 'successful Removed')
        return JsonResponse({'message': 'Product status updated to False'}, status=200)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@login_required
def add_sub_category(request):
    if request.method == "POST":
        name = request.POST["name"]
        category=request.POST["category"]
        status = request.POST.get("check", "False") == "on"# Convert checkbox to boolean
        image = request.FILES.get("img")  # Get image file from request.FILES

        if name:  # Ensure an image is uploaded
            try:
                sub=Sub_Category.objects.create(name=name, status=status, image=image,category_id=category)
            except:
                return render(request, 'admin_templates/add_sub_category.html',{"error":"Sub-Category Exits..","data":Category.objects.filter(status=True).order_by('-id')})
        return render(request, 'admin_templates/add_sub_category.html',{"message":f'{sub.name}:sub-Category Added success..',"data":Category.objects.filter(status=True).order_by('-id')})
    return render(request, 'admin_templates/add_sub_category.html',{"data":Category.objects.filter(status=True).order_by('-id') })
@login_required
def sub_category_list(request):
    subcategories = Sub_Category.objects.filter(status=True).order_by('-id')  
    paginator = Paginator(subcategories, 100) 
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "admin_templates/sub_category_list.html", {
        "page_obj": page_obj
    })
@login_required
def update_subcategory(request, id):
    subcategory = get_object_or_404(Sub_Category, id=id)
    categories = Category.objects.filter(status=True).order_by('-id')

    if request.method == "POST":
        if not Sub_Category.objects.filter(name=request.POST["name"]).exists():
            # Updating subcategory fields
            subcategory.name = request.POST.get("name", subcategory.name)
            subcategory.category_id = request.POST.get("category", subcategory.category.id)
            subcategory.status = 'status' in request.POST

            # Handle Image Deletion
            if 'delete_image' in request.POST:
                if subcategory.image and subcategory.image.name:
                    default_storage.delete(subcategory.image.path)  # Delete file from storage
                    subcategory.image = None  # Remove the image from the database

            # Handle New Image Upload
            if "new_image" in request.FILES:
                new_image = request.FILES["new_image"]
                subcategory.image = new_image  # Replace old image with new one

            subcategory.save()  # Save the updated subcategory
            messages.success(request, 'successful Updated')
            return redirect("sub_category_list")  # Redirect after updating
        else:
            messages.error(request, 'Sub-Category Already Exists')
            return render(request, "admin_templates/update_subcategory.html", {
                                    "categories": categories,
                                    "subcategory": subcategory,
                                })
    return render(request, "admin_templates/update_subcategory.html", {
        "categories": categories,
        "subcategory": subcategory,
    })
@login_required
def add_product(request):
    if request.method == 'POST':
        # Retrieving data from the form
        name = request.POST['name']
        product_type = request.POST['product_type']
        subcategory_id = request.POST['subcategory']
        product_price = request.POST.get('price')
        product_discount = request.POST['discount']
        shipping_charge = request.POST['shipping_charge']
        status = request.POST.get('check') == 'on'
        seller_name_or_shop_name = request.POST['seller_name_or_shop_name']
        out_of_stock = request.POST.get('stock') == 'on'
        send_notification = request.POST.get('send_notification') == 'on'
        publish = request.POST.get('publish') == 'on'
        description = request.POST['product_description']
        image = request.FILES.get('img')
        related_images = request.FILES.getlist('related_img')
        related_pdf=request.FILES.get("pdf_file")
        # Validate required fields and check if the subcategory exists
        try:
            subcategory = Sub_Category.objects.get(id=subcategory_id)
            if Product.objects.filter(name=name,status=True,sub_category=subcategory).exists():
                messages.error(request,"Alerdy Name Exits In subcategory")
                return redirect("add_product")
        except Sub_Category.DoesNotExist:
            messages.error(request, "The selected subcategory does not exist.")
            return redirect('add_product')

        # Create Product object
        product = Product.objects.create(
            name=name,
            sub_category_id=subcategory.id,
            product_type=product_type,
            price=product_price,
            discount=product_discount,
            shipping_charge=shipping_charge,
            status=status,
            seller_name_or_shop_name=seller_name_or_shop_name,
            out_of_stock=out_of_stock,
            send_notification=send_notification,
            product_publish_or_unpublish=publish,
            description=description,
            image=image,
            # created_by=request.user,
        )

        # Nav_bar.objects.create(product=product)
        if related_pdf:
            ProductRelatedPdf.objects.create(product=product,pdf_file=related_pdf)
        # Handle related images
        for related_image in related_images:
            ProductImage.objects.create(product=product, image=related_image)

        messages.success(request, "Product created successfully.")
        return redirect('add_product')

    categories = Category.objects.filter(status=True).order_by('-id')
    return render(request, 'admin_templates/product.html', {'categories': categories})
@login_required
def product_list(request):
    product_list = Product.objects.filter(status=True).order_by('-id')
    # Set up pagination (10 products per page)
    paginator = Paginator(product_list, 100)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin_templates/product_list.html', {"page_obj": page_obj})
@login_required
def update_product(request, id):
    product = get_object_or_404(Product, id=id)
    sub_categories = Sub_Category.objects.filter(status=True).order_by('-id')
    categories = Category.objects.filter(status=True).order_by('-id')
    product_images = ProductImage.objects.filter(product=product).order_by('-id')
    existing_pdf = ProductRelatedPdf.objects.filter(product=product, status=True).order_by("-id").first()

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        subcategory_id = request.POST.get("subcategory")
        subcategory = get_object_or_404(Sub_Category, id=subcategory_id)

        # Check if name is changed and if the new name already exists in the same subcategory
        if product.name != name:
            if Product.objects.filter(name=name, status=True, sub_category=subcategory).exclude(id=product.id).exists():
                messages.error(request, "Name already exists in the selected subcategory.")
                return redirect("update_product", id=id)

        # Proceed to update the product
        product.name = name
        product.sub_category = subcategory
        product.price = request.POST.get("price", product.price)
        product.discount = request.POST.get("discount", product.discount)
        product.shipping_charge = request.POST.get("shipping_charge", product.shipping_charge)
        product.seller_name_or_shop_name = request.POST.get("seller_name_or_shop_name", product.seller_name_or_shop_name)
        product.product_type = request.POST.get("product_type", product.product_type)
        product.description = request.POST.get("description", product.description)
        product.status = 'status' in request.POST
        product.out_of_stock = 'stock' in request.POST
        product.send_notification = 'send_notification' in request.POST
        product.product_publish_or_unpublish = 'publish' in request.POST

        # Handle main image update
        if 'delete_image' in request.POST:
            if product.image:
                default_storage.delete(product.image.path)
                product.image = None

        new_main_image = request.FILES.get('new_image')
        if new_main_image:
            product.image = new_main_image

        product.save()

        # Handle PDF upload
        pdf_file = request.FILES.get('pdf')
        if pdf_file:
            ProductRelatedPdf.objects.filter(product=product).delete()
            ProductRelatedPdf.objects.create(product=product, pdf_file=pdf_file)

        # Handle image deletions
        delete_images = request.POST.getlist("delete_images")
        for image_id in delete_images:
            image = get_object_or_404(ProductImage, id=image_id, product=product)
            if image.image:
                default_storage.delete(image.image.path)
            image.delete()

        # Handle new image uploads
        new_images = request.FILES.getlist("new_images")
        for image in new_images:
            ProductImage.objects.create(product=product, image=image)

        messages.success(request, "Product updated successfully.")
        return redirect("product_list")

    return render(request, "admin_templates/product_update.html", {
        'sub_categories': sub_categories,
        "categories": categories,
        "product": product,
        "product_images": product_images,
        "pdf": existing_pdf
    })

@login_required
def track_order(request,id):
    order=Payment_details.objects.filter(customer__order__status=True,customer__order__id=id).first()
    if request.method == "POST":
        Track.objects.create(track_number=request.POST["track_no"],weight=request.POST["weight"],mobile=request.POST["mobile"],status=True)
        order_detais=Order.objects.get(id=id)
        postal_tracking(request.POST["mobile"],order_detais.order_number,order.total_price(),request.POST["track_no"])
        # order_detais.status=False
        # order_detais.save()
        messages.success(request, 'successful Sended..')
        return redirect("order_list")
    return render(request,"admin_templates/track.html",{"order":order.customer})
@login_required
def order_list(request):
    # Initial filter for all active orders
    product_list = Payment_details.objects.filter(customer__order__status=True).order_by('-id')
    order_counts = Order.objects.filter(status=True,created_at__date=date.today()).values('product__name').annotate(order_count=Count('id')).order_by('-order_count')
    # Handle POST request for date filtering
    if request.method == "POST":
        from_date = request.POST.get("from_date")
        end_date = request.POST.get("end_date")

        try:
            # Convert from_date to datetime if it exists
            if from_date:
                from_date = datetime.strptime(from_date, '%Y-%m-%d')
            else:
                from_date = None

            # If end_date is not provided, use the current date
            if not end_date:
                end_date = datetime.now().date()
            else:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')

            # Apply filter with from_date and end_date
            if from_date:
                product_list = product_list.filter(created_at__range=[from_date, end_date])
                order_counts = Order.objects.filter(status=True,created_at__range=[from_date, end_date]).values('product__name').annotate(order_count=Count('id')).order_by('-order_count')
        except ValueError:
            pass  # Handle invalid date format gracefully

    # Set up pagination (50 products per page)
    paginator = Paginator(product_list, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_templates/order_list.html', {"page_obj": page_obj,"order_counts":order_counts})
@login_required
def cancel_orders(request):
    # Initial filter for all active orders
    product_list = Payment_details.objects.filter(customer__order__status=False).order_by('-id')
    order_counts = Order.objects.filter(status=False,created_at__date=date.today()).values('product__name').annotate(order_count=Count('id')).order_by('-order_count')
    # Handle POST request for date filtering
    if request.method == "POST":
        from_date = request.POST.get("from_date")
        end_date = request.POST.get("end_date")

        try:
            # Convert from_date to datetime if it exists
            if from_date:
                from_date = datetime.strptime(from_date, '%Y-%m-%d')
            else:
                from_date = None

            # If end_date is not provided, use the current date
            if not end_date:
                end_date = datetime.now().date()
            else:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                
            # Apply filter with from_date and end_date
            if from_date:
                product_list = product_list.filter(created_at__range=[from_date, end_date])
                order_counts = Order.objects.filter(status=True,created_at__range=[from_date, end_date]).values('product__name').annotate(order_count=Count('id')).order_by('-order_count')
        except ValueError:
            pass  # Handle invalid date format gracefully

    # Set up pagination (50 products per page)
    paginator = Paginator(product_list, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_templates/cancel_orders.html', {"page_obj": page_obj,"order_counts":order_counts})

@csrf_exempt
def update_check_status(request):
    if request.method == 'POST':
        product_id = request.POST.get('order_id')
        status = request.POST.get('status') == 'true'

        try:
            nav_item = Order.objects.get(id=product_id)
            nav_item.check_status = status
            nav_item.save()
            return JsonResponse({'success': True, 'message': 'Data updated successfully'})
        except Nav_bar.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Nav item not found'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
@login_required
def update_order(request, id):
    order = get_object_or_404(Order, id=id)
    customer = CustomerOrderDetails.objects.filter(order=order).first()

    if not customer:
        messages.error(request, 'Customer details not found.')
        return redirect("order_list")

    if request.method == "POST":
        customer.doorno = request.POST.get("doorno", customer.doorno)
        customer.address_line1 = request.POST.get("address_line1", customer.address_line1)
        customer.address_line2 = request.POST.get("address_line2", customer.address_line2)
        customer.village = request.POST.get("village", customer.village)
        customer.city = request.POST.get("city", customer.city)
        customer.state = request.POST.get("state", customer.state)
        customer.zipcode = request.POST.get("zipcode", customer.zipcode)

        customer.save()
        messages.success(request, 'Successfully updated!')
        return redirect("order_list")

    return render(request, "admin_templates/update_order.html", {"customer": customer})

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from django.http import HttpResponse
@login_required
def download_orders(request, format):
    product_list = Payment_details.objects.filter(status=True, customer__order__status=True).order_by('-id')

    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders.csv"'
        writer = csv.writer(response)
        writer.writerow(['S.No', 'Number', 'Date', 'Product Name', 'Quantity', 'Order No', 'Payment Status', 'Pay Amount', 'Name', 'Phone No', 'Transaction Id', 'Seller Name', 'Address', 'Zipcode', 'City', 'Weight'])

        for i, product in enumerate(product_list, 1):
            writer.writerow([
                i,
                product.customer.order.id,
                product.customer.order.created_at.strftime('%d-%m-%Y'),
                product.customer.order.product.name,
                1,
                product.customer.order.order_number,
                'Success' if product.status else 'Not Available',
                product.amount,
                product.customer.customer_name,
                product.customer.customer_phone,
                product.transaction_id,
                product.customer.order.product.seller_name_or_shop_name,
                product.customer.address_line1,
                product.customer.zipcode,
                product.customer.city,
                product.customer.order.product.weight if hasattr(product.customer.order.product, 'weight') else 'N/A'
            ])
        return response

    elif format == 'excel':
        data = []
        for i, product in enumerate(product_list, 1):
            data.append({
                'S.No': i,
                'Number': product.customer.order.id,
                'Date': product.customer.order.created_at.strftime('%d-%m-%Y'),
                'Product Name': product.customer.order.product.name,
                'Quantity': 1,
                'Order No': product.customer.order.order_number,
                'Payment Status': 'Success' if product.status else 'Not Available',
                'Pay Amount': product.get_final_price(),
                'Name': product.customer.customer_name,
                'Phone No': product.customer.customer_phone,
                'Transaction Id': product.transaction_id,
                'Seller Name': product.customer.order.product.seller_name_or_shop_name,
                'Address': product.customer.address_line1,
                'Zipcode': product.customer.zipcode,
                'City': product.customer.city,
                'Weight': product.customer.order.product.weight if hasattr(product.customer.order.product, 'weight') else 'N/A'
            })

        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="orders.xlsx"'
        df.to_excel(response, index=False)
        return response

    elif format == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="orders.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=landscape(letter))
        data = [['S.No', 'Number', 'Date', 'Product Name', 'Quantity', 'Order No', 'Payment Status', 'Pay Amount', 'Name', 'Phone No', 'Transaction Id', 'Seller Name', 'Address', 'Zipcode', 'City', 'Weight']]

        for i, product in enumerate(product_list, 1):
            data.append([
                i,
                product.customer.order.id,
                product.customer.order.created_at.strftime('%d-%m-%Y'),
                product.customer.order.product.name,
                1,
                product.customer.order.order_number,
                'Success' if product.status else 'Not Available',
                product.get_final_price(),
                product.customer.customer_name,
                product.customer.customer_phone,
                product.transaction_id,
                product.customer.order.product.seller_name_or_shop_name,
                product.customer.address_line1,
                product.customer.zipcode,
                product.customer.city,
                product.customer.order.product.weight if hasattr(product.customer.order.product, 'weight') else 'N/A'
            ])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        doc.build([table])
        return response

    else:
        return HttpResponse("Invalid Format")

@login_required
def navbar_headings(request):
    category = Display_Category.objects.filter(category__status=True).order_by('-status', 'category__name')
    return render(request, "admin_templates/navbar_headings.html", {"category": category})

def save_display_category(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        status = request.POST.get('status') == 'true'

        try:
            display_category = Display_Category.objects.get(category__id=category_id)
            display_category.status = status
            display_category.save()
            return JsonResponse({'status': 'success', 'message': 'Category status updated successfully.'})
        except Display_Category.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Category not found.'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})
@login_required
def p_order(request):
    if request.method == "POST":
        # Get data from POST request
        date = request.POST.get('date', None)
        product_name = request.POST.get('product_name', '')
        pay_amount = request.POST.get('pay_amount', '')
        name = request.POST.get('name', '')
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')
        zip_code = request.POST.get('zip_code', '')
        quntity = request.POST.get('quntity', '')
        pay_status = request.POST.get('pay_status', 'off') == 'on'
        transaction_id = request.POST.get('transaction_id', '')
        status = request.POST.get('status', 'off') == 'on'
        
        # Validation
        errors = []
        if not name:
            errors.append("Name is required.")
        if not phone.isdigit() or len(phone) != 10:
            errors.append("Enter a valid 10-digit phone number.")
        if pay_amount and not pay_amount.isdigit():
            errors.append("Payment amount must be a valid number.")
        if quntity and not quntity.isdigit():
            errors.append("Quantity must be a number.")
        if not date:
            date = datetime.now().date()  # Set current date if not provided

        # Return errors if validation fails
        if errors:
            return render(request, 'create_p_order.html', {'errors': errors})

        # Save to database
        p_order = P_Order(
            date=date,
            product_name=product_name,
            pay_amount=pay_amount,
            name=name,
            phone=phone,
            address=address,
            zip_code=zip_code,
            quntity=quntity,
            pay_status=pay_status,
            transaction_id=transaction_id,
            status=status,
        )
        p_order.save()
        return redirect('admin')  # Redirect to a success page

    return render(request, 'admin_templates/p_order.html')
@login_required
def p_order_list(request):
    product_list = P_Order.objects.filter(status=True).order_by('-id')
    paginator = Paginator(product_list, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request,"admin_templates/p_order_list.html",{"page_obj": page_obj})

@csrf_exempt
def update_check_p_order_status(request):
    if request.method == 'POST':
        product_id = request.POST.get('p_order_id')
        status = request.POST.get('status') == 'true'

        try:
            nav_item = P_Order.objects.get(id=product_id)
            nav_item.check_status = status
            nav_item.save()
            return JsonResponse({'success': True, 'message': 'Deleted successfully'})
        except P_Order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'P-Order not found'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
@csrf_exempt
def remove_p_order_status(request):
    if request.method == 'POST':
        product_id = request.POST.get('p_order_id')

        try:
            nav_item = P_Order.objects.get(id=product_id)
            nav_item.status = False
            nav_item.save()
            return JsonResponse({'success': True, 'message': 'Deleted successfully'})
        except P_Order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'P-Order not found'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
@login_required
def track_p_order(request,id):
    order=P_Order.objects.get(id=id)
    if request.method == "POST":
        Track.objects.create(track_number=request.POST["track_no"],weight=request.POST["weight"],mobile=request.POST["mobile"],status=True)
        order_detais=P_Order.objects.get(id=id)
        postal_tracking(request.POST["mobile"],order_detais.p_order_number,order.pay_amount,request.POST["track_no"])
        messages.success(request, 'successful Sended..')
        return redirect("p_order_list")
    return render(request,"admin_templates/track.html",{"order":order})
from datetime import datetime
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import P_Order

@csrf_exempt
def upload_orders(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        # try:
            # Read Excel or CSV
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        inserted_rows = 0
        print(df)
        for _, row in df.iterrows():
            print(row['date'])
            # Check required fields
            if pd.isnull(row['date']) or pd.isnull(row['product_name']) \
                    or pd.isnull(row['name']) or pd.isnull(row['phone']) or pd.isnull(row['address']) \
                    or pd.isnull(row['zip_code']) or pd.isnull(row['quntity']) :
                continue  # Skip row if any required field is missing

            # Handle date parsing
            date_val = row['date']
            if isinstance(date_val, str):
                date_parsed = datetime.fromisoformat(date_val).date()
            elif isinstance(date_val, (pd.Timestamp, datetime)):
                date_parsed = date_val.date()
            else:
                continue  # Skip invalid date
            # pay_status = True if str(row['pay_status']).strip() == '1' else False
            p_status = True if str(row['status']).strip() == '1' else False
            # Save valid row
            P_Order.objects.create(
                date=date_parsed,
                product_name=row['product_name'],
                # pay_amount=str(row['pay_amount']),
                name=row['name'],
                phone=row['phone'],
                address=row['address'],
                zip_code=str(row['zip_code']),
                quntity=int(row['quntity']),
                # pay_status=pay_status,
                # transaction_id=row['transaction_id'],
                status=p_status,
            )
            inserted_rows += 1

        return JsonResponse({'message': f'{inserted_rows} rows uploaded successfully.'})

        # except Exception as e:
        #     return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)
