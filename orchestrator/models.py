from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    CURRENCY_CHOICES = [
        ('AED', 'AED (dirham)'),
        ('USD', '$ (USD)'),
        ('GBP', '£ (GBP)'),
        ('EUR', '€ (EUR)'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    designation = models.CharField(max_length=100, default='Operations Manager')
    profile_pic_url = models.CharField(
        max_length=500, 
        default='https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=80&fit=crop&q=80'
    )
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='AED')

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Signals to automatically create/save UserProfile when a User is created/saved
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Ensure profile exists before saving
    if not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)
    instance.profile.save()


class InventoryCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class InventoryUnit(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class StorageLocation(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class KitchenLocation(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Vendor(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    LOCATION_CHOICES = [
        ('dry_pantry', 'Dry Pantry'),
        ('walk_in', 'Walk-in Cooler'),
        ('reach_in', 'Reach-in Fridge'),
        ('freezer', 'Freezer'),
    ]

    KITCHEN_CHOICES = [
        ('hessa_street', 'Hessa Street'),
        ('jbr', 'JBR'),
        ('meydan', 'Meydan'),
    ]
    sku = models.CharField(max_length=50, unique=True)
    purchase_item_name = models.CharField(max_length=100)
    generic_item_name = models.CharField(max_length=100)
    category = models.ForeignKey(InventoryCategory, on_delete=models.CASCADE, related_name='items')
    storage_location = models.ForeignKey(StorageLocation, on_delete=models.CASCADE, related_name='items')
    kitchen_location = models.ForeignKey(KitchenLocation, on_delete=models.CASCADE, related_name='items')
    purchase_unit = models.ForeignKey(InventoryUnit, on_delete=models.CASCADE, related_name='purchase_items')
    recipe_unit = models.ForeignKey(InventoryUnit, on_delete=models.CASCADE, related_name='recipe_items')
    par_level = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    qty_on_hand = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    recipe_unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    vendor = models.ForeignKey('Vendor', on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    invoice_number = models.CharField(max_length=100, blank=True, default='')
    invoice_date = models.DateField(null=True, blank=True)
    invoice_image = models.CharField(max_length=500, blank=True, default='')
    
    AUDIT_CHOICES = [
        ('Issue', 'Issue'),
        ('Verified', 'Verified'),
    ]
    audit = models.CharField(max_length=20, choices=AUDIT_CHOICES, default='Issue')

    audit_notes = models.CharField(max_length=50, blank=True, default='')

    @property
    def total_value(self):
        return self.qty_on_hand * self.unit_price

    @property
    def total_qty_on_hand(self):
        if not self.category_id or not self.generic_item_name:
            return self.qty_on_hand
        
        # Direct database query to fetch raw quantities and avoid recursion
        qtys = InventoryItem.objects.filter(
            category_id=self.category_id,
            generic_item_name__iexact=self.generic_item_name
        ).values_list('qty_on_hand', flat=True)
        return sum(qtys)

    @property
    def is_under_par(self):
        return self.total_qty_on_hand < self.par_level

    def save(self, *args, **kwargs):
        if not self.sku:
            from datetime import date
            today = date.today()
            # Category prefix: first 3 letters of category name, uppercase, letters only
            import re as _re
            cat_name = ''
            if self.category_id:
                try:
                    cat_name = InventoryCategory.objects.get(pk=self.category_id).name
                except InventoryCategory.DoesNotExist:
                    cat_name = 'GEN'
            letters_only = _re.sub(r'[^A-Za-z]', '', cat_name)
            cat_code = (letters_only[:3] if letters_only else 'GEN').upper()

            # Month and year parts
            mon_code = today.strftime('%b').upper()   # e.g. JUN
            yr_code  = today.strftime('%y')           # e.g. 26

            prefix = f"{cat_code}-{mon_code}-{yr_code}"

            # Find the highest existing increment globally across all items
            existing = InventoryItem.objects.all().values_list('sku', flat=True)
            max_num = 0
            for existing_sku in existing:
                try:
                    num_part = existing_sku.split('-')[-1]
                    max_num = max(max_num, int(num_part))
                except (ValueError, IndexError):
                    pass

            next_num = max_num + 1
            candidate = f"{prefix}-{str(next_num).zfill(3)}"

            # Guarantee uniqueness in case of race conditions
            while InventoryItem.objects.filter(sku=candidate).exists():
                next_num += 1
                candidate = f"{prefix}-{str(next_num).zfill(3)}"

            self.sku = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.purchase_item_name} ({self.sku})"


class Recipe(models.Model):
    recipe_name         = models.CharField(max_length=200)
    client_name         = models.CharField(max_length=200, blank=True, default='')
    cuisine             = models.CharField(max_length=100, blank=True, default='')
    servings            = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    actual_selling_price= models.DecimalField(max_digits=10, decimal_places=2, default=0)
    portion_cost        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    portion_food_cost_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    date                = models.DateField(null=True, blank=True)
    category            = models.CharField(max_length=100, blank=True, default='')
    subcategory         = models.CharField(max_length=100, blank=True, default='')
    price_without_tax   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vat_pct             = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    comment             = models.TextField(blank=True, default='')
    allergen            = models.CharField(max_length=500, blank=True, default='')
    preparation_steps   = models.TextField(blank=True, default='')
    packaging_type      = models.CharField(max_length=100, blank=True, default='')
    packaging_cost_with_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    approved_by_chef    = models.CharField(max_length=200, blank=True, default='')
    food_image          = models.ImageField(upload_to='recipe_images/', null=True, blank=True)
    modifier            = models.CharField(max_length=100, blank=True, default='None')
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.recipe_name

    @property
    def ingredient_total(self):
        return sum(ing.total for ing in self.ingredients.all())

    @property
    def vat_amount(self):
        return self.ingredient_total * (self.vat_pct / 100)

    @property
    def total_cost(self):
        return self.ingredient_total + self.vat_amount

    @property
    def total_food_cost_with_packaging(self):
        return self.total_cost + self.packaging_cost_with_tax


class RecipeIngredient(models.Model):
    recipe          = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
    generic_name    = models.CharField(max_length=200, blank=True, default='')
    purchase_name   = models.CharField(max_length=200, blank=True, default='')
    unit            = models.CharField(max_length=50, blank=True, default='')
    amount          = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    qty             = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    total           = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    order           = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.purchase_name} ({self.recipe.recipe_name})"


class CommissionInvoice(models.Model):
    month = models.CharField(max_length=50) # e.g. "June 2026"
    brand_name = models.CharField(max_length=150, blank=True, default='')
    license_name = models.CharField(max_length=150, blank=True, default='')
    orders = models.IntegerField(default=0)
    net_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    commission = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    cpc = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    advertisement_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    monthly_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        name = self.brand_name or self.license_name or "Unknown"
        return f"{name} - {self.month}"
