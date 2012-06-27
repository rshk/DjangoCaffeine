# Create your views here.
from django.shortcuts import render

def example(request):
    return render(request, 'index.html')
