from rest_framework.routers import DefaultRouter

from .views import UserViewSet, FaceEmbeddingViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"embeddings", FaceEmbeddingViewSet, basename="embedding")

urlpatterns = router.urls
