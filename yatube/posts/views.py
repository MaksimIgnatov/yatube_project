from django.shortcuts import render
from django.http import HttpResponse

# Главная страница
def index(request):    
    return HttpResponse('Главная страница')

# Главная страница
def group_posts(request, slug):    
    return HttpResponse(f'Страница группы {slug}')
