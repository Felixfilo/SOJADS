from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from .models import Product, ProductImage  # Import your Product model
from .forms import ProductForm , ProductImageForm
from Home.models import Feedback
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from Home.models import Order


# Create your views here.
def main_sell(request):
    return render(request, 'main-sell.html')


def profile_sell(request):
    # Fetch the currently logged-in user's details
    user = request.user
    return render(request, 'profile_sell.html', {'user': user})

def  My_products(request):
    user = request.user
    products = Product.objects.filter(user=user) 
    return render(request, 'manage_products.html' ,{'user':user, 'products': products})


def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)  # Add request.FILES here
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.save()
            
            files = request.FILES.getlist('images')
            for f in files:
                ProductImage.objects.create(product=product, image=f)
                
            return redirect('Seller:My_products')
    else:
        form = ProductForm()

    return render(request, 'add_product.html', {'form': form})

def edit_product(request, id):
    product = get_object_or_404(Product, id=id)
    
    if request.method == 'POST':
        if 'delete_product' in request.POST:
            product.delete()
            return redirect('Seller:My_products')
            
        form = ProductForm(request.POST, instance=product)
        image_formset = ProductImageFormSet(request.POST, request.FILES, instance=product)
        
        if form.is_valid() and image_formset.is_valid():
            form.save()
            image_formset.save()
            return redirect('Seller:My_products')
    else:
        form = ProductForm(instance=product)
        image_formset = ProductImageForm(instance=product)
    
    context = {
        'form': form, 
        'image_formset': image_formset,
        'product': product
    }
    return render(request, 'edit_product.html', context)
        

def complete_order(order):
    for item in order.items.all():  # Assuming order.items is related to the Product or an OrderItem model
        product = item.product  # Ensure this is correct
        product.sales_count += item.quantity  # Increment by quantity purchased
        product.save()  # Save the updated product
        
        
@login_required
def feedback_review(request):
    feedbacks = Feedback.objects.all().order_by('-created_at')

    if request.method == 'POST':
        feedback_id = request.POST.get('feedback_id')  # Get feedback ID from POST data
        response_text = request.POST.get('response_text')  # Get response text from POST data

        if feedback_id and response_text:
            feedback = get_object_or_404(Feedback, id=feedback_id)
            # Create and save the response
            response = Response(feedback=feedback, text=response_text)  # Assuming Response model has these fields
            response.save()
            messages.success(request, 'Response added successfully.')
            return redirect('feedback_review')
        else:
            return HttpResponseBadRequest("Missing feedback ID or response text.")

    return render(request, 'feedback.html', {'feedbacks': feedbacks})

@login_required
def order_tracking(request):
    if hasattr(request.user, 'seller_profile'):
        unfulfilled_orders = Order.objects.filter(status='pending').order_by('-created_at')
        fulfilled_orders = Order.objects.filter(status='delivered').order_by('-created_at')
        context = {
            'unfulfilled_orders': unfulfilled_orders,
            'fulfilled_orders': fulfilled_orders,
        }
    else:
        user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
        context = {
            'user_orders': user_orders,
        }
    return render(request, 'order_tracking.html', context)

@require_POST
@user_passes_test(lambda u: hasattr(u, 'seller_profile'))
def fulfill_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id, status='pending')
        order.status = 'delivered'
        order.save()
        return JsonResponse({'status': 'success'})
    except Order.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)

@require_POST
@user_passes_test(lambda u: hasattr(u, 'seller_profile'))
def cancel_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id, status='pending')
        order.status = 'cancelled'
        order.save()
        return JsonResponse({'status': 'success'})
    except Order.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)
        return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)