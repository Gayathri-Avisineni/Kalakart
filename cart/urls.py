from django.urls import path
from . import views

urlpatterns = [
    # Checkout and order related
    path('checkout/', views.checkout, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),

    # Cart operations
    path('', views.view_cart, name='view_cart'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update/<int:cart_id>/', views.update_cart, name='update_cart'),
    path('remove/<int:cart_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),

    # Address URLs
    path('add-address/', views.add_address, name='add_address'),
    path('edit-address/<int:pk>/', views.edit_address, name='edit_address'),
    path('delete-address/<int:pk>/', views.delete_address, name='delete_address'),

    # Update cart quantity via Ajax
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/<int:order_id>/review/', views.add_review, name='add_review'),
    

]
