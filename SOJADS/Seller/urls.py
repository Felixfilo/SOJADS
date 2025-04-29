from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


app_name='Seller'
urlpatterns = [
    path('', views.main_sell, name='main_sell'),
    path('profile/', views.profile_sell, name='profile_sell'),
    path('My_products/', views.My_products, name='My_products'),
    path('add_product/', views.add_product, name='add_product'),
    path('edit_product/<int:id>', views.edit_product, name='edit_product'),
    path('feedback_review/', views.feedback_review, name='feedback_review'),
    path('order-tracking/', views.order_tracking, name='order_tracking'),
    path('fulfill-order/<int:order_id>/', views.fulfill_order, name='fulfill_order'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
 