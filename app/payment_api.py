import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render,redirect,redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import requests
import json
from django.conf import settings
def payment_oreder(order_id,amount,name,email,mobile):
    try:
        url="https://api.cashfree.com/api/v1/order/create"

        payload={
            "appId":settings.CASHFREE_APP_ID,
            "secretKey":settings.CASHFREE_SECRET_KEY,
            "orderId":order_id,
            "orderAmount":amount,
            "orderCurrency":"INR",
            "orderNote":"Yes Publishers",
            "customerName":name,
            "customerEmail":email,
            "customerPhone":mobile,
            "returnUrl":f"https://test.digigenix.in/payment-success/{order_id}/{mobile}/{amount}/",#https://yesonlinebooks.com/payment-success/
            "notifyUrl":""
        }
        response=requests.request("POST",url,data=payload)
        
        return response.json()
    except Exception as e:
        return JsonResponse({"erorr":"Try agin.."},status=400)
@csrf_exempt
def payment_order_api(request):
    if request.method == "POST":
        try:
            data=json.loads(request.body)
            customer_id=data["customer_details"]["customer_id"]
           
            if 1==1:
                return JsonResponse({"payment_id":""},status=200)
            else:
                return JsonResponse({"error":"Order Creation failed"})
        except Exception as e:
            
            return JsonResponse({"erorr":str(e)},status=500)
    return JsonResponse({"error":"Invalid request method"},status=405)

