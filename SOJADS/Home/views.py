from . import views
from django.shortcuts import render , redirect, get_object_or_404 
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseServerError
from django.contrib.auth.decorators import login_required
import logging , json
from Seller.models import Product
from login_app.models import UserForm
from Home.models import CartItem, Cart , Category, Feedback, Order,  OrderItem
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import F, ExpressionWrapper, DecimalField
from django.db.models import Q
from django.core.paginator import Paginator
from .mpesa import lipa_na_mpesa_online
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# Set up logging
logger = logging.getLogger(__name__)


# Create your views here.

def dashbord(request):
    return render(request, 'main.html')

def home(request):
    flash_sale_products = Product.objects.filter(discount__gt=0)
    for product in flash_sale_products:
        product.discounted_price = product.price * (1 - product.discount / 100)  # Calculate the discounted price

    best_selling_products = Product.objects.order_by('-sales_count')[:4]  # Get top 4 best sellers
    
    return render(request, 'Home.html', {
        'products': flash_sale_products,
        'best_selling_products': best_selling_products,  # Pass best-selling products to the template
    })

def logout(request):
    return redirect('login_app:login_user')
    
def category_list(request):
    categories = Product.objects.values_list('category', flat=True).distinct()
    context = {
        'categories': categories
    }
    return render(request, 'category.html', context)

def category(request, category_name):
    # Fetch the products for the given category
    products = Product.objects.filter(category=category_name)

    # Render the product list with context
    context = {
        'products': products,
        'category_name': category_name,
    }
    # Render a separate product template
    return render(request, 'product_list.html', context)

def deals(request):
    # Fetch deal products with discounts above 10%
    deal_products = Product.objects.filter(discount__gt=10)
    
    # Calculate discounted price for each deal product
    for product in deal_products:
        product.discounted_price = product.price * (1 - product.discount / 100)
    
    return render(request, 'deals.html', {
        'deal_products': deal_products  # Pass deal products to the template
    })
    

def flash_sales(request):
    # Fetch top 10 products with highest discounts for flash sales
    products = Product.objects.filter(discount__gt=0).annotate(
        sale_price=ExpressionWrapper(
            F('original_price') * (1 - F('discount') / 100),
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    ).order_by('-discount')[:10]  # Order by highest discount and limit to top 10

    context = {
        'products': products
    }
    return render(request, 'flash_sales.html', context)

def flash_sales_json(request):
    # Fetch top 10 products with highest discounts
    products = Product.objects.filter(discount__gt=0).annotate(
        sale_price=ExpressionWrapper(
            F('original_price') * (1 - F('discount') / 100),
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    ).order_by('-discount')[:10]

    products_data = [
        {
            'id': product.id,
            'name': product.product_name,
            'image_url': product.image.url if product.image else '',
            'sale_price': float(product.sale_price),
            'discount': float(product.discount)
        }
        for product in products
    ]

    return JsonResponse({'products': products_data})

def add_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        
        # Ensure the product exists
        product = get_object_or_404(Product, id=product_id)

        # Get or create the cart for the current user
        cart, created = Cart.objects.get_or_create(user=request.user)

        # Get or create the cart item
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        # Update quantity if the item already exists in the cart
        if not created:
            cart_item.quantity += 1
            cart_item.save()

        # Retrieve the updated cart items using the correct related name
        cart_items = cart.cart_items.all()  # Adjusted line
        total_price = sum(item.product.price * item.quantity for item in cart_items)  # Calculate total price
        
        # Render the cart template instead of returning JSON
        return render(request, 'cart.html', {
            'image_url': product.image.url if product.image else '',
            'cart_items': cart_items,
            'total_price': total_price,
        })

    return HttpResponseServerError("Invalid request")


def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cart_items.select_related('product').prefetch_related('product__images').all()
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    # Get the first image for each product in cart
    image_urls = []
    for item in cart_items:
        product_images = item.product.images.all()
        if product_images:
            image_urls.append(product_images[0].image.url) 
        else:
            image_urls.append('')

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'image_urls': image_urls,
    })
    
def update_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    data = json.loads(request.body)
    
    for item_data in data['items']:
        product = get_object_or_404(Product, id=item_data['id'])
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        cart_item.quantity = item_data['quantity']
        cart_item.save()

    # Remove items that are no longer in the cart
    cart.items.exclude(product__id__in=[item['id'] for item in data['items']]).delete()

    return redirect('Home:cart_view')  # Redirect back to the cart view after updating

def remove_from_cart(request, item_id):
    if request.method == "POST":
        cart_item = get_object_or_404(CartItem, id=item_id)
        cart_item.delete()  # Remove the cart item
        return redirect('Home:cart_view')  # Redirect back to the cart page
    
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    feedback_list = product.feedback_set.all()
    product_images = product.images.all()  # Assuming there's a related field for images
    context = {
        'product': product,
        'product_images': product_images,
        'feedback_list': feedback_list,
    }
    return render(request, 'product_description.html', context)


def checkout(request):
    if request.method == 'POST':
        selected_items = json.loads(request.body)  # Expecting the JSON body with selected items
        # Process each item (e.g., create orders, charge user, etc.)
        # Return a response
        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)

def submit_feedback(request, product_id):
    if request.method == 'POST':
        rating = request.POST.get('rating')  # Get rating from POST data
        comment = request.POST.get('comment')  # Get comment from POST data
        
        product = get_object_or_404(Product, id=product_id)  # Ensure the product exists                                                                              
       
        # Create the feedback record
        feedback = Feedback.objects.create(
            user=request.user,
            product=product,
            rating=rating,
            comment=comment
        )
        
        return JsonResponse({'success': True})  # Return success response
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)


@login_required
def customer_profile(request):
    user = request.user  # or get custom profile if applicable
    form = UserForm(request.POST or None, instance=user)
    
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile_view')
    
    return render(request, 'profile.html', {'form': form})

def view_feedback(request, product_id):
    products = Product.objects.prefetch_related('reviews').all()

    # Initialize filter form
    filter_form = ReviewFilterForm(request.GET or None)
    if filter_form.is_valid():
        # Search by product name
        search_query = filter_form.cleaned_data.get('search')
        if search_query:
            products = products.filter(name__icontains=search_query)

        # Filter by rating
        rating = filter_form.cleaned_data.get('rating')
        if rating:
            products = products.filter(reviews__rating=rating).distinct()

    # Process reply form submission
    if request.method == 'POST':
        reply_form = ReviewReplyForm(request.POST)
        if reply_form.is_valid():
            review_id = request.POST.get('review_id')
            review = get_object_or_404(Review, id=review_id)
            reply = reply_form.save(commit=False)
            reply.user = request.user
            reply.review = review
            reply.save()
            messages.success(request, "Your reply has been posted.")
            return redirect('view_feedback', product_id=product_id)
    else:
        reply_form = ReviewReplyForm()

    context = {
        'products': products,
        'filter_form': filter_form,
        'reply_form': reply_form,
    }
    return render(request, 'feedback.html', context)

def serch_products(request):
    query = request.GET.get('query', '')  # Get the search term from the URL
    results = Product.objects.filter(Q(product_name__icontains=query)).distinct() if query else []

    paginator = Paginator(results, 9)  # Show 9 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'query': query,
        'page_obj': page_obj,
    }
    return render(request, 'serch.html', context)



def initiate_payment(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        cart = Cart.objects.get_or_create(user=request.user)[0]
        cart_items = cart.cart_items.all()
        amount = float(sum(item.product.price * item.quantity for item in cart_items))
        
        # Store payment details in session for tracking
        request.session['pending_payment'] = {
            'amount': amount,
            'cart_items': list(cart_items.values())
        }
        
        response = lipa_na_mpesa_online(phone_number, amount, "TestAccount", "Payment Description")
        return JsonResponse(response)
    
    # Pass cart total to template
    cart = Cart.objects.get_or_create(user=request.user)[0]
    cart_items = cart.cart_items.all()
    total_amount = float(sum(item.product.price * item.quantity for item in cart_items))
    
    return render(request, 'chekout.html', {'total_amount': total_amount})

def mpesa_callback(request):
    callback_data = json.loads(request.body)
    
    if callback_data.get('ResultCode') == '0':  # Payment successful
        # Create order
        return create_order_after_payment(request)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Payment failed'
    }, status=400)


@login_required
def buyer_order_tracking(request):
    active_orders = Order.objects.filter(
        user=request.user,
        status__in=['pending', 'processing', 'shipped']
    ).select_related('product')

    completed_orders = Order.objects.filter(
        user=request.user,
        status__in=['delivered', 'cancelled']
    ).select_related('product')

    context = {
        'active_orders': active_orders,
        'completed_orders': completed_orders,
    }

    return render(request, 'buyer_order_tracking.html', context)

@login_required
@require_POST
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status in ['pending', 'processing']:
        order.status = 'cancelled'
        order.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'This order cannot be cancelled.'}, status=400)

def create_order_after_payment(request):
    if request.method == 'POST':
        payment_data = json.loads(request.body)
        
        if payment_data.get('ResultCode') == '0':  # Successful payment
            cart = Cart.objects.get(user=request.user)
            
            # Create main order
            order = Order.objects.create(
                user=request.user,
                total_amount=payment_data.get('Amount'),
                payment_id=payment_data.get('TransactionId'),
                status='processing'
            )
            
            # Create order items from cart
            for cart_item in cart.cart_items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )
                
                # Update product inventory
                product = cart_item.product
                product.stock -= cart_item.quantity
                product.sales_count += cart_item.quantity
                product.save()
            
            # Clear the cart
            cart.cart_items.all().delete()
            
            return JsonResponse({
                'status': 'success',
                'order_id': order.id
            })
    
    return JsonResponse({'status': 'error'}, status=400)
