from rest_framework import serializers
from .models import User, FaceEmbedding

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "display_name", "avatar_url", "is_active", "created_at"]
        read_only_fields = ["id", "is_active", "created_at"]

class FaceEmbeddingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaceEmbedding
        fields = ["id", "user", "model_name", "vector", "active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
