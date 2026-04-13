from django.urls import path
from . import views
from .views import (
    BookingDetailAPIView,
    BookingTrackingAPI,
    AdminVendorControlAPI,
    CategoryNearbyServicemanAPI,
    CreatePaymentIntentAPI,
    CustomerBookingHistoryAPI,
    CustomerCancelBookingAPI,
    LoginSendOTPAPI,
    LoginVerifyOTPAPI,
    MarkVendorCollectedAPI,
    NearbyVendorAPI,
    ProductDeleteAPI,
    ProductListAPI,
    RegisterSendOTPAPI,
    RegisterVerifyOTPAPI,
    RegisterCompleteAPI,
    ServicemanBookingActionAPI,
    ServicemanCompleteBookingAPI,
    ServicemanBookingHistoryAPI,
    ServicemanLocationUpdateAPI,
    ServicemanProfileUpdateAPI,
    UpdateProductAndServiceChargeAPI,
    UserProfileAPI,
    LogoutAPI,
    VendorAcceptOrderAPI,
    VendorDeliverOrderAPI,
    VendorProfileAPI,
    ServicemanProfileAPI,
    CustomerProfileAPI,
    CustomerProfileUpdateAPI,
    ProfileAPI,
    VendorProfileUpdateAPI,
    EmailPasswordLoginAPI,
    NearbyServicemanAPI,
    PendingVendorsAPI,
    PendingServicemenAPI,
    AdminServicemanControlAPI,
    ProductCreateAPI,
    ProductUpdateAPI,
    VendorTrackingAPI,
    VerifyStripePaymentAPI,
    AddProductAndServiceAPI,
    ApproveBookingItemsAPI,
    VendorOrdersView,
)

from .admin_views import (
    AdminUserManagementAPI,
    AdminUserDetailAPI,
    CategoryListAPI,
    CategoryCreateAPI,
    CategoryDetailAPI
)

urlpatterns = [

    # ================= AUTH =================
    path("login/", EmailPasswordLoginAPI.as_view(), name="login"),
    path("auth/logout/", LogoutAPI.as_view(), name="logout"),

    path("auth/login/send-otp/", LoginSendOTPAPI.as_view()),
    path("auth/login/verify-otp/", LoginVerifyOTPAPI.as_view()),

    path("auth/register/send-otp/", RegisterSendOTPAPI.as_view()),
    path("auth/register/verify-otp/", RegisterVerifyOTPAPI.as_view()),
    path("auth/register/complete/", RegisterCompleteAPI.as_view()),


    # ================= USER =================
    path("user/profile/", UserProfileAPI.as_view()),

    path("user/customer-profile/", CustomerProfileAPI.as_view()),
    path("user/serviceman-profile/", ServicemanProfileAPI.as_view()),
    path("user/vendor-profile/", VendorProfileAPI.as_view()),

    path("profile/", ProfileAPI.as_view()),
    path("profile/customer/update/", CustomerProfileUpdateAPI.as_view()),
    path("profile/serviceman/update/", ServicemanProfileUpdateAPI.as_view()),
    path("profile/vendor/update/", VendorProfileUpdateAPI.as_view()),


    # ================= NEARBY =================
    path("servicemen/nearby/", NearbyServicemanAPI.as_view()),
    path("servicemen/category-nearby/", CategoryNearbyServicemanAPI.as_view()),
    path("vendors/nearby/", NearbyVendorAPI.as_view(), name="vendors-nearby"),


    # ================= ADMIN =================
    path("admin/users/", AdminUserManagementAPI.as_view()),
    path("admin/users/<int:pk>/", AdminUserDetailAPI.as_view()),

    path("admin/servicemen/pending/", PendingServicemenAPI.as_view()),
    path("admin/vendors/pending/", PendingVendorsAPI.as_view()),

    path("admin/servicemen/<int:pk>/control/", AdminServicemanControlAPI.as_view()),
    path("admin/vendors/<int:pk>/control/", AdminVendorControlAPI.as_view()),

    path("admin/customers/", views.AdminCustomerListAPI.as_view()),
    path("admin/servicemen/all/", views.AdminServicemanListAPI.as_view()),
    path("admin/vendors/all/", views.AdminVendorListAPI.as_view()),


    # ================= CATEGORY =================
    path("categories/", CategoryListAPI.as_view()),
    path("admin/categories/create/", CategoryCreateAPI.as_view()),
    path("admin/categories/<int:pk>/", CategoryDetailAPI.as_view()),


    # ================= PRODUCTS =================
    path("products/", ProductListAPI.as_view()),
    path("products/create/", ProductCreateAPI.as_view()),
    path("products/<int:pk>/update/", ProductUpdateAPI.as_view()),
    path("products/<int:pk>/delete/", ProductDeleteAPI.as_view()),

    path("products/nearby/", views.NearbyProductAPI.as_view()),
    path("product-categories/", views.ProductCategoryAPI.as_view()),
    path("product-categories/<int:pk>/delete/", views.ProductCategoryDeleteAPI.as_view()),


    # ================= BOOKING =================
    path("booking/create/", views.BookingCreateAPIView.as_view()),

    path("booking/<int:booking_id>/cancel/", CustomerCancelBookingAPI.as_view()),
    path("booking/<int:booking_id>/details/", BookingDetailAPIView.as_view()),
    path("booking/<int:booking_id>/summary/", views.BookingSummaryAPI.as_view()),
    path("bookings/history/", CustomerBookingHistoryAPI.as_view()),

    path("booking/<int:booking_id>/action/", ServicemanBookingActionAPI.as_view()),
    path("bookings/<int:booking_id>/track/", BookingTrackingAPI.as_view()),

    path("serviceman/bookings/", views.ServicemanBookingRequestsAPI.as_view()),
    path("serviceman/bookings/history/", ServicemanBookingHistoryAPI.as_view()),
    path("serviceman/booking/<int:booking_id>/complete/", ServicemanCompleteBookingAPI.as_view()),



    # ================= BOOKING PRODUCT FLOW =================
    path("booking/<int:booking_id>/add-product/", AddProductAndServiceAPI.as_view()),
    path("booking/<int:booking_id>/update-product-service/", UpdateProductAndServiceChargeAPI.as_view()),
    path("booking/<int:booking_id>/approve/", ApproveBookingItemsAPI.as_view()),

    path(
        "booking/<int:booking_id>/payment/create-intent/",
        CreatePaymentIntentAPI.as_view(),
    ),
    # ================= PAYMENT =================
    path("booking/<int:booking_id>/payment/", views.BookingPaymentDetailAPI.as_view()),
    path("payment/create/", views.create_payment_view),
    path("payment/verify/stripe/", views.verify_stripe_payment),
    path("payment/verify/razorpay/", views.verify_razorpay_payment),


    # ================= VENDOR =================
    path("vendor/orders/", VendorOrdersView.as_view()),
    path("vendor/order/<int:order_id>/accept/", VendorAcceptOrderAPI.as_view()),
    path("vendor/order/<int:order_id>/deliver/", VendorDeliverOrderAPI.as_view()),
    path("vendor/order/<int:order_id>/collect/", MarkVendorCollectedAPI.as_view()),

    path("booking/<int:booking_id>/vendor-tracking/", VendorTrackingAPI.as_view()),


    # ================= LOCATION =================
    path("serviceman/location/update/", ServicemanLocationUpdateAPI.as_view()),
]