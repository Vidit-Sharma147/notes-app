from django.shortcuts import render

def main(request):
    return render(request, 'myapp/main.html')

def login(request):
    return render(request, 'myapp/login.html')



def login_page(request):
    return render(request, 'login.html')
def mainlogin_page(request):
    return render(request, 'mainlogin.html')

def main_page(request):
    return render(request, 'main.html')