from django.urls import path
from . import views
from .views import (
    BookingDetailAPIView,
    ServiceListAPI,
    ServiceCreateAPI,
    ServiceUpdateAPI,
    ServiceSoftDeleteAPI,
    BookingCreateAPIView,
    AdminVendorControlAPI,
    CategoryNearbyServicemanAPI,
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
    ServicemanProfileUpdateAPI,
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
path("api/booking/<int:booking_id>/details/", BookingDetailAPIView.as_view(), name="booking-details"),

# ================= SERVICES =================
path("services/", views.ServiceListAPI.as_view(), name="service-list"),
path("services/create/", views.ServiceCreateAPI.as_view(), name="service-create"),
path("services/<int:pk>/update/", views.ServiceUpdateAPI.as_view(), name="service-update"),
path("services/<int:pk>/delete/", views.ServiceSoftDeleteAPI.as_view(), name="service-delete"),



# ================= PRODUCTS =================
path("products/", ProductListAPI.as_view()),
path("products/create/", ProductCreateAPI.as_view()),
path("products/<int:pk>/update/", ProductUpdateAPI.as_view()),
path("products/<int:pk>/delete/", ProductDeleteAPI.as_view()),
]
