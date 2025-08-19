from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, FaceEmbeddingViewSet
from . import views_web, views_face, views_api

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"embeddings", FaceEmbeddingViewSet, basename="embedding")

urlpatterns = [
    path("signup/", views_web.signup, name="account-signup"),
    path("profile/", views_web.profile, name="account-profile"),
    # Face auth endpoints
    path("face/login", views_face.face_login, name="account-face-login"),
    path("face/signup", views_face.face_signup, name="account-face-signup"),
    path("face/enroll", views_face.face_enroll, name="account-face-enroll"),
    path("face/reenroll", views_face.face_reenroll, name="account-face-reenroll"),
    # Profile and email verification APIs
    path("profile.json", views_api.profile_api, name="account-profile-api"),
    path("verify-email/request", views_api.request_verify_email, name="account-request-verify-email"),
    path("verify-email", views_api.verify_email, name="account-verify-email"),
    path("signup", views_api.signup_plain, name="account-signup-api"),
]

urlpatterns += router.urls
