from django.shortcuts import render

def home(request):
    return render(request, "blog/home.html", {"title": "DjangoBlog Homepage"})

def about(request):
    return render(request, "blog/about.html", {"title": "Us"})

def contact(request):
    return render(request, "blog/contact.html", {"title": "Us"})


