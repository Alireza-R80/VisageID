from rest_framework import serializers
from .models import User, FaceEmbedding
from facekit.adapter import FaceAdapter
from facekit.crypto import encrypt
from PIL import Image
import numpy as np
from io import BytesIO

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "display_name", "avatar_url", "is_active", "created_at"]
        read_only_fields = ["id", "is_active", "created_at"]

class FaceEmbeddingSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = FaceEmbedding
        fields = ["id", "user", "model_name", "vector", "active", "created_at", "updated_at", "image"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        image = validated_data.pop("image", None)
        if image is not None:
            adapter = FaceAdapter()
            image_bytes = image.read()
            img = Image.open(BytesIO(image_bytes)).convert("RGB")
            image_bgr = np.array(img)[:, :, ::-1]
            validated_data["vector"] = adapter.embed_and_encrypt(image_bgr)
        else:
            validated_data["vector"] = encrypt(validated_data["vector"])
        return super().create(validated_data)
