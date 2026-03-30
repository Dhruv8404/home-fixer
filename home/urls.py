from django.urls import path
from . import views
from .views import (
    AddProductAndServiceChargeAPI,
    BookingDetailAPIView,
    BookingTrackingAPI,
    BookingCreateAPIView,
    AdminVendorControlAPI,
    CategoryNearbyServicemanAPI,
    CreatePaymentIntentAPI,
    CustomerCancelBookingAPI,
    LoginSendOTPAPI,
    LoginVerifyOTPAPI,
    NearbyVendorAPI,
    ProductDeleteAPI,
    ProductListAPI,
    RegisterSendOTPAPI,
    RegisterVerifyOTPAPI,
    RegisterCompleteAPI,
    ServicemanBookingActionAPI,
    ServicemanLocationUpdateAPI,
    ServicemanProfileUpdateAPI,
    UpdateProductAndServiceChargeAPI,
    UserProfileAPI,
    LogoutAPI,
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
     BookingSummaryAPI,
        ApproveProductsAPI,
        VendorOrderListAPI,
        AddProductAndServiceChargeAPI,
    VerifyStripePaymentAPI

)


from .admin_views import (
    AdminUserManagementAPI,
    AdminUserDetailAPI,
    CategoryListAPI,
    CategoryCreateAPI,
    CategoryDetailAPI)

urlpatterns = [

    path("login/",EmailPasswordLoginAPI.as_view()),
    #Logout
    path("auth/logout/", LogoutAPI.as_view()),

    # LOGIN
    path("auth/login/send-otp/", LoginSendOTPAPI.as_view()),
    path("auth/login/verify-otp/", LoginVerifyOTPAPI.as_view()),

    # REGISTER
    path("auth/register/send-otp/", RegisterSendOTPAPI.as_view()),
    path("auth/register/verify-otp/", RegisterVerifyOTPAPI.as_view()),
    path("auth/register/complete/", RegisterCompleteAPI.as_view()),

    # USER
    path("user/profile/", UserProfileAPI.as_view()),
    
    # Customer ,Vendor and Serviceman profiles
    path("user/customer-profile/", CustomerProfileAPI.as_view()),  
    path("user/serviceman-profile/", ServicemanProfileAPI.as_view()),
    path("user/vendor-profile/", VendorProfileAPI.as_view()),     
    path("profile/", ProfileAPI.as_view()),
    path("profile/customer/update/", CustomerProfileUpdateAPI.as_view()),
    path("profile/serviceman/update/", ServicemanProfileUpdateAPI.as_view()),
    path("profile/vendor/update/", VendorProfileUpdateAPI.as_view()),




    # Nearby Serviceman API
    path("servicemen/nearby/", NearbyServicemanAPI.as_view()),
    path("servicemen/category-nearby/", CategoryNearbyServicemanAPI.as_view()),
    # Admin APIs
    path("admin/users/", AdminUserManagementAPI.as_view()),          # GET, POST
    path("admin/users/<int:pk>/", AdminUserDetailAPI.as_view()),     
  
  
    # Categories
    path("categories/", CategoryListAPI.as_view()),          # GET all categories
    path("admin/categories/create/", CategoryCreateAPI.as_view()),    # POST create category
    path("admin/categories/<int:pk>/", CategoryDetailAPI.as_view()),  #


    # ===============================
    # ADMIN APPROVAL APIs
    # ===============================

    path("admin/servicemen/pending/", PendingServicemenAPI.as_view()),
    path("admin/vendors/pending/", PendingVendorsAPI.as_view()),

    path("admin/servicemen/<int:pk>/control/", AdminServicemanControlAPI.as_view()),
    path("admin/vendors/<int:pk>/control/", AdminVendorControlAPI.as_view()),

    #--------get all customers, servicemen and vendors for admin dashboard --------
    path("admin/customers/", views.AdminCustomerListAPI.as_view()),
    path("admin/servicemen/all/", views.AdminServicemanListAPI.as_view()),
    path("admin/vendors/all/", views.AdminVendorListAPI.as_view()),


    path("vendors/nearby/", NearbyVendorAPI.as_view(), name="vendors-nearby"),

# ================= BOOKINGS =================

path(
    "booking/create/",
    views.BookingCreateAPIView.as_view(),
    name="booking-create"
),
path(
    "booking/<int:booking_id>/cancel/",
    CustomerCancelBookingAPI.as_view(),
    name="customer-cancel-booking"
),
path("booking/<int:booking_id>/action/",ServicemanBookingActionAPI.as_view(),name="serviceman-booking-action"),
path("booking/<int:booking_id>/details/", BookingDetailAPIView.as_view(), name="booking-details"),
 path("bookings/<int:booking_id>/track/", BookingTrackingAPI.as_view(), name="booking-track"),
path(
    "serviceman/bookings/",
    views.ServicemanBookingRequestsAPI.as_view(),
    name="serviceman-bookings"
),

# ================= SERVICES =================


# ================= PRODUCTS =================
path("products/", ProductListAPI.as_view()),
path("products/create/", ProductCreateAPI.as_view()),
path("products/<int:pk>/update/", ProductUpdateAPI.as_view()),
path("products/<int:pk>/delete/", ProductDeleteAPI.as_view()),



# ================= PRODUCT CATEGORIES =================

path(
    "product-categories/",
    views.ProductCategoryAPI.as_view(),
    name="product-categories"
),
path(
    "product-categories/<int:pk>/delete/",
    views.ProductCategoryDeleteAPI.as_view(),
    name="delete-product-category"
),
#  LIVE LOCATION UPDATE
path("serviceman/location/update/", ServicemanLocationUpdateAPI.as_view()),





# ================= BOOKING PRODUCT FLOW =================



path(
    "products/nearby/",
    views.NearbyProductAPI.as_view(),
    name="nearby-products"
),



path(
    "booking/<int:booking_id>/summary/",
    views.BookingSummaryAPI.as_view(),
    name="booking-summary"
),

path(
    "booking/<int:booking_id>/approve/",
    views.ApproveProductsAPI.as_view(),
    name="approve-products"
),



path(
    "vendor/orders/",
    views.VendorOrderListAPI.as_view(),
    name="vendor-orders"
),

path(
    "booking/<int:booking_id>/add-product/",
    views.AddProductAndServiceChargeAPI.as_view(),
    name="add-product-service-charge"
),
path(
    'booking/<int:booking_id>/update-product-service/',
    UpdateProductAndServiceChargeAPI.as_view()
),


#Payment Integration (Simulated)
path(
    "booking/<int:booking_id>/payment/",
    views.BookingPaymentDetailAPI.as_view(),
    name="booking-payment-detail"
),
path("booking/<int:booking_id>/payment/create-intent/", CreatePaymentIntentAPI.as_view()),
path("booking/<int:booking_id>/payment/verify/", VerifyStripePaymentAPI.as_view()),




]