
from django.urls import path


from customers.Api.views import RegisterMakerView, RegisterCheckerView, LoginView,MakersUnderCheckerView,CustomTokenObtainPairView,StatusUpdateApprove,StatusUpdateDecline
from customers.Api.views import (
    UploadCustomerDataView,
    CustomerDataView,
 
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
urlpatterns = [

    path('register/maker/', RegisterMakerView.as_view(), name='register-maker'),
    path('register/checker/', RegisterCheckerView.as_view(), name='register-checker'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('makers/', MakersUnderCheckerView.as_view(), name='makers-under-checker'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('upload/', UploadCustomerDataView.as_view(), name='upload-customer-data'),
    path('customer_data/', CustomerDataView.as_view(), name='customer_data'),

    path('makers-under-checker/', MakersUnderCheckerView.as_view(), name='makers-under-checker'),
    path('status-approve/', StatusUpdateApprove.as_view(), name='status-approve'),
    path('sataus-decline',StatusUpdateDecline.as_view(),name='status-decline')
]
