from django.urls import path
from . import views
from .views import (
    AdminVendorControlAPI,
    CategoryNearbyServicemanAPI,
    CreateBookingAPI,
    LoginSendOTPAPI,
    LoginVerifyOTPAPI,
    NearbyVendorAPI,
    RegisterSendOTPAPI,
    RegisterVerifyOTPAPI,
    RegisterCompleteAPI,
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


    path("services/<int:pk>/delete/", views.ServiceSoftDeleteAPI.as_view()),
    path("products/<int:pk>/delete/", views.ProductSoftDeleteAPI.as_view()),

    # Nearby Serviceman API
    path("servicemen/nearby/", NearbyServicemanAPI.as_view()),
    path("servicemen/category-nearby/", CategoryNearbyServicemanAPI.as_view()),
    # Admin APIs
    path("admin/users/", AdminUserManagementAPI.as_view()),          # GET, POST
    path("admin/users/<int:pk>/", AdminUserDetailAPI.as_view()),     
  
  
    # Categories
    path("categories/", CategoryListAPI.as_view()),          # GET all categories
    path("admin/categories/create", CategoryCreateAPI.as_view()),    # POST create category
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
    path("bookings/create/", CreateBookingAPI.as_view()),

]
