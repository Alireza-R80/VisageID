from rest_framework import permissions, viewsets

from .models import User, FaceEmbedding
from .serializers import UserSerializer, FaceEmbeddingSerializer


class UserViewSet(viewsets.ModelViewSet):
    """API endpoint for managing users."""

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]


class FaceEmbeddingViewSet(viewsets.ModelViewSet):
    """API endpoint for managing face embeddings."""

    queryset = FaceEmbedding.objects.all()
    serializer_class = FaceEmbeddingSerializer
    permission_classes = [permissions.IsAuthenticated]
