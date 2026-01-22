from .models import Cart

def cart_counter(request):
    if request.user.is_authenticated:
        total_items = Cart.objects.filter(user=request.user).count()
    else:
        total_items = 0
    return {'cart_count': total_items}
