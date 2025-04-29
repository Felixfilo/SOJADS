from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User 
from django.db.models.functions import TruncMonth
from django.db.models import Sum, Count
from Seller.models import Product
from Home.models import Feedback, Order
import json
from django.utils import timezone
from django.db.models import F

def admin_dashbord(request):
    return render(request, 'dash.html')

def  Main (request):
     # User Statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    
    # Sales Statistics
    monthly_sales = Order.objects.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Sum('total_amount')
    ).order_by('month')
    
    # Convert to chart data
    sales_labels = [entry['month'].strftime("%B %Y") for entry in monthly_sales]
    sales_data = [float(entry['total']) for entry in monthly_sales]
    
    # Product Statistics
    top_products = Product.objects.annotate(
        total_orders=Count('order')
    ).order_by('-total_orders')[:5]
    
    # Feedback Analysis
    feedback_stats = Feedback.objects.values('rating').annotate(
        count=Count('id')
    ).order_by('rating')
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'sales_labels': json.dumps(sales_labels),
        'sales_data': json.dumps(sales_data),
        'top_products': top_products,
        'feedback_stats': feedback_stats,
        'total_sales': sum(sales_data),
        'total_products': Product.objects.count()
    }
    
    return render(request, 'main_Admin.html', context)


@login_required
def users(request):
    users = User.objects.all()
    context = {
        'users': users
    }
    return render(request, 'users.html', context)

@login_required
def total_selling(request):
    total_sales = Order.objects.aggregate(total=Sum('total_amount'))
    context = {
        'total_sales': total_sales['total'] or 0
    }
    return render(request, 'admin/total_selling.html', context)

from django.db.models import DecimalField, ExpressionWrapper

@login_required
def top_selling(request):
    products = Product.objects.annotate(
        current_price=ExpressionWrapper(
            F('price') * (1 - F('discount') / 100),
            output_field=DecimalField(max_digits=10, decimal_places=2)
        ),
        profit=ExpressionWrapper(
            F('current_price') * 0.05,
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    ).order_by('-profit')

    # Apply filters
    category = request.GET.get('category')
    alphabet = request.GET.get('alphabet')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')

    if category:
        products = products.filter(category=category)
    if alphabet:
        if alphabet == 'A-M':
            products = products.filter(product_name__regex=r'^[A-Ma-m]')
        elif alphabet == 'N-Z':
            products = products.filter(product_name__regex=r'^[N-Zn-z]')
    if price_min:
        products = products.filter(current_price__gte=float(price_min))
    if price_max:
        products = products.filter(current_price__lte=float(price_max))

    # Apply sorting
    sort = request.GET.get('sort')
    if sort:
        if sort == 'name':
            products = products.order_by('product_name')
        elif sort == 'price':
            products = products.order_by('-price')
        elif sort == 'current_price':
            products = products.order_by('-current_price')

    # Get unique categories for the filter
    categories = Product.objects.values_list('category', flat=True).distinct()

    # Calculate monthly sales data
    monthly_sales = Order.objects.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total_sales=Sum('total_amount')
    ).order_by('month')

    monthly_sales_labels = [sale['month'].strftime('%B %Y') for sale in monthly_sales]
    monthly_sales_data = [float(sale['total_sales']) for sale in monthly_sales]

    context = {
        'products': products,
        'categories': categories,
        'monthly_sales_labels': monthly_sales_labels,
        'monthly_sales_data': monthly_sales_data,
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'product_list_partial.html', context)
    return render(request, 'top_selling.html', context)
@login_required
def suspend_user(request, user_id):
    if request.method == 'POST':
        user = User.objects.get(id=user_id)
        reason = request.POST.get('reason')
        suspension_days = int(request.POST.get('duration', 1))
        end_date = timezone.now() + timezone.timedelta(days=suspension_days)
        
        UserSuspension.objects.create(
            user=user,
            reason=reason,
            end_date=end_date
        )
        
        user.is_active = False
        user.save()
        return redirect('admin_users')
    
    user = User.objects.get(id=user_id)
    return render(request, 'admin/suspend_user.html', {'user': user})

@login_required
def activate_user(request, user_id):
    if request.method == 'POST':
        user = User.objects.get(id=user_id)
        user.is_active = True
        user.save()
        UserSuspension.objects.filter(user=user, end_date__gt=timezone.now()).update(end_date=timezone.now())
    return redirect('admin_users')

@login_required
def total_sales(request):
     # Daily sales summary
    daily_sales = Order.objects.values('created_at__date').annotate(
        daily_total=Sum('total_amount')
    ).order_by('-created_at__date')

    # Top salespeople
    top_salespeople = User.objects.annotate(
        total_sales=Sum('order__total_amount')
    ).order_by('-total_sales')[:10]

    # Individual sales calculation using available fields
    individual_sales = Order.objects.select_related('user').order_by('-created_at')[:100]

    # Monthly sales for the bar graph
    current_year = timezone.now().year
    monthly_sales = Order.objects.filter(created_at__year=current_year).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Sum('total_amount')
    ).order_by('month')

    monthly_sales_labels = [sale['month'].strftime('%B') for sale in monthly_sales]
    monthly_sales_data = [float(sale['total']) for sale in monthly_sales]

    context = {
        'daily_sales': daily_sales,
        'top_salespeople': top_salespeople,
        'individual_sales': individual_sales,
        'monthly_sales_labels': monthly_sales_labels,
        'monthly_sales_data': monthly_sales_data,
    }
    return render(request, 'total_sales.html', context)

@login_required
def feedback_management(request):
    feedbacks = Feedback.objects.all().order_by('-created_at')
    context = {
        'feedbacks': feedbacks
    }
    return render(request, 'feedback_management.html', context)

@login_required
def delete_feedback(request, feedback_id):
    feedback = Feedback.objects.get(id=feedback_id)
    feedback.delete()
    return redirect('feedback_management')

@login_required
def mark_reviewed(request, feedback_id):
    if request.method == 'POST':
        feedback = Feedback.objects.get(id=feedback_id)
        feedback.reviewed = True
        feedback.save()
    return redirect('feedback_management')
