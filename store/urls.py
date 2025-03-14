from django.conf.urls.static import static
from django.conf import settings
from django.urls import path,include
from . import views



urlpatterns = [
    path('', views.login_view, name="login_view"),
    path('accounts/login/', views.login_view, name='accounts_login'),
    path('accounts/', include('allauth.urls')),
    path('signup/', views.signup, name="signup"),
    path('forget/', views.forget_pass, name='forget_pass'),
    path('send-reset-otp/', views.send_reset_otp, name='send_reset_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('logout/', views.logout_view, name='logout_view'),
    path('home/', views.home_page, name="Home_page"),
    path('products/', views.product_list, name="Product_list"),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    
    path('cart/', views.cart, name="cart"),
    path('product/<int:product_id>/add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('wishlist/', views.wishlist, name="Wishlist"),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('my-account/', views.my_account, name="My_account"), 
    path('checkout/', views.checkout, name="Checkout"),
    path('add_address/', views.add_address, name='add_address'),
    path('edit-address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('razorpay/initiate/', views.initiate_razorpay_payment, name='initiate_razorpay_payment'),
    path('razorpay-payment/', views.razorpay_payment, name='razorpay_payment'),
    path('order-complete/', views.order_complete, name='order_complete'),
    path('order/<int:order_id>/invoice/', views.download_invoice, name='download_invoice'),
    path('order-complete/wallet/<int:order_id>/', views.order_complete, name='order_complete_wallet'),
    path('order-complete/razorpay/<str:razorpay_order_id>/<str:payment_method>/', views.order_complete, name='order_complete'),
    path('order-complete/<str:payment_method>/', views.order_complete, name='order_complete'),
    path('order-complete/<str:payment_method>/<str:razorpay_order_id>/', views.order_complete, name='order_complete'),
    path('order-complete/cod/<int:order_id>/', views.order_complete, name='order_complete'),
    path('order-complete/<str:payment_method>/<int:order_id>/', views.order_complete, name='order_complete'),
    path('order-complete/<str:payment_method>/<str:razorpay_order_id>/<int:order_id>/', views.order_complete, name='order_complete_razorpay_full'),
    path('contact/', views.contact, name="contact"),
    path('order_list/', views.order_list, name='order_list'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/<int:order_id>/invoice/', views.download_invoice, name='download_invoice'),
    path('order/<int:order_id>/continue-payment/', views.continue_payment, name='continue_payment'),
    path('process-payment/<int:order_id>/', views.process_payment, name='process_payment'),
    path('product/<int:product_id>/buy-now/', views.buy_now, name='buy_now'),
    


    
    


    path('admin/', views.admin_login, name='adminn'),
    path('admin/Admin/admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/generate-ledger/', views.generate_ledger, name='generate_ledger'), 
    path('admin/customers/', views.admin_users, name='admin_customers'),
    path('block_customer/<int:user_id>/', views.block_user, name='block_customer'),
    path('unblock_customer/<int:user_id>/', views.unblock_user, name='unblock_customer'),
    path('admin/products/', views.admin_products, name='admin_products'),
    path('admin/products/<int:product_id>/', views.admin_product_detail, name='admin_product_detail'),
    path('add-product/', views.add_product, name='add_product'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('admin/category/', views.admin_category_list, name='admin_category'),
    path('category/toggle/<int:category_id>/', views.toggle_listed_status, name='toggle_listed_status'),
    path('add-category/', views.add_category, name='add_category'),
    path('edit-category/<int:category_id>/', views.edit_category, name='edit_category'),
    path('delete-category/<int:category_id>/', views.soft_delete_category, name='soft_delete_category'),
    path('admin/orders/', views.orders_view, name='admin_orders'),
    path('update-order-status/', views.update_order_status, name='update_order_status'),
    path('admin/coupons/', views.admin_coupons, name='admin_coupons'),
    path('add-coupon/', views.add_coupon, name='admin_add_coupon'),
    path('edit/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('delete/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),
    path('admin/offers/', views.admin_offers, name='admin_offers'),
    path('admin/offers/add/', views.add_offer, name='add_offer'),
    path('edit_offer/<int:id>/', views.edit_offer, name='edit_offer'),
    path('delete_offer/<int:offer_id>/', views.delete_offer, name='delete_offer'),
    path('admin/sales/', views.admin_sales, name='admin_sales'),
    path('admin/sales/download/<str:file_type>/', views.download_report, name='download_report'),
    path('download-report/', views.download_report, name='download_report'),
    path('admin/settings/', views.admin_settings, name='admin_settings'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),
]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
