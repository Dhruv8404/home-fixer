from django.urls import path
from . import views
from .views import (
    LoginSendOTPAPI,
    LoginVerifyOTPAPI,
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
    CategoryCreateAPI,
    CategoryDetailAPI,
    NearbyServicemanAPI,
    
)

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

   # Category APIs
    path("categories/", CategoryCreateAPI.as_view()),          # POST
    path("categories/<int:pk>/", CategoryDetailAPI.as_view()), # PUT, DELETE

    path("services/<int:pk>/delete/", views.ServiceSoftDeleteAPI.as_view()),
    path("products/<int:pk>/delete/", views.ProductSoftDeleteAPI.as_view()),

    # Nearby Serviceman API
    path("servicemen/nearby/", NearbyServicemanAPI.as_view()),
    path("servicemen/", views.ServicemenListAPI.as_view()),





]
