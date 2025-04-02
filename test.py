import requests
url="https://api.cashfree.com/api/v1/order/create"

payload={
    "appId":"87478d531a29f3a768d4b5fe887478",
    "secretKey":"d8b57d22a937864724b7feef4c03d2a14671cb5b",
    "orderId":"testing-112",
    "orderAmount":"10111",
    "orderCurrency":"INR",
    "orderNote":"testing",
    "customerName":"siva",
    "customerEmail":"samba01.sp@gmail.com",
    "customerPhone":"9133694958",
    "returnUrl":"https://cashfree.com",
    "notifyUrl":""
}
response=requests.request("POST",url,data=payload)
print(response.text)