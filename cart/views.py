# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.models import Product
from .models import Cart, Order, OrderItem, Address, Review
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages
from django import forms
import json
from django.views.decorators.cache import never_cache


def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        login_url = reverse('login')
        return JsonResponse({'login_required': True, 'redirect_url': f"{login_url}?next={request.path}"})

    product = get_object_or_404(Product, id=product_id)
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    # total items in cart
    total_items = Cart.objects.filter(user=request.user).count()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({'success': True, 'total_items': total_items})
    else:
        return redirect('view_cart')



# View Cart
@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(item.subtotal for item in cart_items)  # no parentheses
    return render(request, 'cart/view_cart.html', {'cart_items': cart_items, 'total': total})

# Update Cart Item Quantity
@login_required
def update_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('view_cart')

# Remove item from cart
@login_required
def remove_from_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    cart_item.delete()
    return redirect('view_cart')


# -----------------
# Buy Now
# -----------------
@login_required
def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Create cart item if it doesn't exist, otherwise increment quantity
    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product,
        ordered=False
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    # Mark this product as buy-now in session
    request.session['buy_now_product_id'] = product.id

    return redirect('checkout')

# -----------------
# Checkout / Review Page
# -----------------
@login_required
def checkout(request):
    user = request.user
    buy_now_product_id = request.session.get('buy_now_product_id')

    if buy_now_product_id:
        # Buy Now scenario: only this product
        cart_items = Cart.objects.filter(
            user=user,
            product_id=buy_now_product_id,
            ordered=False
        )
    else:
        # Normal checkout scenario: fetch all cart items
        cart_items = Cart.objects.filter(user=user, ordered=False)
        # Ensure buy_now_product_id does not interfere
        request.session.pop('buy_now_product_id', None)

    addresses = Address.objects.filter(user=user)

    # Calculate total
    total = sum(item.subtotal for item in cart_items)

    if request.method == "POST":
        # Create order
        order = Order.objects.create(user=user, total=total)

        for item in cart_items:
            order.items.create(
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
                subtotal=item.subtotal  # add subtotal
            )

        # Mark items as ordered
        for item in cart_items:
            item.ordered = True
            item.save()

        # Clear buy_now session if exists
        if buy_now_product_id:
            del request.session['buy_now_product_id']

        return redirect('order_success', order_id=order.id)

    context = {
        'cart_items': cart_items,
        'addresses': addresses,
        'total': total,
    }
    return render(request, 'cart/checkout.html', context)

# -----------------
# Place Order / Payment
# -----------------
@never_cache
@login_required
def place_order(request):
    if request.method != "POST":
        return redirect('checkout')

    address_id = request.POST.get('address')
    payment_method = request.POST.get('payment_method')

    if not address_id:
        return redirect('checkout')

    try:
        address = Address.objects.get(id=address_id, user=request.user)
    except Address.DoesNotExist:
        return redirect('checkout')

    # Check for buy-now session
    buy_now_product_id = request.session.get('buy_now_product_id')
    if buy_now_product_id:
        cart_items = Cart.objects.filter(user=request.user, product_id=buy_now_product_id, ordered=False)
    else:
        cart_items = Cart.objects.filter(user=request.user, ordered=False)

    if not cart_items.exists():
        return redirect('checkout')

   # Calculate total price before creating order
    total = sum(item.product.price * item.quantity for item in cart_items)

    # Create order with correct total
    order = Order.objects.create(
    user=request.user,
    address=address,
    payment_method=payment_method,
    total=total,
    status='Pending'  # Optional: set default status
)
    for item in cart_items:
        OrderItem.objects.create(
        order=order,
        product=item.product,
        quantity=item.quantity,
        price=item.product.price,
        subtotal=item.product.price * item.quantity

    )
# After creating order items, delete cart items
    cart_items.delete()

    # Clear buy-now session after ordering
    request.session.pop('buy_now_product_id', None)

    return redirect('order_success', order_id=order.id)

@never_cache
@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'cart/order_success.html', {'order': order})

# -----------------
# Order Confirmation Page
# -----------------
@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'cart/order_confirmation.html', {'order': order})



class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'phone', 'address_line1', 'address_line2', 'city', 'state', 'pincode', 'country']

@never_cache
@login_required
def add_address(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            return redirect('checkout')
    else:
        form = AddressForm()
    return render(request, 'cart/add_address.html', {'form': form})


@never_cache
@login_required
def edit_address(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            return redirect('checkout')
    else:
        form = AddressForm(instance=address)
    return render(request, 'cart/edit_address.html', {'form': form})


@login_required
def delete_address(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == "POST":
        address.delete()
        return redirect('checkout')
    return render(request, 'cart/delete_address.html', {'address': address})




def update_cart_item(request, item_id):
    if request.method == "POST":
        data = json.loads(request.body)
        quantity = int(data.get("quantity", 1))
        cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        return JsonResponse({'success': True, 'subtotal': cart_item.subtotal()})
    return JsonResponse({'success': False})



@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'cart/my_orders.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'cart/order_detail.html', {'order': order})


@login_required
def add_review(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        rating = int(request.POST.get('rating'))
        comment = request.POST.get('comment')
        Review.objects.create(order=order, rating=rating, comment=comment)
        return redirect('my_orders')

    return render(request, 'cart/add_review.html', {'order': order})