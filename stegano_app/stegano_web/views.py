from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt

class IndexView(TemplateView):
    template_name = "index.html"

@csrf_exempt
def frontend(request):
    """
    View to serve the React frontend
    """
    return IndexView.as_view()(request)