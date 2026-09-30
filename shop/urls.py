from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path( 'product/<int:product_id>/', views.product_detail,name='product_detail'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cart/', views.cart, name='cart'),
    path( 'cart/increase/<int:item_id>/', views.increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:item_id>/',  views.decrease_quantity, name='decrease_quantity'),
    path('cart/remove/<int:item_id>/',views.remove_from_cart, name='remove_from_cart'),
    path('orders/', views.order_history, name='order_history'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment-success/',views.payment_success,name='payment_success'),
    path('payment-cancel/',views.payment_cancel,name='payment_cancel'),

]
