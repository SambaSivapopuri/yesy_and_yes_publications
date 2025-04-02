from rest_framework import serializers
from .models import P_Order

class POrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = P_Order
        fields = '__all__'
