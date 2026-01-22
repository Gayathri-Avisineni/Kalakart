from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),  # updated
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('profile/', views.profile_view, name='profile'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    
    path('products/category/<int:category_id>/', views.product_by_category, name='product_by_category'),
    path('region/<int:region_id>/', views.products_by_region, name='products_by_region'),
    path("search/", views.search_products, name="search_products"),
    path('about/', views.about, name='about'),
    path('profile/', views.my_profile, name='my_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),  # <- this must exist
    path("my-orders/", views.my_orders, name="my_orders"),
    path('orders/', views.orders, name='orders'),
    path('start-selling/', views.start_selling, name='start_selling'),
    path('create-seller-profile/', views.create_seller_profile, name='create_seller_profile'),
    path('seller/<int:seller_id>/', views.seller_profile, name='seller_profile'),
    path('add-product/', views.add_product, name='add_product'),
    path('seller/edit/', views.edit_seller_profile, name='edit_seller_profile'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
       

    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
        name='password_reset'
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
        name='password_reset_confirm'
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
        name='password_reset_complete'
    ),
     path('seller/public/<int:seller_id>/', views.public_seller_profile, name='public_seller_profile'),


]
