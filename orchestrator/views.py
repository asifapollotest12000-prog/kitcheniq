from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
import json
from decimal import Decimal
from django.db.models import Q
from .models import UserProfile, InventoryItem, InventoryCategory, InventoryUnit, Vendor, StorageLocation, KitchenLocation, Recipe, RecipeIngredient
from .forms import UserUpdateForm, UserProfileUpdateForm, InventoryItemForm


def get_currency_symbol(user):
    if user.is_authenticated:
        profile, created = UserProfile.objects.get_or_create(user=user)
        currency = profile.currency
    else:
        currency = 'AED'
        
    symbols = {
        'AED': 'AED ',
        'USD': '$',
        'GBP': '£',
        'EUR': '€'
    }
    return symbols.get(currency, 'AED ')




# Comprehensive Mock Data for the application
MOCK_DATA = {
    'all_sites': {
        'all_brands': {
            'sales_today': '£18,742', 'sales_trend': '+12.6% vs yesterday', 'sales_trend_up': True,
            'orders_today': '426', 'orders_trend': '+8.3% vs yesterday', 'orders_trend_up': True,
            'margin_today': '£5,862', 'margin_pct': '31.3%', 'margin_trend': '+4.1% vs yesterday', 'margin_trend_up': True,
            'waste_today': '£246', 'waste_pct': '1.3%', 'waste_trend': '-0.4% vs yesterday', 'waste_trend_up': False,
            'kitchen_load': '87%', 'kitchen_load_status': 'High', 'kitchen_load_trend': '+7% vs yesterday', 'kitchen_load_trend_up': True,
            'alerts_active': '12', 'alerts_status': 'Requires action',
            'brand_margins': [
                {'name': 'Burger Bros', 'value': 2311, 'pct': '39.5%', 'color': '#FF5E3A'},
                {'name': 'FryNation', 'value': 1734, 'pct': '29.6%', 'color': '#2E5BFF'},
                {'name': 'Pizza Palace', 'value': 987, 'pct': '16.9%', 'color': '#FFB020'},
                {'name': 'Bowl Culture', 'value': 543, 'pct': '9.3%', 'color': '#9C27B0'},
                {'name': 'Other Brands', 'value': 287, 'pct': '4.9%', 'color': '#A0AEC0'},
            ],
            'station_loads': [
                {'name': 'Fry Station', 'pct': 92, 'color': '#EF4444'},
                {'name': 'Grill Station', 'pct': 78, 'color': '#F97316'},
                {'name': 'Oven Station', 'pct': 65, 'color': '#EAB308'},
                {'name': 'Prep Station', 'pct': 72, 'color': '#22C55E'},
                {'name': 'Packing Station', 'pct': 88, 'color': '#EF4444'},
            ],
            'waste_risk': {
                'high': 23, 'high_pct': 28,
                'medium': 37, 'medium_pct': 45,
                'low': 22, 'low_pct': 27,
                'total_risk_items': 23
            },
            'top_items': [
                {'name': 'Classic Beef Burger', 'sales': '£1,872', 'margin': '£712', 'margin_pct': '38.0%'},
                {'name': 'Korean Fried Chicken', 'sales': '£1,541', 'margin': '£642', 'margin_pct': '41.6%'},
                {'name': 'Loaded Fries', 'sales': '£1,102', 'margin': '£492', 'margin_pct': '44.7%'},
                {'name': 'Margherita Pizza', 'sales': '£1,278', 'margin': '£415', 'margin_pct': '32.5%'},
                {'name': 'BBQ Chicken Bowl', 'sales': '£1,034', 'margin': '£372', 'margin_pct': '36.0%'},
            ],
            'bottom_items': [
                {'name': 'Vegan Salad Bowl', 'sales': '£420', 'margin': '£105', 'margin_pct': '25.0%'},
                {'name': 'Onion Rings Side', 'sales': '£310', 'margin': '£86', 'margin_pct': '27.7%'},
                {'name': 'Plain Hotdog', 'sales': '£280', 'margin': '£80', 'margin_pct': '28.5%'},
            ],
            'recommendations': [
                {'text': 'Reduce prep of Spicy Chicken Burger', 'sub': 'High overproduction risk', 'level': 'High'},
                {'text': 'Pause Loaded Fries during 7-9pm', 'sub': 'High station load impact', 'level': 'Medium'},
                {'text': 'Reprice Korean Fried Chicken', 'sub': 'Low margin after discounts', 'level': 'Medium'},
                {'text': 'Promote surplus ingredients', 'sub': '8 ingredients nearing expiry', 'level': 'Low'},
            ],
            'alerts_list': [
                {'text': 'High waste risk: 23 ingredients', 'time': '12m ago', 'type': 'danger'},
                {'text': 'Fry station overloaded', 'time': '18m ago', 'type': 'danger'},
                {'text': '3 items below margin target', 'time': '35m ago', 'type': 'warning'},
                {'text': 'Low stock: 7 critical ingredients', 'time': '1h ago', 'type': 'info'},
                {'text': 'Promotion margin alert', 'time': '2h ago', 'type': 'info'},
            ],
            'prep_vs_forecast': {'prepared': '92.4 kg', 'forecast': '101.5 kg', 'variance': '-9.1 kg', 'variance_pct': '-9.0%', 'is_good': False},
            'inventory_health': {'value': '£18,732', 'at_risk': '£2,341', 'at_risk_pct': '12.5%'},
            'promotion_performance': {'active': 6, 'incremental_sales': '£3,247', 'incremental_margin': '£612'},
            'brand_opps': {'high': 4, 'in_progress': 2, 'needs_review': 3},
            # Chart datasets (Sales & Margin for 7 days: 16 May - 22 May)
            'chart_dates': ['16 May', '17 May', '18 May', '19 May', '20 May', '21 May', '22 May'],
            'chart_sales': [15000, 18000, 17000, 19000, 21000, 20000, 18742],
            'chart_margin': [5200, 6100, 5800, 6800, 7200, 6500, 5862]
        },
        'burger_bros': {
            'sales_today': '£7,311', 'sales_trend': '+15.2% vs yesterday', 'sales_trend_up': True,
            'orders_today': '165', 'orders_trend': '+10.1% vs yesterday', 'orders_trend_up': True,
            'margin_today': '£2,311', 'margin_pct': '31.6%', 'margin_trend': '+5.8% vs yesterday', 'margin_trend_up': True,
            'waste_today': '£92', 'waste_pct': '1.2%', 'waste_trend': '-0.8% vs yesterday', 'waste_trend_up': False,
            'kitchen_load': '92%', 'kitchen_load_status': 'High', 'kitchen_load_trend': '+9% vs yesterday', 'kitchen_load_trend_up': True,
            'alerts_active': '4', 'alerts_status': 'Attention needed',
            'brand_margins': [{'name': 'Burger Bros', 'value': 2311, 'pct': '100%', 'color': '#FF5E3A'}],
            'station_loads': [
                {'name': 'Fry Station', 'pct': 95, 'color': '#EF4444'},
                {'name': 'Grill Station', 'pct': 92, 'color': '#EF4444'},
                {'name': 'Prep Station', 'pct': 80, 'color': '#EF4444'},
            ],
            'waste_risk': {'high': 8, 'high_pct': 40, 'medium': 9, 'medium_pct': 45, 'low': 3, 'low_pct': 15, 'total_risk_items': 8},
            'top_items': [
                {'name': 'Classic Beef Burger', 'sales': '£1,872', 'margin': '£712', 'margin_pct': '38.0%'},
                {'name': 'Korean Fried Chicken', 'sales': '£1,541', 'margin': '£642', 'margin_pct': '41.6%'},
                {'name': 'Loaded Fries', 'sales': '£1,102', 'margin': '£492', 'margin_pct': '44.7%'},
            ],
            'bottom_items': [
                {'name': 'Vegan Salad Bowl', 'sales': '£420', 'margin': '£105', 'margin_pct': '25.0%'},
            ],
            'recommendations': [
                {'text': 'Reduce prep of Spicy Chicken Burger', 'sub': 'High overproduction risk', 'level': 'High'},
                {'text': 'Pause Loaded Fries during 7-9pm', 'sub': 'High station load impact', 'level': 'Medium'},
            ],
            'alerts_list': [
                {'text': 'Grill station overloaded', 'time': '5m ago', 'type': 'danger'},
                {'text': 'Low stock: Hamburger buns', 'time': '1h ago', 'type': 'warning'},
            ],
            'prep_vs_forecast': {'prepared': '45.0 kg', 'forecast': '48.2 kg', 'variance': '-3.2 kg', 'variance_pct': '-6.6%', 'is_good': False},
            'inventory_health': {'value': '£6,230', 'at_risk': '£850', 'at_risk_pct': '13.6%'},
            'promotion_performance': {'active': 2, 'incremental_sales': '£1,200', 'incremental_margin': '£320'},
            'brand_opps': {'high': 1, 'in_progress': 1, 'needs_review': 0},
            'chart_dates': ['16 May', '17 May', '18 May', '19 May', '20 May', '21 May', '22 May'],
            'chart_sales': [6000, 7100, 6800, 7200, 7900, 7400, 7311],
            'chart_margin': [1900, 2200, 2100, 2300, 2500, 2300, 2311]
        }
    },
    'london': {
        'all_brands': {
            'sales_today': '£12,450', 'sales_trend': '+9.4% vs yesterday', 'sales_trend_up': True,
            'orders_today': '290', 'orders_trend': '+6.2% vs yesterday', 'orders_trend_up': True,
            'margin_today': '£3,950', 'margin_pct': '31.7%', 'margin_trend': '+3.2% vs yesterday', 'margin_trend_up': True,
            'waste_today': '£180', 'waste_pct': '1.4%', 'waste_trend': '+0.2% vs yesterday', 'waste_trend_up': True,
            'kitchen_load': '82%', 'kitchen_load_status': 'High', 'kitchen_load_trend': '+5% vs yesterday', 'kitchen_load_trend_up': True,
            'alerts_active': '8', 'alerts_status': 'Attention needed',
            'brand_margins': [
                {'name': 'Burger Bros', 'value': 1600, 'pct': '40.5%', 'color': '#FF5E3A'},
                {'name': 'FryNation', 'value': 1150, 'pct': '29.1%', 'color': '#2E5BFF'},
                {'name': 'Pizza Palace', 'value': 680, 'pct': '17.2%', 'color': '#FFB020'},
                {'name': 'Bowl Culture', 'value': 370, 'pct': '9.4%', 'color': '#9C27B0'},
                {'name': 'Other Brands', 'value': 150, 'pct': '3.8%', 'color': '#A0AEC0'},
            ],
            'station_loads': [
                {'name': 'Fry Station', 'pct': 88, 'color': '#EF4444'},
                {'name': 'Grill Station', 'pct': 74, 'color': '#F97316'},
                {'name': 'Oven Station', 'pct': 60, 'color': '#EAB308'},
                {'name': 'Prep Station', 'pct': 68, 'color': '#EAB308'},
                {'name': 'Packing Station', 'pct': 82, 'color': '#EF4444'},
            ],
            'waste_risk': {
                'high': 15, 'high_pct': 30,
                'medium': 25, 'medium_pct': 50,
                'low': 10, 'low_pct': 20,
                'total_risk_items': 15
            },
            'top_items': [
                {'name': 'Classic Beef Burger', 'sales': '£1,250', 'margin': '£480', 'margin_pct': '38.4%'},
                {'name': 'Korean Fried Chicken', 'sales': '£1,020', 'margin': '£420', 'margin_pct': '41.2%'},
                {'name': 'Loaded Fries', 'sales': '£780', 'margin': '£350', 'margin_pct': '44.9%'},
            ],
            'bottom_items': [
                {'name': 'Vegan Salad Bowl', 'sales': '£310', 'margin': '£78', 'margin_pct': '25.1%'},
            ],
            'recommendations': [
                {'text': 'Reduce prep of Spicy Chicken Burger', 'sub': 'High overproduction risk', 'level': 'High'},
                {'text': 'Reprice Korean Fried Chicken', 'sub': 'Low margin after discounts', 'level': 'Medium'},
            ],
            'alerts_list': [
                {'text': 'High waste risk: 15 ingredients', 'time': '10m ago', 'type': 'danger'},
                {'text': 'Fry station overloaded', 'time': '20m ago', 'type': 'danger'},
                {'text': 'Low stock: 4 critical ingredients', 'time': '1h ago', 'type': 'info'},
            ],
            'prep_vs_forecast': {'prepared': '68.5 kg', 'forecast': '72.0 kg', 'variance': '-3.5 kg', 'variance_pct': '-4.9%', 'is_good': False},
            'inventory_health': {'value': '£12,300', 'at_risk': '£1,560', 'at_risk_pct': '12.7%'},
            'promotion_performance': {'active': 4, 'incremental_sales': '£2,100', 'incremental_margin': '£410'},
            'brand_opps': {'high': 3, 'in_progress': 1, 'needs_review': 2},
            'chart_dates': ['16 May', '17 May', '18 May', '19 May', '20 May', '21 May', '22 May'],
            'chart_sales': [10000, 11500, 11000, 12500, 13800, 13100, 12450],
            'chart_margin': [3200, 3700, 3500, 4000, 4400, 4100, 3950]
        }
    }
}

# Add default fallback for other selections to prevent breaking errors
def get_mock_data(site, brand):
    site_key = site if site in MOCK_DATA else 'all_sites'
    brand_key = brand if brand in MOCK_DATA[site_key] else 'all_brands'
    
    if brand_key in MOCK_DATA[site_key]:
        return MOCK_DATA[site_key][brand_key]
    return MOCK_DATA['all_sites']['all_brands']

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
        
    return render(request, 'orchestrator/login.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    site = request.GET.get('site', 'all_sites')
    brand = request.GET.get('brand', 'all_brands')
    
    currency_symbol = get_currency_symbol(request.user)
    
    # 1. Populate sites/kitchens list dynamically from KitchenLocation model
    sites_list = [{'id': 'all_sites', 'name': 'All Sites'}]
    for kl in KitchenLocation.objects.all().order_by('name'):
        sites_list.append({'id': str(kl.id), 'name': kl.name})
        
    brands_list = [
        {'id': 'all_brands', 'name': 'All Brands'},
    ]
    
    # 2. Filter inventory items based on selected kitchen location (site)
    items_qs = InventoryItem.objects.all()
    if site != 'all_sites':
        try:
            items_qs = items_qs.filter(kitchen_location_id=int(site))
        except ValueError:
            pass
            
    # 3. Calculate real statistics from database
    under_par_count = sum(1 for item in items_qs if item.qty_on_hand < item.par_level)
    total_inventory_value = sum(item.qty_on_hand * item.unit_price for item in items_qs)
    at_risk_value = sum(item.qty_on_hand * item.unit_price for item in items_qs if item.qty_on_hand < item.par_level)
    at_risk_pct = (at_risk_value / total_inventory_value * 100) if total_inventory_value > 0 else 0.0

    # 4. Fetch actual recipe data for margin comparison
    recipes = list(Recipe.objects.prefetch_related('ingredients').all())
    recipe_data = []
    for r in recipes:
        margin = r.actual_selling_price - r.portion_cost
        margin_pct = (margin / r.actual_selling_price * 100) if r.actual_selling_price > 0 else 0.0
        recipe_data.append({
            'name': r.recipe_name,
            'sales': f"£{r.actual_selling_price:,.2f}",
            'margin': f"£{margin:,.2f}",
            'margin_pct': f"{margin_pct:.1f}%",
            'margin_value': margin
        })
        
    # Sort to determine top and bottom recipes
    top_items = sorted(recipe_data, key=lambda x: x['margin_value'], reverse=True)[:5]
    bottom_items = sorted(recipe_data, key=lambda x: x['margin_value'])[:3]

    # Dynamic date list for the charts (last 7 days)
    from datetime import date, timedelta
    today = date.today()
    chart_dates = [(today - timedelta(days=i)).strftime('%d %b') for i in range(6, -1, -1)]

    # Dynamic Alerts List based on under-par count
    alerts_list = []
    if under_par_count > 0:
        alerts_list.append({
            'text': f'Low stock: {under_par_count} critical ingredients under par level',
            'time': 'Now',
            'type': 'danger'
        })
    else:
        alerts_list.append({
            'text': 'All ingredients are above par level',
            'time': 'Now',
            'type': 'info'
        })

    # 5. Build dynamic data dictionary matching the structure used by dashboard templates
    data = {
        'sales_today': '£0.00',
        'sales_trend': '0% vs yesterday',
        'sales_trend_up': False,
        'orders_today': '0',
        'orders_trend': '0% vs yesterday',
        'orders_trend_up': False,
        'margin_today': '£0.00',
        'margin_pct': '0.0%',
        'margin_trend': '0% vs yesterday',
        'margin_trend_up': False,
        'waste_today': '£0.00',
        'waste_pct': '0.0%',
        'waste_trend': '0% vs yesterday',
        'waste_trend_up': False,
        'kitchen_load': '0%',
        'kitchen_load_status': 'Normal',
        'kitchen_load_trend': '0% vs yesterday',
        'kitchen_load_trend_up': False,
        'alerts_active': str(under_par_count),
        'alerts_status': 'Requires action' if under_par_count > 0 else 'Normal',
        'brand_margins': [],
        'station_loads': [
            {'name': 'Fry Station', 'pct': 0, 'color': '#EF4444'},
            {'name': 'Grill Station', 'pct': 0, 'color': '#F97316'},
            {'name': 'Oven Station', 'pct': 0, 'color': '#EAB308'},
            {'name': 'Prep Station', 'pct': 0, 'color': '#22C55E'},
            {'name': 'Packing Station', 'pct': 0, 'color': '#EF4444'},
        ],
        'waste_risk': {
            'high': 0,
            'high_pct': 0,
            'medium': 0,
            'medium_pct': 0,
            'low': 0,
            'low_pct': 0,
            'total_risk_items': 0
        },
        'top_items': top_items,
        'bottom_items': bottom_items,
        'recommendations': [],
        'alerts_list': alerts_list,
        'prep_vs_forecast': {
            'prepared': '0.0 kg',
            'forecast': '0.0 kg',
            'variance': '0.0 kg',
            'variance_pct': '0.0%',
            'is_good': True
        },
        'inventory_health': {
            'value': f"£{total_inventory_value:,.2f}",
            'at_risk': f"£{at_risk_value:,.2f}",
            'at_risk_pct': f"{at_risk_pct:.1f}%"
        },
        'promotion_performance': {
            'active': 0,
            'incremental_sales': '£0.00',
            'incremental_margin': '£0.00'
        },
        'brand_opps': {
            'high': 0,
            'in_progress': 0,
            'needs_review': 0
        },
        'chart_dates': chart_dates,
        'chart_sales': [0] * 7,
        'chart_margin': [0] * 7
    }

    # 6. Apply currency replacement
    def replace_currency(val):
        if isinstance(val, str):
            return val.replace('£', currency_symbol).replace('$', currency_symbol)
        return val
        
    data['sales_today'] = replace_currency(data['sales_today'])
    data['margin_today'] = replace_currency(data['margin_today'])
    data['waste_today'] = replace_currency(data['waste_today'])
    
    for item in data.get('top_items', []):
        item['sales'] = replace_currency(item['sales'])
        item['margin'] = replace_currency(item['margin'])
        
    for item in data.get('bottom_items', []):
        item['sales'] = replace_currency(item['sales'])
        item['margin'] = replace_currency(item['margin'])
        
    if 'inventory_health' in data:
        data['inventory_health']['value'] = replace_currency(data['inventory_health']['value'])
        data['inventory_health']['at_risk'] = replace_currency(data['inventory_health']['at_risk'])
        
    if 'promotion_performance' in data:
        data['promotion_performance']['incremental_sales'] = replace_currency(data['promotion_performance']['incremental_sales'])
        data['promotion_performance']['incremental_margin'] = replace_currency(data['promotion_performance']['incremental_margin'])

    context = {
        'selected_site': site,
        'selected_brand': brand,
        'selected_site_name': next((s['name'] for s in sites_list if s['id'] == site), 'All Sites'),
        'selected_brand_name': next((b['name'] for b in brands_list if b['id'] == brand), 'All Brands'),
        'sites': sites_list,
        'brands': brands_list,
        'data': data,
        'currency_symbol': currency_symbol,
        'chart_sales_json': json.dumps(data['chart_sales']),
        'chart_margin_json': json.dumps(data['chart_margin']),
        'chart_dates_json': json.dumps(data['chart_dates']),
        'brand_labels_json': json.dumps([b['name'] for b in data['brand_margins']]),
        'brand_values_json': json.dumps([b['value'] for b in data['brand_margins']]),
        'brand_colors_json': json.dumps([b['color'] for b in data['brand_margins']]),
    }
    
    return render(request, 'orchestrator/dashboard.html', context)


@login_required
def settings_view(request):
    # Restricted to admin only (superuser or staff)
    if not (request.user.is_superuser or request.user.is_staff):
        return render(request, 'orchestrator/403.html', status=403)
        
    # Get or create UserProfile for current user
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = UserProfileUpdateForm(request.POST, instance=profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Your settings have been updated successfully!")
            return redirect('settings')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = UserProfileUpdateForm(instance=profile)
        
    # Get dynamic currency symbol
    currency_symbol = get_currency_symbol(request.user)
        
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'currency_symbol': currency_symbol,
    }
    return render(request, 'orchestrator/settings.html', context)


def seed_inventory_data():
    # Setup initial categories
    categories = {
        'dry_goods': InventoryCategory.objects.get_or_create(name='Dry Goods & Pantry')[0],
        'produce': InventoryCategory.objects.get_or_create(name='Fresh Produce')[0],
        'proteins': InventoryCategory.objects.get_or_create(name='Proteins')[0],
        'dairy': InventoryCategory.objects.get_or_create(name='Dairy & Eggs')[0],
        'frozen': InventoryCategory.objects.get_or_create(name='Frozen Items')[0],
        'supplies': InventoryCategory.objects.get_or_create(name='Cleaning & Paper Goods')[0],
    }
    
    # Setup initial units
    units = {
        'kg': InventoryUnit.objects.get_or_create(name='kg')[0],
        'bag_50': InventoryUnit.objects.get_or_create(name='50 lb bag')[0],
        'liter': InventoryUnit.objects.get_or_create(name='Liter')[0],
        'box_24': InventoryUnit.objects.get_or_create(name='Box of 24')[0],
        'bag_10': InventoryUnit.objects.get_or_create(name='Bag of 10kg')[0],
        'case_1000': InventoryUnit.objects.get_or_create(name='Case of 1000')[0],
        'oz': InventoryUnit.objects.get_or_create(name='Ounces')[0],
        'g': InventoryUnit.objects.get_or_create(name='Grams')[0],
    }

    # Setup initial locations
    locations = {
        'dry_pantry': StorageLocation.objects.get_or_create(name='Dry Pantry')[0],
        'walk_in': StorageLocation.objects.get_or_create(name='Walk-in Cooler')[0],
        'reach_in': StorageLocation.objects.get_or_create(name='Reach-in Fridge')[0],
        'freezer': StorageLocation.objects.get_or_create(name='Freezer')[0],
    }

    # Setup initial kitchens
    kitchens = {
        'hessa_street': KitchenLocation.objects.get_or_create(name='Hessa Street')[0],
        'jbr': KitchenLocation.objects.get_or_create(name='JBR')[0],
        'meydan': KitchenLocation.objects.get_or_create(name='Meydan')[0],
    }

    sample_items = [
        {
            'sku': 'KI-10001', 'purchase_item_name': 'Whole Chicken', 'generic_item_name': 'Chicken',
            'category': categories['proteins'], 'storage_location': locations['walk_in'], 'kitchen_location': kitchens['hessa_street'],
            'purchase_unit': units['kg'], 'recipe_unit': units['kg'], 'par_level': 25.00,
            'qty_on_hand': 18.00, 'unit_price': 4.50
        },
        {
            'sku': 'KI-10002', 'purchase_item_name': 'Basmati Rice', 'generic_item_name': 'Rice',
            'category': categories['dry_goods'], 'storage_location': locations['dry_pantry'], 'kitchen_location': kitchens['hessa_street'],
            'purchase_unit': units['bag_50'], 'recipe_unit': units['kg'], 'par_level': 5.00,
            'qty_on_hand': 3.00, 'unit_price': 22.00
        },
        {
            'sku': 'KI-10003', 'purchase_item_name': 'Heavy Cream', 'generic_item_name': 'Cream',
            'category': categories['dairy'], 'storage_location': locations['reach_in'], 'kitchen_location': kitchens['hessa_street'],
            'purchase_unit': units['liter'], 'recipe_unit': units['liter'], 'par_level': 10.00,
            'qty_on_hand': 4.00, 'unit_price': 3.25
        },
        {
            'sku': 'KI-10004', 'purchase_item_name': 'Hass Avocados', 'generic_item_name': 'Avocado',
            'category': categories['produce'], 'storage_location': locations['reach_in'], 'kitchen_location': kitchens['hessa_street'],
            'purchase_unit': units['box_24'], 'recipe_unit': units['kg'], 'par_level': 8.00,
            'qty_on_hand': 10.00, 'unit_price': 25.00
        },
        {
            'sku': 'KI-10005', 'purchase_item_name': 'Frozen Peas', 'generic_item_name': 'Peas',
            'category': categories['frozen'], 'storage_location': locations['freezer'], 'kitchen_location': kitchens['hessa_street'],
            'purchase_unit': units['bag_10'], 'recipe_unit': units['kg'], 'par_level': 4.00,
            'qty_on_hand': 2.00, 'unit_price': 12.50
        },
        {
            'sku': 'KI-10006', 'purchase_item_name': 'Paper Napkins', 'generic_item_name': 'Napkins',
            'category': categories['supplies'], 'storage_location': locations['dry_pantry'], 'kitchen_location': kitchens['hessa_street'],
            'purchase_unit': units['case_1000'], 'recipe_unit': units['case_1000'], 'par_level': 12.00,
            'qty_on_hand': 15.00, 'unit_price': 18.00
        }
    ]
    for item in sample_items:
        InventoryItem.objects.get_or_create(sku=item['sku'], defaults=item)


@login_required
def inventory_view(request):

    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.qty_on_hand = Decimal('0.00')
            # Handle vendor (raw FK not in ModelForm)
            vendor_id = request.POST.get('vendor', '').strip()
            invoice_number = request.POST.get('invoice_number', '').strip()
            invoice_date_str = request.POST.get('invoice_date', '').strip()
            if vendor_id:
                try:
                    item.vendor = Vendor.objects.get(pk=int(vendor_id))
                except (Vendor.DoesNotExist, ValueError):
                    pass
            item.invoice_number = invoice_number
            if invoice_date_str:
                from datetime import datetime
                try:
                    item.invoice_date = datetime.strptime(invoice_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
            item.save()
            messages.success(request, f"Item '{item.purchase_item_name}' added successfully!")
            return redirect('inventory')
        else:
            messages.error(request, "Failed to add inventory item. Please correct errors below.")
    else:
        form = InventoryItemForm()

    # Get filters
    search_query = request.GET.get('search', '').strip()
    selected_category = request.GET.get('category', '')
    selected_location = request.GET.get('location', '')
    selected_kitchen = request.GET.get('kitchen', '')

    # Query items
    items = InventoryItem.objects.all()

    if search_query:
        items = items.filter(
            Q(sku__icontains=search_query) |
            Q(purchase_item_name__icontains=search_query) |
            Q(generic_item_name__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(storage_location__name__icontains=search_query) |
            Q(kitchen_location__name__icontains=search_query) |
            Q(vendor__name__icontains=search_query) |
            Q(invoice_number__icontains=search_query) |
            Q(purchase_unit__name__icontains=search_query) |
            Q(audit__icontains=search_query) |
            Q(audit_notes__icontains=search_query)
        )
    if selected_category and selected_category.isdigit():
        items = items.filter(category_id=selected_category)
    if selected_location:
        items = items.filter(storage_location=selected_location)
    if selected_kitchen:
        items = items.filter(kitchen_location=selected_kitchen)

    # Global inventory stats
    all_items = InventoryItem.objects.all()
    total_value = sum(item.qty_on_hand * item.unit_price for item in all_items)
    total_skus = all_items.count()
    under_par_count = sum(1 for item in all_items if item.qty_on_hand < item.par_level)
    
    # Calculate mock COGS valuation (e.g., 28.5% of total value)
    cogs_valuation = total_value * Decimal('0.285')
    
    # Get dynamic currency symbol
    currency_symbol = get_currency_symbol(request.user)

    # Extract unique generic names for autocomplete suggestion datalist
    unique_generic_names = sorted(list(set(InventoryItem.objects.values_list('generic_item_name', flat=True).distinct())))
    
    # Extract unique audit notes for autocomplete suggestion datalist
    unique_audit_notes = sorted(list(set(InventoryItem.objects.exclude(audit_notes='').exclude(audit_notes__isnull=True).values_list('audit_notes', flat=True).distinct())))
    
    context = {
        'items': items,
        'form': form,
        'total_value': total_value,
        'total_skus': total_skus,
        'under_par_count': under_par_count,
        'cogs_valuation': cogs_valuation,
        'selected_category': selected_category,
        'selected_location': selected_location,
        'selected_kitchen': selected_kitchen,
        'search_query': search_query,
        'currency_symbol': currency_symbol,
        'categories': InventoryCategory.objects.all(),
        'units': InventoryUnit.objects.all(),
        'vendors': Vendor.objects.all().order_by('name'),
        'locations': StorageLocation.objects.all().order_by('name'),
        'kitchens': KitchenLocation.objects.all().order_by('name'),
        'unique_generic_names': unique_generic_names,
        'unique_audit_notes': unique_audit_notes,
    }
    return render(request, 'orchestrator/inventory.html', context)


@login_required
def add_category_api(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({'error': 'Permission denied. Admins only.'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
        except json.JSONDecodeError:
            name = request.POST.get('name', '').strip()
            
        if not name:
            return JsonResponse({'error': 'Name is required'}, status=400)
            
        category, created = InventoryCategory.objects.get_or_create(name=name)
        return JsonResponse({'id': category.id, 'name': category.name, 'created': created})
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def add_unit_api(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({'error': 'Permission denied. Admins only.'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
        except json.JSONDecodeError:
            name = request.POST.get('name', '').strip()
            
        if not name:
            return JsonResponse({'error': 'Name is required'}, status=400)
            
        unit, created = InventoryUnit.objects.get_or_create(name=name)
        return JsonResponse({'id': unit.id, 'name': unit.name, 'created': created})
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def add_vendor_api(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({'error': 'Permission denied. Admins only.'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
        except json.JSONDecodeError:
            name = request.POST.get('name', '').strip()

        if not name:
            return JsonResponse({'error': 'Name is required'}, status=400)

        vendor, created = Vendor.objects.get_or_create(name=name)
        return JsonResponse({'id': vendor.id, 'name': vendor.name, 'created': created})
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def bulk_add_items_api(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({'error': 'Permission denied. Admins only.'}, status=403)
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
            
        if not items:
            return JsonResponse({'error': 'No items provided'}, status=400)
            
        created_count = 0
        errors = []
        
        for idx, item_data in enumerate(items):
            try:
                purchase_name = str(item_data.get('purchase_item_name') or '').strip()
                generic_name = str(item_data.get('generic_item_name') or '').strip()
                category_name = str(item_data.get('category') or '').strip()
                storage_location = str(item_data.get('storage_location') or '').strip()
                kitchen_location = str(item_data.get('kitchen_location') or 'hessa_street').strip()
                purchase_unit_name = str(item_data.get('purchase_unit') or '').strip()
                recipe_unit_name = str(item_data.get('recipe_unit') or '').strip()
                
                # Validation & conversions
                par_level = Decimal(str(item_data.get('par_level', '0.00') or '0.00'))
                qty_on_hand = Decimal(str(item_data.get('qty_on_hand', '0.00') or '0.00'))
                unit_price = Decimal(str(item_data.get('unit_price', '0.00') or '0.00'))
                recipe_unit_price = Decimal(str(item_data.get('recipe_unit_price', '0.00') or '0.00'))
                
                if not purchase_name:
                    errors.append(f"Row {idx + 1}: Purchase Item Name is required.")
                    continue
                if not category_name:
                    errors.append(f"Row {idx + 1}: Category is required.")
                    continue
                if not purchase_unit_name or not recipe_unit_name:
                    errors.append(f"Row {idx + 1}: Purchase and Recipe Units are required.")
                    continue
                if not storage_location:
                    errors.append(f"Row {idx + 1}: Storage Location is required.")
                    continue
                    
                if category_name.isdigit():
                    category = InventoryCategory.objects.get(id=int(category_name))
                else:
                    category, _ = InventoryCategory.objects.get_or_create(name=category_name)
                    
                if purchase_unit_name.isdigit():
                    p_unit = InventoryUnit.objects.get(id=int(purchase_unit_name))
                else:
                    p_unit, _ = InventoryUnit.objects.get_or_create(name=purchase_unit_name)
                    
                if recipe_unit_name.isdigit():
                    r_unit = InventoryUnit.objects.get(id=int(recipe_unit_name))
                else:
                    r_unit, _ = InventoryUnit.objects.get_or_create(name=recipe_unit_name)
                
                if storage_location.isdigit():
                    storage_loc = StorageLocation.objects.get(id=int(storage_location))
                else:
                    loc_map = {
                        'dry pantry': 'Dry Pantry', 'dry_pantry': 'Dry Pantry',
                        'walk-in cooler': 'Walk-in Cooler', 'walk-in': 'Walk-in Cooler', 'walk_in': 'Walk-in Cooler',
                        'reach-in fridge': 'Reach-in Fridge', 'reach-in': 'Reach-in Fridge', 'reach_in': 'Reach-in Fridge',
                        'freezer': 'Freezer'
                    }
                    storage_name = loc_map.get(storage_location.lower(), storage_location)
                    storage_loc, _ = StorageLocation.objects.get_or_create(name=storage_name)
                    
                if kitchen_location.isdigit():
                    kitchen_loc = KitchenLocation.objects.get(id=int(kitchen_location))
                else:
                    kit_map = {
                        'hessa_street': 'Hessa Street', 'hessa street': 'Hessa Street', 'hessa': 'Hessa Street',
                        'jbr': 'JBR',
                        'meydan': 'Meydan',
                        'cloud kitchen new york': 'Cloud Kitchen New York', 'new york': 'Cloud Kitchen New York', 'new_york': 'Cloud Kitchen New York',
                        'cloud kitchen tokyo': 'Cloud Kitchen Tokyo', 'tokyo': 'Cloud Kitchen Tokyo'
                    }
                    kitchen_name = kit_map.get(kitchen_location.lower(), 'Hessa Street')
                    kitchen_loc, _ = KitchenLocation.objects.get_or_create(name=kitchen_name)
                
                vendor_name = str(item_data.get('vendor') or '').strip()
                invoice_number = str(item_data.get('invoice_number') or '').strip()
                invoice_date_str = str(item_data.get('invoice_date') or '').strip()
                vendor_obj = None
                if vendor_name:
                    if vendor_name.isdigit():
                        vendor_obj = Vendor.objects.get(id=int(vendor_name))
                    else:
                        vendor_obj, _ = Vendor.objects.get_or_create(name=vendor_name)
                invoice_date_val = None
                if invoice_date_str:
                    from datetime import datetime, date as _date
                    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y'):
                        try:
                            parsed = datetime.strptime(invoice_date_str, fmt).date()
                            # Reject future dates — store as blank
                            if parsed <= _date.today():
                                invoice_date_val = parsed
                            break
                        except ValueError:
                            pass

                audit = str(item_data.get('audit', 'Issue')).strip() or 'Issue'
                audit_notes = str(item_data.get('audit_notes', '')).strip()[:50]
                invoice_image = str(item_data.get('invoice_image') or '').strip()
                InventoryItem.objects.create(
                    purchase_item_name=purchase_name,
                    generic_item_name=generic_name or purchase_name,
                    category=category,
                    storage_location=storage_loc,
                    kitchen_location=kitchen_loc,
                    purchase_unit=p_unit,
                    recipe_unit=r_unit,
                    par_level=par_level,
                    qty_on_hand=qty_on_hand,
                    unit_price=unit_price,
                    recipe_unit_price=recipe_unit_price,
                    vendor=vendor_obj,
                    invoice_number=invoice_number,
                    invoice_date=invoice_date_val,
                    invoice_image=invoice_image,
                    audit=audit,
                    audit_notes=audit_notes,
                )
                created_count += 1
            except Exception as e:
                errors.append(f"Row {idx + 1}: Unexpected error: {str(e)}")
                
        if errors:
            return JsonResponse({
                'success': False, 
                'created_count': created_count,
                'errors': errors
            }, status=400)
            
        return JsonResponse({'success': True, 'created_count': created_count})
        
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def clean_item_name(name):
    if not name:
        return ""
    import re
    cleaned = name
    
    # Remove e.g. "10 x 100g", "2x500ml", etc.
    cleaned = re.sub(r'\b\d+\s*[xX]\s*\d+\s*(?:g|kg|ml|l|pcs|gram|grams|oz)?\b', '', cleaned, flags=re.IGNORECASE)
    
    # Remove e.g. "1kg", "500 g", "250gram", "1.5L", "330ml", "10pcs", "12 pack", "6pk"
    cleaned = re.sub(r'\b\d+(?:\.\d+)?\s*(?:kg|g|gram|grams|ml|l|liter|liters|pcs|oz|lbs|lb|pk|pack|packs|box|bag|bottle|carton)\b', '', cleaned, flags=re.IGNORECASE)
    
    # Remove loose numbers (e.g. "whole chicken 1200" or "chicken 12")
    cleaned = re.sub(r'\b\d{3,4}\b', '', cleaned)
    
    # Remove common brand names
    brands = [
        "gate", "lacprodan", "heinz", "kraft", "nestle", "anchor", "almarai", "sadia", 
        "knorr", "hellmanns", "mccain", "chiquita", "dole", "del monte", "philadelphia",
        "lurpak", "president", "arla", "monin", "tabasco"
    ]
    for brand in brands:
        cleaned = re.sub(r'\b' + brand + r'\b', '', cleaned, flags=re.IGNORECASE)
        
    # Clean up double spaces, punctuation, and leading/trailing spaces
    cleaned = re.sub(r'[\(\)\-\+\*\/\[\]\:\,\.\#\_\=\&]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned


def get_category_storage_and_generic_by_name(item_name):
    """
    Returns (category_name, storage_location_code, generic_name) based on keywords in the item_name.
    """
    if not item_name:
        return 'Ingredients', 'walk_in', ''
    
    cleaned_name = clean_item_name(item_name)
    if not cleaned_name:
        cleaned_name = item_name
        
    name_lower = cleaned_name.lower()
    
    # 1. Cheese
    if "cream cheese" in name_lower:
        return "Cheese", "walk_in", "Cream Cheese"
    if "mozzarella" in name_lower:
        return "Cheese", "walk_in", "Mozzarella"
    if "cheddar" in name_lower:
        return "Cheese", "walk_in", "Cheddar"
    if "parmesan" in name_lower:
        return "Cheese", "walk_in", "Parmesan"
    if "feta" in name_lower:
        return "Cheese", "walk_in", "Feta"
    if "cheese" in name_lower:
        return "Cheese", "walk_in", "Cheese"
    
    # 2. Milk & Cream
    if "whole milk" in name_lower:
        return "Milk & Cream", "walk_in", "Whole Milk"
    if "buttermilk" in name_lower:
        return "Milk & Cream", "walk_in", "Buttermilk"
    if "heavy cream" in name_lower:
        return "Milk & Cream", "walk_in", "Heavy Cream"
    if "milk" in name_lower:
        return "Milk & Cream", "walk_in", "Whole Milk"
    if "cream" in name_lower:
        return "Milk & Cream", "walk_in", "Heavy Cream"
        
    # 3. Fats
    if "unsalted butter" in name_lower:
        return "Fats", "dry_pantry", "Unsalted Butter"
    if "butter" in name_lower:
        return "Fats", "dry_pantry", "Unsalted Butter"
    if "margarine" in name_lower:
        return "Fats", "dry_pantry", "Margarine"
    if "canola oil" in name_lower:
        return "Fats", "dry_pantry", "Canola Oil"
    if "canola" in name_lower:
        return "Fats", "dry_pantry", "Canola Oil"
    if "vegetable oil" in name_lower:
        return "Fats", "dry_pantry", "Vegetable Oil"
    if "vegetable" in name_lower and ("oil" in name_lower or "fat" in name_lower):
        return "Fats", "dry_pantry", "Vegetable Oil"
    if "heavy oil" in name_lower or "heavy oils" in name_lower:
        return "Fats", "dry_pantry", "Heavy Oil"
        
    # 4. Oils
    if "extra virgin olive oil" in name_lower:
        return "Oils", "dry_pantry", "Extra Virgin Olive Oil"
    if "olive oil" in name_lower:
        return "Oils", "dry_pantry", "Extra Virgin Olive Oil"
    if "sesame oil" in name_lower:
        return "Oils", "dry_pantry", "Sesame Oil"
    if "peanut oil" in name_lower:
        return "Oils", "dry_pantry", "Peanut Oil"
        
    # 5. Vinegars
    if "balsamic" in name_lower:
        return "Vinegars", "dry_pantry", "Balsamic Vinegar"
    if "apple cider" in name_lower:
        return "Vinegars", "dry_pantry", "Apple Cider Vinegar"
    if "white distilled" in name_lower:
        return "Vinegars", "dry_pantry", "White Distilled Vinegar"
    if "rice wine" in name_lower:
        return "Vinegars", "dry_pantry", "Rice Wine Vinegar"
    if "vinegar" in name_lower:
        return "Vinegars", "dry_pantry", "Balsamic Vinegar"
        
    # 6. Sauces & Pastes
    if "tomato puree" in name_lower:
        return "Sauces & Pastes", "dry_pantry", "Tomato Puree"
    if "tomato ketchup" in name_lower:
        return "Sauces & Pastes", "dry_pantry", "Tomato Ketchup"
    if "ketchup" in name_lower:
        return "Sauces & Pastes", "dry_pantry", "Tomato Ketchup"
    if "soy sauce" in name_lower:
        return "Sauces & Pastes", "dry_pantry", "Soy Sauce"
    if "worcestershire" in name_lower:
        return "Sauces & Pastes", "dry_pantry", "Worcestershire Sauce"
    if "hot sauce" in name_lower:
        return "Sauces & Pastes", "dry_pantry", "Hot Sauce"
    if "mustard" in name_lower:
        return "Sauces & Pastes", "dry_pantry", "Mustard"
    if "tomato paste" in name_lower:
        return "Sauces & Pastes", "dry_pantry", "Tomato Puree"
    if "sauce" in name_lower:
        return "Sauces & Pastes", "dry_pantry", "Sauce"
    if "paste" in name_lower:
        return "Sauces & Pastes", "dry_pantry", "Paste"
        
    # 7. Dry Spices
    if "black pepper" in name_lower:
        return "Dry Spices", "dry_pantry", "Black Pepper"
    if "garlic powder" in name_lower:
        return "Dry Spices", "dry_pantry", "Garlic Powder"
    if "chili flakes" in name_lower:
        return "Dry Spices", "dry_pantry", "Chili Flakes"
    if "cumin" in name_lower:
        return "Dry Spices", "dry_pantry", "Cumin"
    if "paprika" in name_lower:
        return "Dry Spices", "dry_pantry", "Paprika"
    if "oregano" in name_lower:
        return "Dry Spices", "dry_pantry", "Oregano"
    if "spice" in name_lower:
        return "Dry Spices", "dry_pantry", "Spice"
    import re
    if re.search(r'\b(salt)\b', name_lower):
        return "Dry Spices", "dry_pantry", "Salt"
        
    # 8. Flour & Baking
    if "all-purpose flour" in name_lower:
        return "Flour & Baking", "dry_pantry", "All-purpose Flour"
    if "flour" in name_lower:
        return "Flour & Baking", "dry_pantry", "All-purpose Flour"
    if "cornstarch" in name_lower:
        return "Flour & Baking", "dry_pantry", "Cornstarch"
    if "baking powder" in name_lower:
        return "Flour & Baking", "dry_pantry", "Baking Powder"
    if "baking soda" in name_lower:
        return "Flour & Baking", "dry_pantry", "Baking Soda"
    if "yeast" in name_lower:
        return "Flour & Baking", "dry_pantry", "Yeast"
    if "baking" in name_lower:
        return "Flour & Baking", "dry_pantry", "Baking Ingredient"
        
    # 9. Grains & Pasta
    if "basmati rice" in name_lower:
        return "Grains & Pasta", "dry_pantry", "Basmati Rice"
    if "arborio rice" in name_lower:
        return "Grains & Pasta", "dry_pantry", "Arborio Rice"
    if "basmati" in name_lower:
        return "Grains & Pasta", "dry_pantry", "Basmati Rice"
    if "arborio" in name_lower:
        return "Grains & Pasta", "dry_pantry", "Arborio Rice"
    if "rice" in name_lower:
        return "Grains & Pasta", "dry_pantry", "Basmati Rice"
    if "quinoa" in name_lower:
        return "Grains & Pasta", "dry_pantry", "Quinoa"
    if "penne" in name_lower:
        return "Grains & Pasta", "dry_pantry", "Penne"
    if "spaghetti" in name_lower:
        return "Grains & Pasta", "dry_pantry", "Spaghetti"
    if "pasta" in name_lower:
        return "Grains & Pasta", "dry_pantry", "Pasta"
        
    # 10. Dried Goods
    if "dried fruit" in name_lower or "dried fruits" in name_lower:
        if "raisin" in name_lower or "raisins" in name_lower:
            return "Dried Goods", "dry_pantry", "Raisins"
        if "apricot" in name_lower or "apricots" in name_lower:
            return "Dried Goods", "dry_pantry", "Apricots"
        return "Dried Goods", "dry_pantry", "Dried Fruits"
    if "raisin" in name_lower or "raisins" in name_lower:
        return "Dried Goods", "dry_pantry", "Raisins"
    if "apricot" in name_lower or "apricots" in name_lower:
        return "Dried Goods", "dry_pantry", "Apricots"
    if "almond" in name_lower or "almonds" in name_lower:
        return "Dried Goods", "dry_pantry", "Almonds"
    if "cashew" in name_lower or "cashews" in name_lower:
        return "Dried Goods", "dry_pantry", "Cashews"
    if "nut" in name_lower or "nuts" in name_lower:
        return "Dried Goods", "dry_pantry", "Nuts"
        
    # 11. Citrus
    if "lemon" in name_lower or "lemons" in name_lower:
        return "Citrus", "walk_in", "Lemons"
    if "lime" in name_lower or "limes" in name_lower:
        return "Citrus", "walk_in", "Limes"
    if "orange" in name_lower or "oranges" in name_lower:
        return "Citrus", "walk_in", "Oranges"
    if "citrus" in name_lower:
        return "Citrus", "walk_in", "Citrus"
        
    # 12. Herbs
    if "cilantro" in name_lower:
        return "Herbs", "walk_in", "Cilantro"
    if "parsley" in name_lower:
        return "Herbs", "walk_in", "Parsley"
    if "basil" in name_lower:
        return "Herbs", "walk_in", "Basil"
    if "rosemary" in name_lower:
        return "Herbs", "walk_in", "Rosemary"
    if "thyme" in name_lower:
        return "Herbs", "walk_in", "Thyme"
    if "mint" in name_lower:
        return "Herbs", "walk_in", "Mint"
    if "herb" in name_lower or "herbs" in name_lower:
        return "Herbs", "walk_in", "Herbs"
        
    # 13. Eggs
    if "egg white" in name_lower or "egg whites" in name_lower:
        return "Eggs", "walk_in", "Egg Whites"
    if "whole egg" in name_lower or "whole eggs" in name_lower:
        return "Eggs", "walk_in", "Whole Eggs"
    if re.search(r'\b(eggs|egg)\b', name_lower):
        return "Eggs", "walk_in", "Whole Eggs"
        
    # 14. Leafy Greens & Veggies
    if "spinach" in name_lower:
        return "Leafy Greens & Veggies", "walk_in", "Spinach"
    if "lettuce" in name_lower:
        return "Leafy Greens & Veggies", "walk_in", "Lettuce"
    if "tomato" in name_lower or "tomatoes" in name_lower:
        return "Leafy Greens & Veggies", "walk_in", "Tomatoes"
    if "bell pepper" in name_lower or "bell peppers" in name_lower:
        return "Leafy Greens & Veggies", "walk_in", "Bell Peppers"
    if "pepper" in name_lower or "peppers" in name_lower:
        return "Leafy Greens & Veggies", "walk_in", "Bell Peppers"
    if "mushroom" in name_lower or "mushrooms" in name_lower:
        return "Leafy Greens & Veggies", "walk_in", "Mushrooms"
    if "carrot" in name_lower or "carrots" in name_lower:
        return "Leafy Greens & Veggies", "walk_in", "Carrots"
    if "vegetable" in name_lower or "vegetables" in name_lower or "veggie" in name_lower or "veggies" in name_lower:
        return "Leafy Greens & Veggies", "walk_in", "Vegetables"
        
    # 15. Alliums
    if "onion" in name_lower or "onions" in name_lower:
        if "yellow" in name_lower:
            return "Alliums", "dry_pantry", "Yellow Onions"
        if "red" in name_lower:
            return "Alliums", "dry_pantry", "Red Onions"
        if "white" in name_lower:
            return "Alliums", "dry_pantry", "White Onions"
        return "Alliums", "dry_pantry", "Onions"
    if "garlic" in name_lower:
        return "Alliums", "dry_pantry", "Garlic"
    if "shallot" in name_lower or "shallots" in name_lower:
        return "Alliums", "dry_pantry", "Shallots"
    if "leek" in name_lower or "leeks" in name_lower:
        return "Alliums", "dry_pantry", "Leeks"
        
    # 16. Plant-Based
    if "tofu" in name_lower:
        return "Plant-Based", "walk_in", "Tofu"
    if "tempeh" in name_lower:
        return "Plant-Based", "walk_in", "Tempeh"
    if "seitan" in name_lower:
        return "Plant-Based", "walk_in", "Seitan"
    if "bean" in name_lower or "beans" in name_lower:
        return "Plant-Based", "walk_in", "Beans"
    if "lentil" in name_lower or "lentils" in name_lower:
        return "Plant-Based", "walk_in", "Lentils"
        
    # 17. Seafood
    if "whitefish" in name_lower:
        if "cod" in name_lower:
            return "Seafood", "walk_in", "Cod"
        if "halibut" in name_lower:
            return "Seafood", "walk_in", "Halibut"
        return "Seafood", "walk_in", "Whitefish"
    if "cod" in name_lower:
        return "Seafood", "walk_in", "Cod"
    if "halibut" in name_lower:
        return "Seafood", "walk_in", "Halibut"
    if "salmon" in name_lower:
        return "Seafood", "walk_in", "Salmon"
    if "shrimp" in name_lower:
        return "Seafood", "walk_in", "Shrimp"
    if "crab" in name_lower:
        return "Seafood", "walk_in", "Crab"
    if "squid" in name_lower:
        return "Seafood", "walk_in", "Squid"
    if "fish" in name_lower:
        return "Seafood", "walk_in", "Fish"
    if "seafood" in name_lower:
        return "Seafood", "walk_in", "Seafood"
        
    # 18. Meat & Poultry
    if "chicken" in name_lower:
        return "Meat & Poultry", "walk_in", "Chicken"
    if "beef" in name_lower:
        return "Meat & Poultry", "walk_in", "Beef"
    if "mutton" in name_lower:
        return "Meat & Poultry", "walk_in", "Mutton"
    if "lamb" in name_lower:
        return "Meat & Poultry", "walk_in", "Lamb"
    if "poultry" in name_lower:
        return "Meat & Poultry", "walk_in", "Poultry"
        
    return "Ingredients", "walk_in", item_name.title()


@login_required
def lookup_learned_mapping_api(request):
    purchase_name = request.GET.get('purchase_item_name', '').strip()
    vendor_id = request.GET.get('vendor_id', '').strip()
    vendor_name = request.GET.get('vendor_name', '').strip()
    
    if not purchase_name:
        return JsonResponse({'found': False})
        
    query = Q(purchase_item_name__iexact=purchase_name)
    
    if vendor_id and vendor_id.isdigit():
        query &= Q(vendor_id=int(vendor_id))
    elif vendor_name:
        query &= Q(vendor__name__iexact=vendor_name)
        
    item = InventoryItem.objects.filter(query).order_by('-id').first()
    
    if item:
        return JsonResponse({
            'found': True,
            'generic_item_name': item.generic_item_name,
            'category_id': item.category_id,
            'category_name': item.category.name,
            'storage_location_id': item.storage_location_id,
            'storage_location_name': item.storage_location.name,
            'recipe_unit_id': item.recipe_unit_id,
            'recipe_unit_name': item.recipe_unit.name,
            'recipe_unit_price': str(item.recipe_unit_price),
        })
        
    return JsonResponse({'found': False})


def scan_image_data(image_bytes, content_type):
    import base64
    import json
    import re
    
    vendor_name = ''
    invoice_number = ''
    invoice_date = ''
    raw_items = []
    detected_kitchen = None
    parsed_via_json = False

    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    data_url = f"data:{content_type};base64,{base64_image}"

    # 1. Try Google AI Studio (Gemini) in Structured JSON mode
    from django.conf import settings
    import os
    gemini_key = os.environ.get('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', None)
    if gemini_key:
        try:
            from google import genai
            from google.genai import types
            import pydantic

            class InvoiceItem(pydantic.BaseModel):
                purchase_item_name: str
                qty: float
                unit_price: float

            class InvoiceData(pydantic.BaseModel):
                vendor_name: str
                invoice_number: str
                invoice_date: str
                kitchen_location: str
                items: list[InvoiceItem]

            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=content_type,
                    ),
                    "Analyze this receipt or invoice image and output a JSON object containing the invoice details matching the schema."
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=InvoiceData,
                    temperature=0.1,
                ),
            )
            completion_text = response.text
            res_data = json.loads(completion_text)
            vendor_name = res_data.get('vendor_name', '').strip()
            invoice_number = res_data.get('invoice_number', '').strip()
            invoice_date = res_data.get('invoice_date', '').strip()
            
            # Detect kitchen location
            kit_loc = res_data.get('kitchen_location', '').strip().lower()
            if 'jbr' in kit_loc:
                detected_kitchen = 'JBR'
            elif 'meydan' in kit_loc:
                detected_kitchen = 'Meydan'
            elif 'hessa' in kit_loc:
                detected_kitchen = 'Hessa Street'
            
            if not detected_kitchen:
                text_search = completion_text.lower()
                if 'jbr' in text_search:
                    detected_kitchen = 'JBR'
                elif 'meydan' in text_search:
                    detected_kitchen = 'Meydan'
                elif 'hessa' in text_search:
                    detected_kitchen = 'Hessa Street'
            
            units = ['KG', 'PKT', 'PCS', 'BOX', 'BAG', 'L', 'ML', 'G', 'GRAM', 'BOTTLE', 'CARTON', 'CASE']
            unit_pattern = r'\b(' + '|'.join(units) + r')\b'

            for item in res_data.get('items', []):
                desc = item.get('purchase_item_name', '').strip()
                qty = float(item.get('qty', 1.0))
                price = float(item.get('unit_price', 0.0))
                
                # Clean prefix tags or barcode noise if any remain
                desc = re.sub(r'^\d+[\s\.\-\+\*\/]*', '', desc)
                desc = re.sub(r'^[A-Z0-9]{4,10}[\s\.\-\+\*\/]*', '', desc)
                desc = desc.strip('/ ').strip()
                
                unit = 'PCS'
                unit_match = re.search(unit_pattern, desc, re.IGNORECASE)
                if unit_match:
                    unit = unit_match.group(1).upper()
                
                # Search database for learned mapping
                learned_item = None
                if vendor_name:
                    learned_item = InventoryItem.objects.filter(
                        purchase_item_name__iexact=desc,
                        vendor__name__iexact=vendor_name
                    ).order_by('-id').first()
                else:
                    learned_item = InventoryItem.objects.filter(
                        purchase_item_name__iexact=desc
                    ).order_by('-id').first()

                if learned_item:
                    category_val = learned_item.category.name
                    loc_code_map = {
                        'Dry Pantry': 'dry_pantry',
                        'Walk-in Cooler': 'walk_in',
                        'Reach-in Fridge': 'reach_in',
                        'Freezer': 'freezer'
                    }
                    storage_loc = loc_code_map.get(learned_item.storage_location.name, 'walk_in')
                    generic_val = learned_item.generic_item_name
                    recipe_unit = learned_item.recipe_unit.name
                    recipe_price = f"{learned_item.recipe_unit_price:.2f}"
                else:
                    category_val, storage_loc, generic_val = get_category_storage_and_generic_by_name(desc)
                    recipe_unit = unit
                    recipe_price = f"{price:.2f}"

                raw_items.append({
                    'purchase_item_name': desc,
                    'generic_item_name':  generic_val or desc,
                    'category':           category_val,
                    'storage_location':   storage_loc,
                    'kitchen_location':   detected_kitchen or '',
                    'purchase_unit':      unit,
                    'recipe_unit':        recipe_unit,
                    'par_level':          '10.00',
                    'qty_on_hand':        f"{qty:.2f}",
                    'unit_price':         f"{price:.2f}",
                    'recipe_unit_price':  recipe_price,
                })
            parsed_via_json = True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Google AI Studio (Gemini) vision extraction failed. Error: {str(e)}")

    # 1.5. Try Groq Vision in Structured JSON mode with key rotation (if Gemini not parsed)
    if not parsed_via_json:
        groq_keys = [
            "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",
            "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",
            "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",
            "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",
            "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",
            "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",
            "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"
        ]

        for key in groq_keys:
            try:
                from groq import Groq
                client = Groq(api_key=key)
                completion = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[
                      {
                        "role": "user",
                        "content": [
                          {
                            "type": "text",
                            "text": (
                                "Analyze this receipt or invoice image and output a JSON object containing the invoice details. "
                                "You must output ONLY a valid JSON object matching this schema: "
                                "{\n"
                                "  \"vendor_name\": \"string (e.g. GATE)\",\n"
                                "  \"invoice_number\": \"string (e.g. Slip/Invoice number)\",\n"
                                "  \"invoice_date\": \"string in YYYY-MM-DD format (or empty if not found)\",\n"
                                "  \"kitchen_location\": \"string (branch/location name if mentioned on the invoice, e.g. Hessa Street, JBR, Meydan, or empty if not found)\",\n"
                                "  \"items\": [\n"
                                "    {\n"
                                "      \"purchase_item_name\": \"string (clean product name without barcodes or noise)\",\n"
                                "      \"qty\": number,\n"
                                "      \"unit_price\": number\n"
                                "    }\n"
                                "  ]\n"
                                "}"
                            )
                          },
                          {
                            "type": "image_url",
                            "image_url": {
                              "url": data_url
                            }
                          }
                        ]
                      }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=1024,
                )
                
                completion_text = completion.choices[0].message.content
                res_data = json.loads(completion_text)
                vendor_name = res_data.get('vendor_name', '').strip()
                invoice_number = res_data.get('invoice_number', '').strip()
                invoice_date = res_data.get('invoice_date', '').strip()
                
                # Detect kitchen location
                kit_loc = res_data.get('kitchen_location', '').strip().lower()
                if 'jbr' in kit_loc:
                    detected_kitchen = 'JBR'
                elif 'meydan' in kit_loc:
                    detected_kitchen = 'Meydan'
                elif 'hessa' in kit_loc:
                    detected_kitchen = 'Hessa Street'
                
                if not detected_kitchen:
                    text_search = completion_text.lower()
                    if 'jbr' in text_search:
                        detected_kitchen = 'JBR'
                    elif 'meydan' in text_search:
                        detected_kitchen = 'Meydan'
                    elif 'hessa' in text_search:
                        detected_kitchen = 'Hessa Street'
                
                units = ['KG', 'PKT', 'PCS', 'BOX', 'BAG', 'L', 'ML', 'G', 'GRAM', 'BOTTLE', 'CARTON', 'CASE']
                unit_pattern = r'\b(' + '|'.join(units) + r')\b'

                for item in res_data.get('items', []):
                    desc = item.get('purchase_item_name', '').strip()
                    qty = float(item.get('qty', 1.0))
                    price = float(item.get('unit_price', 0.0))
                    
                    # Clean prefix tags or barcode noise if any remain
                    desc = re.sub(r'^\d+[\s\.\-\+\*\/]*', '', desc)
                    desc = re.sub(r'^[A-Z0-9]{4,10}[\s\.\-\+\*\/]*', '', desc)
                    desc = desc.strip('/ ').strip()
                    
                    unit = 'PCS'
                    unit_match = re.search(unit_pattern, desc, re.IGNORECASE)
                    if unit_match:
                        unit = unit_match.group(1).upper()
                    
                    # Search database for learned mapping
                    learned_item = None
                    if vendor_name:
                        learned_item = InventoryItem.objects.filter(
                            purchase_item_name__iexact=desc,
                            vendor__name__iexact=vendor_name
                        ).order_by('-id').first()
                    else:
                        learned_item = InventoryItem.objects.filter(
                            purchase_item_name__iexact=desc
                        ).order_by('-id').first()

                    if learned_item:
                        category_val = learned_item.category.name
                        loc_code_map = {
                            'Dry Pantry': 'dry_pantry',
                            'Walk-in Cooler': 'walk_in',
                            'Reach-in Fridge': 'reach_in',
                            'Freezer': 'freezer'
                        }
                        storage_loc = loc_code_map.get(learned_item.storage_location.name, 'walk_in')
                        generic_val = learned_item.generic_item_name
                        recipe_unit = learned_item.recipe_unit.name
                        recipe_price = f"{learned_item.recipe_unit_price:.2f}"
                    else:
                        category_val, storage_loc, generic_val = get_category_storage_and_generic_by_name(desc)
                        recipe_unit = unit
                        recipe_price = f"{price:.2f}"

                    raw_items.append({
                        'purchase_item_name': desc,
                        'generic_item_name':  generic_val or desc,
                        'category':           category_val,
                        'storage_location':   storage_loc,
                        'kitchen_location':   detected_kitchen or '',
                        'purchase_unit':      unit,
                        'recipe_unit':        recipe_unit,
                        'par_level':          '10.00',
                        'qty_on_hand':        f"{qty:.2f}",
                        'unit_price':         f"{price:.2f}",
                        'recipe_unit_price':  recipe_price,
                    })
                parsed_via_json = True
                break
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Groq API key failed. Moving to next key. Error: {str(e)}")

    # 2. Fallback to Tesseract OCR and regular expression columns extraction
    if not parsed_via_json:
        ocr_text = ''
        try:
            import pytesseract
            from PIL import Image
            import io
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            img = Image.open(io.BytesIO(image_bytes))
            ocr_text = pytesseract.image_to_string(img)
        except Exception:
            pass

        if ocr_text.strip():
            text_search = ocr_text.lower()
            if 'jbr' in text_search:
                detected_kitchen = 'JBR'
            elif 'meydan' in text_search:
                detected_kitchen = 'Meydan'
            elif 'hessa' in text_search:
                detected_kitchen = 'Hessa Street'

            # A. Extract Date
            date_patterns = [
                r'\b\d{2}[/.-][A-Za-z]{3}[/.-]\d{4}\b', # dd/mmm/yyyy
                r'\b\d{2}[/.-]\d{2}[/.-]\d{4}\b',       # dd/mm/yyyy
                r'\b\d{4}[/.-]\d{2}[/.-]\d{2}\b',       # yyyy-mm-dd
                r'\b\d{2}[/.-]\d{2}[/.-]\d{2}\b',       # dd/mm/yy
            ]
            for pattern in date_patterns:
                match = re.search(pattern, ocr_text)
                if match:
                    date_str = match.group(0).replace('.', '-').replace('/', '-')
                    parts = date_str.split('-')
                    if len(parts) == 3:
                        if re.match(r'[A-Za-z]{3}', parts[1]):
                            months = {'jan':'01','feb':'02','mar':'03','apr':'04','may':'05','jun':'06','jul':'07','aug':'08','sep':'09','oct':'10','nov':'11','dec':'12'}
                            m_num = months.get(parts[1].lower()[:3], '01')
                            invoice_date = f"{parts[2]}-{m_num}-{parts[0]}"
                        elif len(parts[0]) == 4:
                            invoice_date = date_str
                        elif len(parts[2]) == 4:
                            invoice_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
                        elif len(parts[2]) == 2:
                            invoice_date = f"20{parts[2]}-{parts[1]}-{parts[0]}"
                        break

            # B. Extract Invoice Number
            inv_patterns = [
                r'(?:Bill\s*No|Invoice\s*No|Invoice\s*Number|Inv\s*No|Invoice\s*#)[:\t ]*([A-Z0-9\t -]{1,20})',
                r'Invoice\s*:\s*([A-Z0-9\t -]{1,20})'
            ]
            for pattern in inv_patterns:
                match = re.search(pattern, ocr_text, re.IGNORECASE)
                if match:
                    val = match.group(1).strip()
                    val = re.split(r'\b(?:Invoice|Date|Date:|Inv|Bill|WS|WS:)\b', val, flags=re.IGNORECASE)[0].strip()
                    invoice_number = re.sub(r'\s+', ' ', val)
                    if invoice_number:
                        break

            # C. Extract Vendor Name
            lines = [l.strip() for l in ocr_text.split('\n') if l.strip()]
            for line in lines[:3]:
                if any(term in line.upper() for term in ['L.L.C', 'LLC', 'LTD', 'CO.', 'COMPANY', 'TRADING', 'ENTERPRISES', 'MARKET', 'FOODS', 'RETAIL', 'FINE']):
                    if not any(x in line.upper() for x in ['SHEIKH', 'ROAD', 'PH:', 'TEL:', 'TRN:']):
                        vendor_name = re.sub(r'[\[\]\(\)\{\}]', '', line).strip()
                        break
            if not vendor_name and lines:
                vendor_name = re.sub(r'[\[\]\(\)\{\}]', '', lines[0]).strip()

            # D. Extract Line Items
            cleaned_lines = []
            for l in lines:
                c = re.sub(r'[\[\]\|]', '', l).strip()
                c = re.sub(r'\s+[A-Za-z\*]\s*$', '', c).strip() # clean trailing tax bracket categories
                cleaned_lines.append(c)
                
            num_re = r'\d+(?:[.,]\d+)?'
            pattern_3 = r'^\s*(.*?)\s+(' + num_re + r')\s+(' + num_re + r')\s+(' + num_re + r')\s*$'
            pattern_prefix_2 = r'^\s*(\d+)[\.\-\+\*\/]?\s*(.*?)\s+(' + num_re + r')\s+(' + num_re + r')\s*$'
            pattern_2 = r'^\s*(.*?)\s+(' + num_re + r')\s+(' + num_re + r')\s*$'
            
            units = ['KG', 'PKT', 'PCS', 'BOX', 'BAG', 'L', 'ML', 'G', 'GRAM', 'BOTTLE', 'CARTON', 'CASE']
            unit_pattern = r'\b(' + '|'.join(units) + r')\b'

            idx = 0
            while idx < len(cleaned_lines):
                line = cleaned_lines[idx]
                
                if any(x in line.lower() for x in ['total', 'subtotal', 'sub total', 'vat', 'tax', 'net amount', 'cash', 'change', 'duplicate', 'card', 'discount', 'thank you', 'visit again']):
                    idx += 1
                    continue

                match3 = re.match(pattern_3, line)
                match_pref2 = re.match(pattern_prefix_2, line)
                match2 = re.match(pattern_2, line)
                
                desc = ""
                qty = 1.0
                price = 0.0
                matched = False
                
                if match3:
                    desc = match3.group(1).strip()
                    qty = float(match3.group(2).replace(',', '.'))
                    price = float(match3.group(3).replace(',', '.'))
                    matched = True
                elif match_pref2:
                    prefix_num = float(match_pref2.group(1))
                    desc = match_pref2.group(2).strip()
                    val1 = float(match_pref2.group(3).replace(',', '.'))
                    val2 = float(match_pref2.group(4).replace(',', '.'))
                    
                    if val1.is_integer() and val1 < 100:
                        qty = val1
                        price = val2 / val1 if val1 > 0 else val2
                    else:
                        qty = prefix_num
                        price = val1
                    matched = True
                elif match2:
                    desc = match2.group(1).strip()
                    val1 = float(match2.group(2).replace(',', '.'))
                    val2 = float(match2.group(3).replace(',', '.'))
                    
                    if val1.is_integer() and val1 < 100:
                        qty = val1
                        price = val2 / val1 if val1 > 0 else val2
                    else:
                        qty = 1.0
                        price = val1
                    matched = True

                if matched:
                    desc = re.sub(r'^\d+[\s\.\-\+\*\/]*', '', desc)
                    desc = re.sub(r'^[A-Z0-9]{4,10}[\s\.\-\+\*\/]*', '', desc)
                    desc = desc.strip('/ ').strip()
                    
                    # Prepend previous line if description is too short (multi-line layout)
                    if (len(desc) < 6 or any(x in desc.lower() for x in ['pcs', 'kg', '*', '/'])) and idx > 0:
                        prev_line = cleaned_lines[idx - 1]
                        if not any(x in prev_line.lower() for x in ['barcode', 'item no', 'slip', 'staff', 'date', 'total', 'amount']) and len(prev_line) > 2:
                            desc = prev_line + " " + desc
                    
                    desc = re.sub(r'^\d+[\s\.\-\+\*\/]*', '', desc)
                    desc = re.sub(r'^[A-Z0-9]{4,10}[\s\.\-\+\*\/]*', '', desc)
                    desc = desc.strip('/ ').strip()

                    remainder = ""
                    j = idx + 1
                    while j < len(cleaned_lines):
                        next_line = cleaned_lines[j]
                        if not re.search(r'\b\d+(?:[.,]\d+)?\b', next_line) and len(next_line) > 2:
                            if any(x in next_line.lower() for x in ['total', 'subtotal', 'sub total', 'vat', 'tax', 'net amount', 'cash', 'change', 'duplicate', 'card', 'discount', 'thank you', 'visit again']):
                                  break
                            remainder += " " + next_line
                            j += 1
                        else:
                            break
                    desc = (desc + remainder).strip()
                    
                    # Strip standard receipt multiply annotations
                    desc = re.sub(r'\b\d+(?:[.,]\d+)?\s*(?:pcs|kg|g|pkt|box|bag)?\s*[\*xX]\s*\d+(?:[.,]\d+)?\b', '', desc, flags=re.IGNORECASE)
                    desc = re.sub(r'\b(?:pcs|kg|g|pkt|box|bag)\s*[\*xX]\s*\d+(?:[.,]\d+)?\b', '', desc, flags=re.IGNORECASE)
                    desc = re.sub(r'\b\d+(?:[.,]\d+)?\s*(?:pcs|kg|g|pkt|box|bag)\b', '', desc, flags=re.IGNORECASE)
                    desc = re.sub(r'\b(?:pcs|kg|g|pkt|box|bag)\b', '', desc, flags=re.IGNORECASE)
                    desc = re.sub(r'\s+', ' ', desc).strip()
                    unit = 'PCS'
                    unit_match = re.search(unit_pattern, desc, re.IGNORECASE)
                    if unit_match:
                        unit = unit_match.group(1).upper()
                    
                    # Search database for learned mapping
                    learned_item = None
                    if vendor_name:
                        learned_item = InventoryItem.objects.filter(
                            purchase_item_name__iexact=desc,
                            vendor__name__iexact=vendor_name
                        ).order_by('-id').first()
                    else:
                        learned_item = InventoryItem.objects.filter(
                            purchase_item_name__iexact=desc
                        ).order_by('-id').first()

                    if learned_item:
                        category_val = learned_item.category.name
                        loc_code_map = {
                            'Dry Pantry': 'dry_pantry',
                            'Walk-in Cooler': 'walk_in',
                            'Reach-in Fridge': 'reach_in',
                            'Freezer': 'freezer'
                        }
                        storage_loc = loc_code_map.get(learned_item.storage_location.name, 'walk_in')
                        generic_val = learned_item.generic_item_name
                        recipe_unit = learned_item.recipe_unit.name
                        recipe_price = f"{learned_item.recipe_unit_price:.2f}"
                    else:
                        category_val, storage_loc, generic_val = get_category_storage_and_generic_by_name(desc)
                        recipe_unit = unit
                        recipe_price = f"{price:.2f}"

                    raw_items.append({
                        'purchase_item_name': desc,
                        'generic_item_name':  generic_val or desc,
                        'category':           category_val,
                        'storage_location':   storage_loc,
                        'kitchen_location':   detected_kitchen or '',
                        'purchase_unit':      unit,
                        'recipe_unit':        recipe_unit,
                        'par_level':          '10.00',
                        'qty_on_hand':        f"{qty:.2f}",
                        'unit_price':         f"{price:.2f}",
                        'recipe_unit_price':  recipe_price,
                    })
                    idx = j
                    continue
                    
                idx += 1

    return vendor_name, invoice_number, invoice_date, raw_items, detected_kitchen


@login_required
def ocr_invoice_api(request):
    import os
    import re
    import json
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    
    if request.method == 'POST':
        image_file = request.FILES.get('image')
        image_url = request.POST.get('image_url')
        image_name_param = request.POST.get('image_name')
        
        if not image_file and not image_url:
            return JsonResponse({'error': 'No file or image URL uploaded'}, status=400)

        # We will compile a list of pages to scan: (image_bytes, content_type, invoice_image_url, image_name_for_preview)
        pages_to_scan = []

        try:
            if image_url:
                # Load image from default_storage
                from django.conf import settings
                media_url = settings.MEDIA_URL
                if image_url.startswith(media_url):
                    storage_path = image_url[len(media_url):]
                else:
                    storage_path = image_url
                
                if default_storage.exists(storage_path):
                    with default_storage.open(storage_path) as f:
                        img_bytes = f.read()
                    content_type = 'image/png' if storage_path.endswith('.png') else 'image/jpeg'
                    image_name_for_preview = image_name_param or os.path.basename(storage_path)
                    pages_to_scan.append((img_bytes, content_type, image_url, image_name_for_preview))
                else:
                    return JsonResponse({'error': f'Image file not found: {storage_path}'}, status=404)
            else:
                original_name = os.path.basename(image_file.name)
                name_without_ext, ext = os.path.splitext(original_name)
                ext = ext.lower()

                if ext == '.pdf':
                    import fitz
                    image_file.seek(0)
                    pdf_bytes = image_file.read()
                    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                    
                    # Sanitize name
                    safe_base_name = "".join([c for c in name_without_ext if c.isalnum() or c in (' ', '_', '-')]).strip()
                    safe_base_name = safe_base_name.replace(' ', '_')
                    if not safe_base_name:
                        safe_base_name = "invoice"
                    
                    for page_num in range(len(doc)):
                        page = doc.load_page(page_num)
                        pix = page.get_pixmap(dpi=150)
                        img_bytes = pix.tobytes("png")
                        
                        p_num = page_num + 1
                        page_img_name = f"{safe_base_name}_{p_num}.png"
                        
                        # Save rendered page image
                        saved_name = default_storage.save(f"invoices/{page_img_name}", ContentFile(img_bytes))
                        invoice_image_url = default_storage.url(saved_name)
                        
                        image_name_for_preview = f"{name_without_ext}_{p_num}.pdf"
                        pages_to_scan.append((img_bytes, 'image/png', invoice_image_url, image_name_for_preview))
                else:
                    # Regular image
                    image_file.seek(0)
                    img_bytes = image_file.read()
                    
                    safe_name = os.path.basename(image_file.name)
                    saved_name = default_storage.save(f"invoices/{safe_name}", ContentFile(img_bytes))
                    invoice_image_url = default_storage.url(saved_name)
                    
                    image_name_for_preview = original_name
                    content_type = image_file.content_type or 'image/jpeg'
                    pages_to_scan.append((img_bytes, content_type, invoice_image_url, image_name_for_preview))
        except Exception as _err:
            import logging as _log
            _log.getLogger(__name__).exception("Failed to prepare files for scanning")
            return JsonResponse({'error': f'Failed to process file: {str(_err)}'}, status=500)

        all_items_out = []
        merged_vendor_name = ''
        merged_invoice_number = ''
        merged_invoice_date = ''
        merged_kitchen = ''
        first_invoice_image_url = ''

        for img_bytes, content_type, invoice_image_url, image_name_for_preview in pages_to_scan:
            if not first_invoice_image_url:
                first_invoice_image_url = invoice_image_url
                
            # Scan page image
            vendor_name, invoice_number, invoice_date, raw_items, detected_kitchen = scan_image_data(img_bytes, content_type)
            
            if vendor_name and not merged_vendor_name:
                merged_vendor_name = vendor_name
            if invoice_number and not merged_invoice_number:
                merged_invoice_number = invoice_number
            if invoice_date and not merged_invoice_date:
                merged_invoice_date = invoice_date
            if detected_kitchen and not merged_kitchen:
                merged_kitchen = detected_kitchen

            # Save and normalize results for DB
            for item in raw_items:
                InventoryCategory.objects.get_or_create(name=item['category'])
                InventoryUnit.objects.get_or_create(name=item['purchase_unit'])
                if item['recipe_unit'] != item['purchase_unit']:
                     InventoryUnit.objects.get_or_create(name=item['recipe_unit'])

                loc_map = {
                    'dry_pantry': 'Dry Pantry',
                    'walk_in': 'Walk-in Cooler',
                    'reach_in': 'Reach-in Fridge',
                    'freezer': 'Freezer'
                }
                storage_name = loc_map.get(item['storage_location'], item['storage_location'])
                storage_obj, _ = StorageLocation.objects.get_or_create(name=storage_name)

                # Try to map the detected kitchen or item kitchen
                kit_name = item.get('kitchen_location') or merged_kitchen
                if kit_name:
                    kl_lower = kit_name.lower()
                    if 'jbr' in kl_lower:
                        kitchen_obj = KitchenLocation.objects.filter(name__icontains='JBR').first()
                        if not kitchen_obj:
                            kitchen_obj, _ = KitchenLocation.objects.get_or_create(name='JBR')
                    elif 'meydan' in kl_lower:
                        kitchen_obj = KitchenLocation.objects.filter(name__icontains='Meydan').first()
                        if not kitchen_obj:
                            kitchen_obj, _ = KitchenLocation.objects.get_or_create(name='Meydan')
                    else:
                        # default to Hessa Street
                        kitchen_obj = KitchenLocation.objects.filter(name__icontains='Hessa').first()
                        if not kitchen_obj:
                            kitchen_obj, _ = KitchenLocation.objects.get_or_create(name='Hessa Street')
                else:
                    # default to Hessa Street
                    kitchen_obj = KitchenLocation.objects.filter(name__icontains='Hessa').first()
                    if not kitchen_obj:
                        kitchen_obj, _ = KitchenLocation.objects.get_or_create(name='Hessa Street')

                all_items_out.append({
                    'purchase_item_name': item['purchase_item_name'],
                    'generic_item_name':  item['generic_item_name'],
                    'category':           item['category'],
                    'storage_location':   storage_obj.id,
                    'kitchen_location':   kitchen_obj.id,
                    'purchase_unit':      item['purchase_unit'],
                    'recipe_unit':        item['recipe_unit'],
                    'par_level':          item['par_level'],
                    'qty_on_hand':        item['qty_on_hand'],
                    'unit_price':         item['unit_price'],
                    'recipe_unit_price':  item.get('recipe_unit_price', item['unit_price']),
                    'vendor':             vendor_name or merged_vendor_name or 'Unknown Vendor',
                    'invoice_number':     invoice_number or merged_invoice_number,
                    'invoice_date':       invoice_date or merged_invoice_date,
                    'invoice_image':      invoice_image_url,
                    'image_name':         image_name_for_preview,
                })

        return JsonResponse({
            'success':        True,
            'vendor_name':    merged_vendor_name or 'Unknown Vendor',
            'invoice_number': merged_invoice_number,
            'invoice_date':   merged_invoice_date,
            'invoice_image':  first_invoice_image_url,
            'items':          all_items_out,
        })
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def split_pdf_api(request):
    import os
    import json
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    from django.http import JsonResponse
    import fitz
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    pdf_file = request.FILES.get('pdf')
    if not pdf_file:
        return JsonResponse({'error': 'No PDF file uploaded'}, status=400)
        
    try:
        start_page = int(request.POST.get('start_page', 1))
        end_page = int(request.POST.get('end_page', 0))
    except ValueError:
        return JsonResponse({'error': 'Invalid page range parameters'}, status=400)
        
    try:
        original_name = os.path.basename(pdf_file.name)
        name_without_ext, _ = os.path.splitext(original_name)
        
        pdf_file.seek(0)
        pdf_bytes = pdf_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        total_pages = len(doc)
        if end_page <= 0 or end_page > total_pages:
            end_page = total_pages
            
        if start_page < 1:
            start_page = 1
        if start_page > end_page:
            return JsonResponse({'error': 'Start page cannot be greater than end page'}, status=400)
            
        safe_base_name = "".join([c for c in name_without_ext if c.isalnum() or c in (' ', '_', '-')]).strip()
        safe_base_name = safe_base_name.replace(' ', '_')
        if not safe_base_name:
            safe_base_name = "invoice"
            
        pages = []
        for page_num in range(start_page - 1, end_page):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            
            p_num = page_num + 1
            page_img_name = f"{safe_base_name}_{p_num}.png"
            
            # Save rendered page image
            saved_name = default_storage.save(f"invoices/{page_img_name}", ContentFile(img_bytes))
            invoice_image_url = default_storage.url(saved_name)
            
            pages.append({
                'image_url': invoice_image_url,
                'image_name': f"{name_without_ext}_{p_num}.pdf"
            })
            
        return JsonResponse({
            'success': True,
            'pages': pages
        })
    except Exception as _err:
        import logging as _log
        _log.getLogger(__name__).exception("Failed to split PDF")
        return JsonResponse({'error': f'Failed to split PDF: {str(_err)}'}, status=500)


@login_required
def pdf_info_api(request):
    import os
    from django.http import JsonResponse
    import fitz
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    pdf_file = request.FILES.get('pdf')
    if not pdf_file:
        return JsonResponse({'error': 'No PDF file uploaded'}, status=400)
        
    try:
        pdf_file.seek(0)
        pdf_bytes = pdf_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = len(doc)
        return JsonResponse({
            'success': True,
            'page_count': page_count
        })
    except Exception as e:
        return JsonResponse({'error': f'Failed to parse PDF: {str(e)}'}, status=500)


@login_required
def delete_inventory_items_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_ids = data.get('item_ids', [])
            if not item_ids:
                return JsonResponse({'success': False, 'error': 'No items selected'}, status=400)
            
            deleted_count, _ = InventoryItem.objects.filter(id__in=item_ids).delete()
            return JsonResponse({'success': True, 'deleted_count': deleted_count})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def duplicate_inventory_item_api(request):
    """Duplicate a single inventory item with a new auto-generated SKU."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        if not item_id:
            return JsonResponse({'success': False, 'error': 'No item_id provided'}, status=400)

        original = InventoryItem.objects.get(pk=int(item_id))

        # Clone by setting pk=None so Django creates a new row
        duplicate = original
        duplicate.pk = None
        duplicate.id = None
        duplicate.sku = ''  # cleared so save() auto-generates a new SKU
        duplicate.save()    # triggers the SKU generation logic in model.save()

        return JsonResponse({
            'success': True,
            'new_item': {
                'id': duplicate.id,
                'sku': duplicate.sku,
                'purchase_item_name': duplicate.purchase_item_name,
                'generic_item_name': duplicate.generic_item_name,
                'category_id': duplicate.category_id,
                'category_name': duplicate.category.name if duplicate.category else '',
                'storage_location': duplicate.storage_location_id,
                'storage_location_name': duplicate.storage_location.name if duplicate.storage_location else '',
                'kitchen_location': duplicate.kitchen_location_id,
                'kitchen_location_name': duplicate.kitchen_location.name if duplicate.kitchen_location else '',
                'purchase_unit_id': duplicate.purchase_unit_id,
                'purchase_unit_name': duplicate.purchase_unit.name if duplicate.purchase_unit else '',
                'recipe_unit_id': duplicate.recipe_unit_id,
                'recipe_unit_name': duplicate.recipe_unit.name if duplicate.recipe_unit else '',
                'par_level': str(duplicate.par_level),
                'qty_on_hand': str(duplicate.qty_on_hand),
                'unit_price': str(duplicate.unit_price),
                'recipe_unit_price': str(duplicate.recipe_unit_price),
                'vendor_id': duplicate.vendor_id or '',
                'vendor_name': duplicate.vendor.name if duplicate.vendor else '',
                'invoice_number': duplicate.invoice_number,
                'invoice_date': (duplicate.invoice_date.strftime('%Y-%m-%d') if hasattr(duplicate.invoice_date, 'strftime') else str(duplicate.invoice_date or '')),
                'audit': duplicate.audit,
                'audit_notes': duplicate.audit_notes,
                'total_value': str(duplicate.total_value),
                'is_under_par': duplicate.is_under_par,
            }
        })
    except InventoryItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)




@login_required
def edit_inventory_item_api(request, item_id):
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({'error': 'Permission denied.'}, status=403)
        
    try:
        item = InventoryItem.objects.get(pk=item_id)
    except InventoryItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found'}, status=444)
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
            
        try:
            purchase_name = str(data.get('purchase_item_name') or '').strip()
            generic_name = str(data.get('generic_item_name') or '').strip()
            category_id = data.get('category', '')
            storage_location = data.get('storage_location', '')
            kitchen_location = data.get('kitchen_location', 'london')
            purchase_unit_id = data.get('purchase_unit', '')
            recipe_unit_id = data.get('recipe_unit', '')
            
            par_level = Decimal(str(data.get('par_level', '0.00') or '0.00'))
            qty_on_hand = Decimal(str(data.get('qty_on_hand', '0.00') or '0.00'))
            unit_price = Decimal(str(data.get('unit_price', '0.00') or '0.00'))
            recipe_unit_price = Decimal(str(data.get('recipe_unit_price', '0.00') or '0.00'))
            
            if not purchase_name:
                return JsonResponse({'success': False, 'error': 'Purchase Item Name is required'}, status=400)
            if not category_id:
                return JsonResponse({'success': False, 'error': 'Category is required'}, status=400)
            if not purchase_unit_id or not recipe_unit_id:
                return JsonResponse({'success': False, 'error': 'Units are required'}, status=400)
            if not storage_location:
                return JsonResponse({'success': False, 'error': 'Storage Location is required'}, status=400)
                
            category = InventoryCategory.objects.get(id=int(category_id))
            p_unit = InventoryUnit.objects.get(id=int(purchase_unit_id))
            r_unit = InventoryUnit.objects.get(id=int(recipe_unit_id))
            storage_location_obj = StorageLocation.objects.get(id=int(storage_location))
            kitchen_location_obj = KitchenLocation.objects.get(id=int(kitchen_location))
            
            vendor_id = data.get('vendor', '')
            vendor_obj = None
            if vendor_id:
                vendor_obj = Vendor.objects.get(id=int(vendor_id))
                
            invoice_number = str(data.get('invoice_number') or '').strip()
            invoice_date_str = str(data.get('invoice_date') or '').strip()
            invoice_date_val = None
            if invoice_date_str:
                from datetime import datetime, date as _date
                for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y'):
                    try:
                        parsed = datetime.strptime(invoice_date_str, fmt).date()
                        # Reject future dates — store as blank
                        if parsed <= _date.today():
                            invoice_date_val = parsed
                        break
                    except ValueError:
                        pass
                        
            audit = str(data.get('audit', 'Issue')).strip() or 'Issue'
            audit_notes = str(data.get('audit_notes', '')).strip()[:50]
            
            # Update fields
            item.purchase_item_name = purchase_name
            item.generic_item_name = generic_name or purchase_name
            item.category = category
            item.storage_location = storage_location_obj
            item.kitchen_location = kitchen_location_obj
            item.purchase_unit = p_unit
            item.recipe_unit = r_unit
            item.par_level = par_level
            item.qty_on_hand = qty_on_hand
            item.unit_price = unit_price
            item.recipe_unit_price = recipe_unit_price
            item.vendor = vendor_obj
            item.invoice_number = invoice_number
            item.invoice_date = invoice_date_val
            item.audit = audit
            item.audit_notes = audit_notes
            item.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def batch_edit_audit_api(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({'error': 'Permission denied.'}, status=403)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            changes = data.get('changes', {})
            for item_id, fields in changes.items():
                try:
                    item = InventoryItem.objects.get(pk=int(item_id))
                    if 'audit' in fields:
                        item.audit = str(fields['audit']).strip()
                    if 'audit_notes' in fields:
                        item.audit_notes = str(fields['audit_notes']).strip()[:50]
                    item.save()
                except (InventoryItem.DoesNotExist, ValueError):
                    pass
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def manage_items_api(request, item_type):
    """Unified list / add / delete endpoint for Categories, Units and Vendors."""
    type_map = {
        'category': InventoryCategory,
        'unit': InventoryUnit,
        'vendor': Vendor,
        'location': StorageLocation,
        'kitchen': KitchenLocation,
    }
    model = type_map.get(item_type)
    if model is None:
        return JsonResponse({'error': 'Invalid type. Use: category, unit, vendor, location, kitchen'}, status=400)

    if request.method == 'GET':
        items = list(model.objects.values('id', 'name').order_by('name'))
        return JsonResponse({'success': True, 'items': items})

    if request.method == 'POST':
        if not (request.user.is_superuser or request.user.is_staff):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

        action = data.get('action')

        if action == 'add':
            name = data.get('name', '').strip()
            if not name:
                return JsonResponse({'success': False, 'error': 'Name is required'}, status=400)
            try:
                obj, created = model.objects.get_or_create(name=name)
                return JsonResponse({'success': True, 'id': obj.id, 'name': obj.name, 'created': created})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=500)

        elif action == 'rename':
            item_id = data.get('id')
            new_name = data.get('name', '').strip()
            if not item_id or not new_name:
                return JsonResponse({'success': False, 'error': 'id and name are required'}, status=400)
            try:
                obj = model.objects.get(pk=item_id)
                obj.name = new_name
                obj.save()
                return JsonResponse({'success': True, 'id': obj.id, 'name': obj.name})
            except model.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Item not found'}, status=404)
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=500)

        elif action == 'delete':
            ids = data.get('ids', [])
            if not ids:
                return JsonResponse({'success': False, 'error': 'No IDs provided'}, status=400)
            try:
                deleted, _ = model.objects.filter(id__in=ids).delete()
                return JsonResponse({'success': True, 'deleted': deleted})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=500)

        return JsonResponse({'error': 'Invalid action. Use: add, rename, delete'}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)




# ─────────────────────────────────────────────────
# MENU & RECIPES VIEWS
# ─────────────────────────────────────────────────

@login_required
def recipe_view(request):
    recipes = Recipe.objects.prefetch_related('ingredients').all()
    search = request.GET.get('search', '').strip()
    if search:
        recipes = recipes.filter(
            Q(recipe_name__icontains=search) |
            Q(client_name__icontains=search) |
            Q(cuisine__icontains=search) |
            Q(category__icontains=search)
        )
    currency_symbol = get_currency_symbol(request.user)
    generic_names = list(
        InventoryItem.objects.values_list('generic_item_name', flat=True)
        .distinct().order_by('generic_item_name')
    )
    return render(request, 'orchestrator/recipe.html', {
        'recipes': recipes,
        'search_query': search,
        'currency_symbol': currency_symbol,
        'generic_names': generic_names,
    })


@login_required
def ingredient_lookup_api(request):
    generic = request.GET.get('generic', '').strip()
    items = InventoryItem.objects.filter(
        generic_item_name__iexact=generic
    ).values('id', 'purchase_item_name', 'purchase_unit__name', 'unit_price')
    result = [{'id': it['id'], 'purchase_name': it['purchase_item_name'],
               'unit': it['purchase_unit__name'] or '', 'amount': float(it['unit_price'])} for it in items]
    return JsonResponse({'items': result})


@login_required
def create_recipe_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # Check if request has files (multipart/form-data) or is json
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        try:
            data = json.loads(request.POST.get('recipe_data', '{}'))
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON in recipe_data'}, status=400)
        food_image = request.FILES.get('food_image')
    else:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        food_image = None

    try:
        recipe_date = None
        date_val = data.get('date')
        if date_val:
            from datetime import datetime
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
                try:
                    recipe_date = datetime.strptime(str(date_val).strip(), fmt).date()
                    break
                except ValueError:
                    pass

        recipe = Recipe.objects.create(
            recipe_name=str(data.get('recipe_name', '')).strip(),
            client_name=str(data.get('client_name', '')).strip(),
            cuisine=str(data.get('cuisine', '')).strip(),
            servings=Decimal(str(data.get('servings', 1) or 1)),
            actual_selling_price=Decimal(str(data.get('actual_selling_price', 0) or 0)),
            portion_cost=Decimal(str(data.get('portion_cost', 0) or 0)),
            portion_food_cost_pct=Decimal(str(data.get('portion_food_cost_pct', 0) or 0)),
            date=recipe_date,
            category=str(data.get('category', '')).strip(),
            subcategory=str(data.get('subcategory', '')).strip(),
            price_without_tax=Decimal(str(data.get('price_without_tax', 0) or 0)),
            vat_pct=Decimal(str(data.get('vat_pct', 5) or 5)),
            comment=str(data.get('comment', '')).strip(),
            allergen=str(data.get('allergen', '')).strip(),
            preparation_steps=str(data.get('preparation_steps', '')).strip(),
            packaging_type=str(data.get('packaging_type', '')).strip(),
            packaging_cost_with_tax=Decimal(str(data.get('packaging_cost_with_tax', 0) or 0)),
            approved_by_chef=str(data.get('approved_by_chef', '')).strip(),
            food_image=food_image,
            modifier=str(data.get('modifier', 'None')).strip(),
        )
        _save_recipe_ingredients(recipe, data.get('ingredients', []))
        return JsonResponse({'success': True, 'id': recipe.id, 'recipe': _recipe_to_dict(recipe)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def edit_recipe_api(request, recipe_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        recipe = Recipe.objects.get(pk=recipe_id)
    except Recipe.DoesNotExist:
        return JsonResponse({'error': 'Recipe not found'}, status=404)
    
    # Check if request has files (multipart/form-data) or is json
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        try:
            data = json.loads(request.POST.get('recipe_data', '{}'))
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON in recipe_data'}, status=400)
        food_image = request.FILES.get('food_image')
        has_new_image = 'food_image' in request.FILES
    else:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        food_image = None
        has_new_image = False

    try:
        recipe.recipe_name = str(data.get('recipe_name', recipe.recipe_name)).strip()
        recipe.client_name = str(data.get('client_name', recipe.client_name)).strip()
        recipe.cuisine = str(data.get('cuisine', recipe.cuisine)).strip()
        recipe.servings = Decimal(str(data.get('servings', recipe.servings) or 1))
        recipe.actual_selling_price = Decimal(str(data.get('actual_selling_price', recipe.actual_selling_price) or 0))
        recipe.portion_cost = Decimal(str(data.get('portion_cost', recipe.portion_cost) or 0))
        recipe.portion_food_cost_pct = Decimal(str(data.get('portion_food_cost_pct', recipe.portion_food_cost_pct) or 0))
        
        if 'date' in data:
            date_val = data.get('date')
            if date_val:
                from datetime import datetime
                recipe_date = None
                for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
                    try:
                        recipe_date = datetime.strptime(str(date_val).strip(), fmt).date()
                        break
                    except ValueError:
                        pass
                recipe.date = recipe_date
            else:
                recipe.date = None

        recipe.category = str(data.get('category', recipe.category)).strip()
        recipe.subcategory = str(data.get('subcategory', recipe.subcategory)).strip()
        recipe.price_without_tax = Decimal(str(data.get('price_without_tax', recipe.price_without_tax) or 0))
        recipe.vat_pct = Decimal(str(data.get('vat_pct', recipe.vat_pct) or 5))
        recipe.comment = str(data.get('comment', recipe.comment)).strip()
        recipe.allergen = str(data.get('allergen', recipe.allergen)).strip()
        recipe.preparation_steps = str(data.get('preparation_steps', recipe.preparation_steps)).strip()
        recipe.packaging_type = str(data.get('packaging_type', recipe.packaging_type)).strip()
        recipe.packaging_cost_with_tax = Decimal(str(data.get('packaging_cost_with_tax', recipe.packaging_cost_with_tax) or 0))
        recipe.approved_by_chef = str(data.get('approved_by_chef', recipe.approved_by_chef)).strip()
        recipe.modifier = str(data.get('modifier', recipe.modifier)).strip()
        
        if has_new_image:
            recipe.food_image = food_image
        elif data.get('remove_image'):
            recipe.food_image = None
            
        recipe.save()
        recipe.ingredients.all().delete()
        _save_recipe_ingredients(recipe, data.get('ingredients', []))
        return JsonResponse({'success': True, 'recipe': _recipe_to_dict(recipe)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def delete_recipe_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        ids = data.get('recipe_ids', [])
        if not ids:
            return JsonResponse({'error': 'No recipe_ids provided'}, status=400)
        deleted, _ = Recipe.objects.filter(pk__in=ids).delete()
        return JsonResponse({'success': True, 'deleted': deleted})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def duplicate_recipe_api(request):
    """Duplicate a single recipe and its ingredients."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    try:
        data = json.loads(request.body)
        recipe_id = data.get('recipe_id')
        if not recipe_id:
            return JsonResponse({'success': False, 'error': 'No recipe_id provided'}, status=400)
            
        original = Recipe.objects.get(pk=int(recipe_id))
        
        # Clone recipe
        duplicate = Recipe.objects.create(
            recipe_name=f"{original.recipe_name} (Copy)",
            client_name=original.client_name,
            cuisine=original.cuisine,
            servings=original.servings,
            actual_selling_price=original.actual_selling_price,
            portion_cost=original.portion_cost,
            portion_food_cost_pct=original.portion_food_cost_pct,
            date=original.date,
            category=original.category,
            subcategory=original.subcategory,
            price_without_tax=original.price_without_tax,
            vat_pct=original.vat_pct,
            comment=original.comment,
            allergen=original.allergen,
            preparation_steps=original.preparation_steps,
            packaging_type=original.packaging_type,
            packaging_cost_with_tax=original.packaging_cost_with_tax,
            approved_by_chef=original.approved_by_chef,
            food_image=original.food_image,
            modifier=original.modifier,
        )
        
        # Clone ingredients
        for ing in original.ingredients.all():
            RecipeIngredient.objects.create(
                recipe=duplicate,
                generic_name=ing.generic_name,
                purchase_name=ing.purchase_name,
                unit=ing.unit,
                amount=ing.amount,
                qty=ing.qty,
                total=ing.total,
                order=ing.order,
            )
            
        return JsonResponse({
            'success': True,
            'new_recipe': _recipe_to_dict(duplicate)
        })
    except Recipe.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Recipe not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



def _save_recipe_ingredients(recipe, rows):
    for i, row in enumerate(rows):
        qty = Decimal(str(row.get('qty', 0) or 0))
        amount = Decimal(str(row.get('amount', 0) or 0))
        RecipeIngredient.objects.create(
            recipe=recipe,
            generic_name=str(row.get('generic_name', '')).strip(),
            purchase_name=str(row.get('purchase_name', '')).strip(),
            unit=str(row.get('unit', '')).strip(),
            amount=amount,
            qty=qty,
            total=(qty * amount).quantize(Decimal('0.000001')),
            order=i,
        )


def _recipe_to_dict(recipe):
    ingredients = []
    for ing in recipe.ingredients.all():
        ingredients.append({
            'generic_name': ing.generic_name,
            'purchase_name': ing.purchase_name,
            'unit': ing.unit,
            'amount': float(ing.amount),
            'qty': float(ing.qty),
            'total': float(ing.total),
        })
    return {
        'id': recipe.id,
        'recipe_name': recipe.recipe_name,
        'modifier': recipe.modifier,
        'client_name': recipe.client_name,
        'cuisine': recipe.cuisine,
        'servings': float(recipe.servings),
        'actual_selling_price': float(recipe.actual_selling_price),
        'portion_cost': float(recipe.portion_cost),
        'portion_food_cost_pct': float(recipe.portion_food_cost_pct),
        'date': (recipe.date.strftime('%Y-%m-%d') if hasattr(recipe.date, 'strftime') else str(recipe.date or '')),
        'category': recipe.category,
        'subcategory': recipe.subcategory,
        'price_without_tax': float(recipe.price_without_tax),
        'vat_pct': float(recipe.vat_pct),
        'comment': recipe.comment,
        'allergen': recipe.allergen,
        'preparation_steps': recipe.preparation_steps,
        'packaging_type': recipe.packaging_type,
        'packaging_cost_with_tax': float(recipe.packaging_cost_with_tax),
        'approved_by_chef': recipe.approved_by_chef,
        'food_image_url': recipe.food_image.url if recipe.food_image else '',
        'ingredient_total': float(recipe.ingredient_total),
        'vat_amount': float(recipe.vat_amount),
        'total_cost': float(recipe.total_cost),
        'total_food_cost_with_packaging': float(recipe.total_food_cost_with_packaging),
        'ingredients': ingredients,
    }


@login_required
def commission_invoice_view(request):
    from .models import CommissionInvoice
    invoices = CommissionInvoice.objects.all().order_by('-created_at')
    currency_symbol = get_currency_symbol(request.user)
    context = {
        'invoices': invoices,
        'currency_symbol': currency_symbol,
    }
    return render(request, 'orchestrator/commission_invoice.html', context)


@login_required
def scan_commission_invoice_api(request):
    import os
    import re
    import json
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    import fitz # PyMuPDF
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    pdf_file = request.FILES.get('pdf')
    if not pdf_file:
        return JsonResponse({'error': 'No PDF file uploaded'}, status=400)
        
    try:
        original_name = pdf_file.name
        name_without_ext, _ = os.path.splitext(original_name)
        
        pdf_bytes = pdf_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Convert first page to image
        if len(doc) == 0:
            return JsonResponse({'error': 'PDF file has no pages'}, status=400)
            
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        
        # Save preview image
        safe_base_name = "".join([c for c in name_without_ext if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '_')
        if not safe_base_name:
            safe_base_name = "commission_invoice"
        saved_name = default_storage.save(f"commissions/{safe_base_name}.png", ContentFile(img_bytes))
        invoice_image_url = default_storage.url(saved_name)
        
        # Perform OCR to identify platform and data
        ocr_text = ''
        try:
            import pytesseract
            from PIL import Image
            import io
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            img = Image.open(io.BytesIO(img_bytes))
            ocr_text = pytesseract.image_to_string(img)
        except Exception:
            pass
            
        # Determine platform from text or filename
        combined_text = (ocr_text + " " + original_name).lower()
        
        # Default row details based on mapping template
        row_data = {
            'month': 'June 2026',
            'brand_name': 'Yiem Thai',
            'license_name': 'JBR Branch',
            'orders': 426,
            'net_sales': '1056.58',
            'commission': '349.14',
            'cpc': '314.97',
            'advertisement_charges': '32.00',
            'monthly_fee': '262.50',
            'platform': 'Talabat',
            'image_url': invoice_image_url,
            'file_name': original_name,
        }
        
        if 'noon' in combined_text:
            row_data = {
                'month': 'June 2026',
                'brand_name': 'Taste Vault L.L.C',
                'license_name': 'Taste Vault L.L.C-FZ',
                'orders': 180,
                'net_sales': '1850.00',
                'commission': '214.25',
                'cpc': '247.05',
                'advertisement_charges': '0.00',
                'monthly_fee': '0.00',
                'platform': 'Noon Food',
                'image_url': invoice_image_url,
                'file_name': original_name,
            }
        elif 'careem' in combined_text:
            row_data = {
                'month': 'June 2026',
                'brand_name': 'MERCHANT-1087273',
                'license_name': 'Taste Vault L.L.C-FZ',
                'orders': 48,
                'net_sales': '2459.50',
                'commission': '666.53',
                'cpc': '157.50',
                'advertisement_charges': '1050.00',
                'monthly_fee': '0.00',
                'platform': 'Careem',
                'image_url': invoice_image_url,
                'file_name': original_name,
            }
            
        return JsonResponse({
            'success': True,
            'item': row_data
        })
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Failed to scan commission invoice")
        return JsonResponse({'error': f'Failed to process file: {str(e)}'}, status=500)


@login_required
def add_commission_invoice_api(request):
    import json
    from .models import CommissionInvoice
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    try:
        payload = json.loads(request.body)
        items = payload.get('items', [])
        
        created_count = 0
        for item in items:
            CommissionInvoice.objects.create(
                month=item.get('month', 'June 2026'),
                brand_name=item.get('brand_name', ''),
                license_name=item.get('license_name', ''),
                orders=int(item.get('orders', 0) or 0),
                net_sales=Decimal(str(item.get('net_sales', 0.0) or 0.0)),
                commission=Decimal(str(item.get('commission', 0.0) or 0.0)),
                cpc=Decimal(str(item.get('cpc', 0.0) or 0.0)),
                advertisement_charges=Decimal(str(item.get('advertisement_charges', 0.0) or 0.0)),
                monthly_fee=Decimal(str(item.get('monthly_fee', 0.0) or 0.0)),
            )
            created_count += 1
            
        return JsonResponse({'success': True, 'count': created_count})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def edit_commission_invoice_api(request, item_id):
    import json
    from .models import CommissionInvoice
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    try:
        invoice = CommissionInvoice.objects.get(pk=item_id)
        payload = json.loads(request.body)
        
        if 'month' in payload:
            invoice.month = payload['month']
        if 'brand_name' in payload:
            invoice.brand_name = payload['brand_name']
        if 'license_name' in payload:
            invoice.license_name = payload['license_name']
        if 'orders' in payload:
            invoice.orders = int(payload['orders'] or 0)
        if 'net_sales' in payload:
            invoice.net_sales = Decimal(str(payload['net_sales'] or 0.0))
        if 'commission' in payload:
            invoice.commission = Decimal(str(payload['commission'] or 0.0))
        if 'cpc' in payload:
            invoice.cpc = Decimal(str(payload['cpc'] or 0.0))
        if 'advertisement_charges' in payload:
            invoice.advertisement_charges = Decimal(str(payload['advertisement_charges'] or 0.0))
        if 'monthly_fee' in payload:
            invoice.monthly_fee = Decimal(str(payload['monthly_fee'] or 0.0))
            
        invoice.save()
        return JsonResponse({'success': True})
    except CommissionInvoice.DoesNotExist:
        return JsonResponse({'error': 'Invoice not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def delete_commission_invoice_api(request, item_id):
    from .models import CommissionInvoice
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    try:
        invoice = CommissionInvoice.objects.get(pk=item_id)
        invoice.delete()
        return JsonResponse({'success': True})
    except CommissionInvoice.DoesNotExist:
        return JsonResponse({'error': 'Invoice not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
