from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login 
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseBadRequest


# Create your views here.
def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return render(request, 'admin_choice.html')  # New template for choices
            return redirect('Home:dashbord')
        else:
            return HttpResponseBadRequest("Invalid login credentials.")
    return render(request, 'Login.html')


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']

        if User.objects.filter(username=username).exists():
            return HttpResponseBadRequest("Username already exists.")

        user = User.objects.create_user(username=username, password=password, email=email)
        return redirect('login_user')  # or another redirect as needed

    return render(request, 'Register.html')