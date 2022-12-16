from django.core.paginator import Paginator
from django.conf import settings


def paginator_context(queryset, request):
    paginator = Paginator(queryset, settings.NMB_OF_ITEMS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
