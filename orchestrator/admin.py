from django.contrib import admin
from .models import UserProfile, InventoryItem, InventoryCategory, InventoryUnit

admin.site.register(UserProfile)
admin.site.register(InventoryItem)
admin.site.register(InventoryCategory)
admin.site.register(InventoryUnit)

