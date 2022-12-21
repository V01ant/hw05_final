from django.core.paginator import Paginator


def pagin_func(request, posts, posts_per_list):
    paginator = Paginator(posts, posts_per_list)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
