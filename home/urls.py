from django.urls import path
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
    VendorProfileUpdateAPI
)

urlpatterns = [
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



]
