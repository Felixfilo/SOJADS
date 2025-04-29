from django.urls import path
from . import views

app_name='Admin'
urlpatterns = [
    path('admin_dashbord', views.admin_dashbord, name='admin_dashbord'),
    path('Main', views.Main ,name='Main'),
    path('users', views.users , name='users'),
    path('total_selling', views.total_selling , name='total_selling'),
    path('top_selling', views.top_selling , name='top_selling'),
    path('suspend_user', views.suspend_user , name='suspend_user'),
    path('activate_user/<int:user_id>/', views.activate_user, name='activate_user'),
    path('total_sales', views.total_sales , name='total_sales'),
    path('feedback_management', views.feedback_management , name='feedback_management'),
    path('delete/<int:feedback_id>/', views.delete_feedback, name='delete_feedback'),
    path('mark-reviewed/<int:feedback_id>/', views.mark_reviewed, name='mark_reviewed'),
]


