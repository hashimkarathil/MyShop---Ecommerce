from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Cart, Order, OrderItem
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
import stripe
from django.conf import settings
from .models import Product

stripe.api_key = settings.STRIPE_SECRET_KEY

def home(request):
    products = Product.objects.all()

    return render(
        request,
        'shop/home.html',
        {'products': products}
    )


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    return render(request, 'shop/product_detail.html', {
        'product': product
    })


@login_required(login_url='login')
def add_to_cart(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    quantity = int(request.POST.get('quantity', 1))

    if quantity < 1:
        quantity = 1

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product
    )

    if created:
        cart_item.quantity = quantity
    else:
        cart_item.quantity += quantity

    cart_item.save()

    return redirect('cart')


def signup(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            return render(
                request,
                'shop/signup.html',
                {'error': 'Username already exists'}
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        login(request, user)

        return redirect('home')

    return render(request, 'shop/signup.html')


def login_view(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            # Go back to the page user originally wanted
            next_url = request.GET.get('next')

            if next_url:
                return redirect(next_url)

            return redirect('home')

        return render(
            request,
            'shop/login.html',
            {'error': 'Invalid username or password'}
        )

    return render(request, 'shop/login.html')


@login_required(login_url='login')
def logout_view(request):

    logout(request)

    return redirect('home')


@login_required(login_url='login')
def cart(request):

    cart_items = Cart.objects.filter(user=request.user)

    total = sum(
        item.total_price
        for item in cart_items
    )

    return render(
        request,
        'shop/cart.html',
        {
            'cart_items': cart_items,
            'total': total,
        }
    )

@login_required(login_url='login')
def increase_quantity(request, item_id):

    cart_item = get_object_or_404(
        Cart,
        id=item_id,
        user=request.user
    )

    cart_item.quantity += 1
    cart_item.save()

    return redirect('cart')



@login_required(login_url='login')
def decrease_quantity(request, item_id):

    cart_item = get_object_or_404(
        Cart,
        id=item_id,
        user=request.user
    )

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()

    return redirect('cart')


def remove_from_cart(request, item_id):

    if not request.user.is_authenticated:
        return redirect('login')

    cart_item = get_object_or_404(
        Cart,
        id=item_id,
        user=request.user
    )

    cart_item.delete()

    return redirect('cart')


@login_required(login_url='login')
def checkout(request):

    cart_items = Cart.objects.filter(user=request.user)

    if not cart_items.exists():
        return redirect('cart')

    total = sum(
        item.total_price
        for item in cart_items
    )

    order = Order.objects.create(
        user=request.user,
        total_price=total,
        payment_method='STRIPE',
        status='Pending'
    )

    line_items = []

    for item in cart_items:

        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )

        line_items.append({
            'price_data': {
                'currency': 'inr',
                'product_data': {
                    'name': item.product.name,
                },
                'unit_amount': int(item.product.price * 100),
            },
            'quantity': item.quantity,
        })

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',

        success_url=request.build_absolute_uri(
            '/payment-success/'
        ) + '?session_id={CHECKOUT_SESSION_ID}',

        cancel_url=request.build_absolute_uri(
            '/payment-cancel/'
        ),

        metadata={
            'order_id': order.id
        }
    )

    order.stripe_session_id = session.id
    order.save()

    return redirect(session.url)


@login_required(login_url='login')
def payment_success(request):

    session_id = request.GET.get('session_id')

    if session_id:
        session = stripe.checkout.Session.retrieve(session_id)

        order_id = getattr(session.metadata, 'order_id', None)

        if order_id:
            order = Order.objects.get(id=order_id)

            # Check Stripe payment status
            if session.payment_status == 'paid':
                order.status = 'Paid'
                order.save()

                # Clear user's cart after successful payment
                Cart.objects.filter(user=request.user).delete()

    return render(request, 'shop/payment_success.html')



def payment_cancel(request):
    return render(request, 'shop/payment_cancel.html')


@login_required(login_url='login')
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-ordered_at')

    return render(request, 'shop/order_history.html', {
        'orders': orders
    })