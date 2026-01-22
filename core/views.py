# core/views.py (or split into core/views.py + users/views.py if preferred)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Product, ProductImage,Category, Region, UserProfile
from .forms import CustomUserRegistrationForm
from django.db.models import Q
from thefuzz import fuzz
from nltk.stem import WordNetLemmatizer
from django.views.decorators.cache import never_cache
from .forms import UserForm, ProfileForm
from cart.models import Order, OrderItem
from .models import Review
from .forms import SellerProfileForm
from .models import SellerProfile
from .forms import ProductForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.template import loader

# -------------------------
# Core App Views (Products)
# -------------------------

def home(request):   
    featured_products = Product.objects.all().order_by('-created_at')[:15]
    categories = Category.objects.all()
    regions = Region.objects.all()
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'regions': regions
    }
    return render(request, 'core/home.html', context)  # core folder


def about(request):
    return render(request, 'core/about.html')

def product_list(request):
    products = Product.objects.all()
    return render(request, 'core/product_list.html', {'products': products})  # core folder

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    images = product.images.all()
    similar_products = product.category.product_set.exclude(id=product.id)
    context = {
        'product': product,
        'images': images,
        'similar_products': similar_products
    }
    return render(request, 'core/product_detail.html', context)  # core folder

def product_by_category(request, category_id):
    category_obj = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category_obj)
    return render(request, 'core/product_list.html', {'products': products, 'category': category_obj})  # core folder

def products_by_region(request, region_id):
    region = get_object_or_404(Region, id=region_id)
    products = Product.objects.filter(region=region)
    context = {'products': products, 'region': region}
    return render(request, 'core/product_list.html', context)  # core folder

@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html')  # core folder

# -------------------------
# Users / Authentication
# -------------------------
from django.utils.http import url_has_allowed_host_and_scheme

@never_cache
def login_view(request):
    # If user is already logged in, redirect to home
    if request.user.is_authenticated:
        return redirect('home')

    # Determine next_url safely
    next_url = request.POST.get('next') or request.GET.get('next')
    if not next_url or next_url in [reverse('login'), reverse('register')]:
        next_url = reverse('home')

    # Extra safety: only allow relative URLs within your site
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = reverse('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect(next_url)
        else:
            if not User.objects.filter(username=username).exists():
                messages.error(request, 'Account not found. Please register to continue.')
            else:
                messages.error(request, 'Incorrect password. Please try again.')

    return render(request, 'users/login.html', {'next': next_url})



@never_cache
def register_view(request):
    # If user is already logged in, redirect to previous page or home
    if request.user.is_authenticated:
        previous_url = request.META.get('HTTP_REFERER') or 'home'
        return redirect(previous_url)

    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            UserProfile.objects.create(
                user=user,
                gender=form.cleaned_data.get('gender'),
                account_type=form.cleaned_data.get('account_type'),
                phone=form.cleaned_data.get('phone')
            )
            messages.success(request, "Registration successful.")
            return redirect('login')
    else:
        form = CustomUserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})




@login_required
def profile_view(request):
    user_profile = UserProfile.objects.get(user=request.user)
    return render(request, 'users/profile.html', {'user_profile': user_profile})  # users folder

def logout_view(request):
    logout(request)
    return redirect('home')  # redirects to core/home.html




# Initialize lemmatizer once
lemmatizer = WordNetLemmatizer()

def search_products(request):
    query = request.GET.get('q', '').strip()  # search text
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    category_id = request.GET.get('category')
    region_id = request.GET.get('region')
    sort_by = request.GET.get('sort')

    # Step 1: Start with all products
    products = Product.objects.all()

    # Step 2: Apply filters
    if category_id:
        products = products.filter(category_id=category_id)
    if region_id:
        products = products.filter(region_id=region_id)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Step 3: Process query using lemmatization + fuzzy
    results = []
    if query:
        query_root = lemmatizer.lemmatize(query.lower())
        for product in products:
            # Prepare searchable text: include name, description, material, color, region name, category name
            searchable_text = " ".join(filter(None, [
                str(product.name),
                str(product.description),
                str(product.material),
                str(product.color),
                str(product.region.name if product.region else ''),
                str(product.category.name if product.category else '')
            ])).lower()

            # Lemmatize each word in product text
            searchable_words = [lemmatizer.lemmatize(word) for word in searchable_text.split()]
            searchable_root = " ".join(searchable_words)

            # Check for substring match or fuzzy match
            similarity = fuzz.token_set_ratio(query_root, searchable_root)
            if query_root in searchable_root or similarity >= 40:  # 40 = more lenient
                results.append((product, similarity))

        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        results = [prod for prod, score in results]
    else:
        results = list(products)

    # Step 4: Apply sorting
    if sort_by == "price_asc":
        results.sort(key=lambda x: x.price)
    elif sort_by == "price_desc":
        results.sort(key=lambda x: x.price, reverse=True)
    elif sort_by == "newest":
        results.sort(key=lambda x: x.created_at, reverse=True)

    # Categories for filter dropdown
    categories = Category.objects.all()
    regions = Region.objects.all()


    context = {
        'products': results,
        'query': query,
        'categories': categories,
        'regions': regions,
        'selected_category': category_id,
        'selected_region': region_id, 
        'region': region_id,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
    }

    return render(request, 'core/search_results.html', context)



@login_required
def my_profile(request):
    user = request.user
    profile = user.userprofile  # This will always exist due to signals
    return render(request, 'users/my_profile.html', {'user': user, 'profile': profile})


def profile_view(request):
    return render(request, 'users/my_profile.html', {})

# make sure this is imported
@never_cache
@login_required
def edit_profile(request):
    profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('my_profile')   # ✅ force refresh to see updated image

    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    return render(request, 'users/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile
    })




@login_required
def orders_view(request):
    from core.models import Product  # import here to avoid circular import
    from cart.models import Order

    orders = Order.objects.filter(user=request.user)
    return render(request, 'users/orders.html', {'orders': orders})



@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')

    if request.method == "POST":
        product_id = request.POST.get("product_id")
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")

        product = get_object_or_404(Product, id=product_id)
        Review.objects.create(user=request.user, product=product, rating=rating, comment=comment)

        return redirect("my_orders")

    return render(request, "orders.html", {"orders": orders})

def orders(request):
    return render(request, 'cart/orders.html')




@login_required
def start_selling(request):
    """Check user state and redirect accordingly."""
    try:
        # If already has a seller profile → show profile page
        seller_profile = SellerProfile.objects.get(user=request.user)
        return redirect('seller_profile', seller_id=seller_profile.id)
    except SellerProfile.DoesNotExist:
        # If not a seller → go to seller form
        return redirect('create_seller_profile')


@login_required
def create_seller_profile(request):
    """Form to create seller profile."""
    if SellerProfile.objects.filter(user=request.user).exists():
        # If they already made one, redirect directly
        return redirect('seller_profile', seller_id=request.user.sellerprofile.id)
    
    if request.method == 'POST':
        form = SellerProfileForm(request.POST, request.FILES)
        if form.is_valid():
            seller_profile = form.save(commit=False)
            seller_profile.user = request.user
            seller_profile.save()
            return redirect('seller_profile', seller_id=seller_profile.id)
    else:
        form = SellerProfileForm()
    
    return render(request, 'core/seller_form.html', {'form': form})


def seller_profile(request, seller_id):
    seller = get_object_or_404(SellerProfile, id=seller_id)
    products = seller.products.all()  # Get all products uploaded by this seller
    seller_orders = OrderItem.objects.filter(product__in=products).order_by('-order__created_at')

    total_products = products.count()
    joined_date = seller.user.date_joined.strftime("%b %Y")

    context = {
        'seller': seller,
        'products': products,
        'total_products': total_products,
        'joined_date': joined_date,
        'seller_orders': seller_orders,
    }
    return render(request, 'core/seller_profile.html', context)



@login_required
def add_product(request):
    try:
        seller_profile = SellerProfile.objects.get(user=request.user)
    except SellerProfile.DoesNotExist:
        messages.warning(request, "Please complete your seller profile first.")
        return redirect('seller_form')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        files = request.FILES.getlist('extra_images')  # get multiple images

        if form.is_valid():
            product = form.save(commit=False)
            product.seller = seller_profile
            product.save()

            # Save extra images
            for file in files:
                ProductImage.objects.create(product=product, image=file)

            messages.success(request, "Product added successfully!")
            return redirect('seller_profile', seller_id=request.user.sellerprofile.id)
    else:
        form = ProductForm()

    return render(request, 'core/add_product.html', {'form': form})


@login_required
def edit_seller_profile(request):
    seller_profile = request.user.sellerprofile

    if request.method == 'POST':
        form = SellerProfileForm(request.POST, request.FILES, instance=seller_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")

            # Redirect to seller_profile with special param
            return redirect(f"{reverse('seller_profile', kwargs={'seller_id': seller_profile.id})}?from_edit=1")
    else:
        form = SellerProfileForm(instance=seller_profile)

    return render(request, 'core/edit_seller_profile.html', {'form': form})

@never_cache
@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, seller__user=request.user)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product details updated successfully!")
            return redirect('seller_profile', seller_id=request.user.sellerprofile.id)
    else:
        form = ProductForm(instance=product)

    return render(request, 'core/edit_product.html', {'form': form, 'product': product})



def public_seller_profile(request, seller_id):
    seller = get_object_or_404(SellerProfile, id=seller_id)
    products = Product.objects.filter(seller=seller)

    context = {
        'seller': seller,
        'products': products,
    }
    return render(request, 'core/public_seller_profile.html', context)
