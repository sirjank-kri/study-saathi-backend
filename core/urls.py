from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import api_views

# API Router
router = DefaultRouter()
router.register(r'subjects', api_views.SubjectViewSet, basename='subject')

urlpatterns = [
    # ========== API ENDPOINTS (for React) ==========
    path('api/auth/register/', api_views.register_api, name='api_register'),
    path('api/auth/login/', api_views.login_api, name='api_login'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/profile/', api_views.user_profile, name='user_profile'),
    

    path('api/dashboard/stats/', api_views.dashboard_stats, name='dashboard_stats'),
    path('api/quiz/start/', api_views.start_quiz_api, name='start_quiz_api'),
    path('api/quiz/submit/', api_views.submit_quiz_api, name='submit_quiz_api'),
    path('api/history/', api_views.session_history_api, name='session_history_api'),
    path('api/quiz/save/', api_views.save_quiz_api, name='save_quiz_api'),
    path('api/analytics/', api_views.analytics_data_api, name='analytics_data'),
    path('api/schedule/', api_views.generate_schedule_api, name='generate_schedule'),
    path('api/log-session/', api_views.log_session_api, name='log_session'),
    path('api/', include(router.urls)),
]