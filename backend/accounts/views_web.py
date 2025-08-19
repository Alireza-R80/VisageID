from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect
from django import forms

from .models import User, FaceEmbedding
from facekit.adapter import FaceAdapter


class SignUpForm(forms.Form):
    email = forms.EmailField()
    display_name = forms.CharField(max_length=200)
    password = forms.CharField(widget=forms.PasswordInput)
    avatar_url = forms.URLField(required=False)
    face_image = forms.ImageField(required=False, help_text="Optional: upload a face image to enroll")


@csrf_protect
def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = User.objects.create_user(
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
                display_name=form.cleaned_data["display_name"],
                avatar_url=form.cleaned_data.get("avatar_url", ""),
            )
            # Optional: create an initial embedding
            img = form.cleaned_data.get("face_image")
            if img:
                import numpy as np
                from PIL import Image
                from io import BytesIO

                adapter = FaceAdapter()
                image_bytes = img.read()
                pil = Image.open(BytesIO(image_bytes)).convert("RGB")
                bgr = np.array(pil)[:, :, ::-1]
                vector_enc = adapter.embed_and_encrypt(bgr)
                FaceEmbedding.objects.create(user=user, model_name=adapter.model_name, vector=vector_enc)

            login(request, user)
            return redirect("account-profile")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["display_name", "avatar_url"]


@login_required
@csrf_protect
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("account-profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})
