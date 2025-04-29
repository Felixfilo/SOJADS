from django.urls import path
from . import views

app_name='Home'
urlpatterns = [
    path('', views.dashbord, name='dashbord'),
    path('home/', views.home, name='home'),
    path('customer_profile/', views.customer_profile, name='customer_profile'),
    path('category_list/', views.category_list, name='category_list'),
    path('category/<str:category_name>/', views.category, name='category'),
    path('checkout/', views.checkout, name='checkout'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart_view', views.cart_view, name='cart_view'),
    path('update_cart/', views.update_cart, name='update_cart'),
    path('deals/', views.deals, name='deals'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('submit_feedback/<int:product_id>/', views.submit_feedback, name='submit_feedback'),
    path('flash_sales_json/', views.flash_sales_json, name='flash_sales_json'),
    path('flash_sales/', views.flash_sales, name='flash_sales'),
    path('serch_products/', views.serch_products, name='serch_products'),
    path('logout/', views.logout, name='logout'),
    path('initiate_payment/', views.initiate_payment, name='initiate_payment'),
    path('mpesa_callback/', views.mpesa_callback, name='mpesa_callback'),
    path('create_order_after_payment/', views.create_order_after_payment, name='create_order_after_payment'),
    path('my-orders/', views.buyer_order_tracking, name='buyer_order_tracking'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
]