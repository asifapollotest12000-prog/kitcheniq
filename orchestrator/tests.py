from django.test import TestCase, Client
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from .models import KitchenLocation, InventoryItem, InventoryCategory, StorageLocation, InventoryUnit, Recipe

class DashboardViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = "testuser"
        self.password = "testpass123"
        self.user = User.objects.create_user(username=self.username, password=self.password)
        
        # Create categories, storage locations, units, and kitchen locations
        self.category, _ = InventoryCategory.objects.get_or_create(name="Dry Goods")
        self.location, _ = StorageLocation.objects.get_or_create(name="Dry Pantry")
        self.unit, _ = InventoryUnit.objects.get_or_create(name="kg")
        self.kitchen1, _ = KitchenLocation.objects.get_or_create(name="Kitchen A")
        self.kitchen2, _ = KitchenLocation.objects.get_or_create(name="Kitchen B")
        
        # Create inventory items for testing calculations
        self.item1 = InventoryItem.objects.create(
            sku="DRY-JUL-26-001",
            purchase_item_name="Rice",
            generic_item_name="Rice",
            category=self.category,
            storage_location=self.location,
            kitchen_location=self.kitchen1,
            purchase_unit=self.unit,
            recipe_unit=self.unit,
            par_level=Decimal("10.00"),
            qty_on_hand=Decimal("5.00"),  # Under par
            unit_price=Decimal("2.50")    # Total value = 12.50, at risk = 12.50
        )
        self.item2 = InventoryItem.objects.create(
            sku="DRY-JUL-26-002",
            purchase_item_name="Flour",
            generic_item_name="Flour",
            category=self.category,
            storage_location=self.location,
            kitchen_location=self.kitchen2,
            purchase_unit=self.unit,
            recipe_unit=self.unit,
            par_level=Decimal("5.00"),
            qty_on_hand=Decimal("8.00"),   # Above par
            unit_price=Decimal("1.50")     # Total value = 12.00, at risk = 0.00
        )
        
        # Create a recipe to verify top/bottom recipe margins
        self.recipe = Recipe.objects.create(
            recipe_name="Test Cake",
            actual_selling_price=Decimal("15.00"),
            portion_cost=Decimal("5.00")
        )

    def test_dashboard_redirects_for_anonymous_user(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"/login/?next={reverse('dashboard')}")

    def test_dashboard_loads_for_logged_in_user(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orchestrator/dashboard.html')

    def test_dashboard_real_stats_calculation_all_sites(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('dashboard'))
        
        data = response.context['data']
        # Active alerts: item1 is under par, item2 is not under par. Total under par count = 1.
        self.assertEqual(data['alerts_active'], "1")
        
        # Inventory health calculations:
        # Total value = (5 * 2.50) + (8 * 1.50) = 12.50 + 12.00 = 24.50
        # At risk value = 12.50
        # At risk pct = 12.50 / 24.50 * 100 = 51.02%
        self.assertIn("24.50", data['inventory_health']['value'])
        self.assertIn("12.50", data['inventory_health']['at_risk'])
        self.assertEqual(data['inventory_health']['at_risk_pct'], "51.0%")
        
        # Recipe margins
        self.assertEqual(len(data['top_items']), 1)
        self.assertEqual(data['top_items'][0]['name'], "Test Cake")
        self.assertIn("10.00", data['top_items'][0]['margin'])
        self.assertEqual(data['top_items'][0]['margin_pct'], "66.7%")

    def test_dashboard_real_stats_calculation_filtered_site(self):
        self.client.login(username=self.username, password=self.password)
        # Filter by kitchen1
        response = self.client.get(f"{reverse('dashboard')}?site={self.kitchen1.id}")
        
        data = response.context['data']
        # For kitchen1, item1 is under par. Total under par count = 1.
        self.assertEqual(data['alerts_active'], "1")
        
        # Total value = 5 * 2.50 = 12.50
        # At risk value = 12.50
        # At risk pct = 100.0%
        self.assertIn("12.50", data['inventory_health']['value'])
        self.assertIn("12.50", data['inventory_health']['at_risk'])
        self.assertEqual(data['inventory_health']['at_risk_pct'], "100.0%")
        
        # Filter by kitchen2
        response = self.client.get(f"{reverse('dashboard')}?site={self.kitchen2.id}")
        data = response.context['data']
        # For kitchen2, item2 is above par. Total under par count = 0.
        self.assertEqual(data['alerts_active'], "0")
        self.assertIn("12.00", data['inventory_health']['value'])
        self.assertIn("0.00", data['inventory_health']['at_risk'])
        self.assertEqual(data['inventory_health']['at_risk_pct'], "0.0%")

    def test_dashboard_dummy_stats_are_zero(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('dashboard'))
        data = response.context['data']
        
        self.assertIn("0.00", data['sales_today'])
        self.assertEqual(data['sales_trend'], "0% vs yesterday")
        self.assertFalse(data['sales_trend_up'])
        self.assertEqual(data['orders_today'], "0")
        self.assertIn("0.00", data['margin_today'])
        self.assertIn("0.00", data['waste_today'])
        self.assertEqual(data['kitchen_load'], "0%")
        self.assertEqual(data['brand_margins'], [])
        self.assertEqual(data['recommendations'], [])
        self.assertEqual(data['waste_risk']['high'], 0)
        self.assertEqual(data['promotion_performance']['active'], 0)
        self.assertEqual(data['brand_opps']['high'], 0)

    @patch('PIL.Image.open')
    @patch('pytesseract.image_to_string')
    def test_scan_image_data_kitchen_detection(self, mock_tesseract, mock_image_open):
        from .views import scan_image_data
        
        # Case A: JBR in text
        mock_tesseract.return_value = "INVOICE\nBranch: JBR\nItem: Chicken\nQty: 2\nPrice: 10"
        _, _, _, _, kitchen = scan_image_data(b"fake bytes", "image/png")
        self.assertEqual(kitchen, "JBR")
        
        # Case B: Meydan in text
        mock_tesseract.return_value = "INVOICE\nAddress: Meydan road\nItem: Rice"
        _, _, _, _, kitchen = scan_image_data(b"fake bytes", "image/png")
        self.assertEqual(kitchen, "Meydan")
        
        # Case C: Hessa in text
        mock_tesseract.return_value = "INVOICE\nBranch: Hessa Street\nItem: Flour"
        _, _, _, _, kitchen = scan_image_data(b"fake bytes", "image/png")
        self.assertEqual(kitchen, "Hessa Street")
        
        # Case D: No match -> returns None (ocr_invoice_api will default this to Hessa Street)
        mock_tesseract.return_value = "INVOICE\nBranch: Downtown\nItem: Apples"
        _, _, _, _, kitchen = scan_image_data(b"fake bytes", "image/png")
        self.assertIsNone(kitchen)


class RecipeApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = "testuser"
        self.password = "testpass123"
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.client.login(username=self.username, password=self.password)
        
    def test_create_recipe_with_string_date(self):
        import json
        url = reverse('api_create_recipe')
        # We pass a date as a string "2026-07-14"
        payload = {
            'recipe_name': 'New Test Recipe',
            'date': '2026-07-14',
            'ingredients': []
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        resp_data = response.json()
        self.assertTrue(resp_data['success'])
        self.assertEqual(resp_data['recipe']['date'], '2026-07-14')

    def test_edit_recipe_with_string_date(self):
        import json
        recipe = Recipe.objects.create(recipe_name="Old Name", date="2026-07-10")
        url = reverse('api_edit_recipe', args=[recipe.id])
        payload = {
            'recipe_name': 'Updated Name',
            'date': '2026-07-14',
            'ingredients': []
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        resp_data = response.json()
        self.assertTrue(resp_data['success'])
        self.assertEqual(resp_data['recipe']['date'], '2026-07-14')

    def test_duplicate_recipe(self):
        import json
        recipe = Recipe.objects.create(recipe_name="Original Recipe", servings=2, actual_selling_price=Decimal("20.00"))
        from .models import RecipeIngredient
        RecipeIngredient.objects.create(
            recipe=recipe,
            generic_name="Water",
            purchase_name="Water bottle",
            unit="ml",
            amount=Decimal("1.50"),
            qty=Decimal("100"),
            total=Decimal("150.00"),
            order=0
        )
        url = reverse('api_duplicate_recipe')
        payload = {
            'recipe_id': recipe.id
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        resp_data = response.json()
        self.assertTrue(resp_data['success'])
        self.assertEqual(resp_data['new_recipe']['recipe_name'], "Original Recipe (Copy)")
        self.assertEqual(resp_data['new_recipe']['servings'], 2)
        
        # Verify duplicate created in DB and has ingredients
        dup_recipe = Recipe.objects.get(pk=resp_data['new_recipe']['id'])
        self.assertEqual(dup_recipe.recipe_name, "Original Recipe (Copy)")
        self.assertEqual(dup_recipe.ingredients.count(), 1)





