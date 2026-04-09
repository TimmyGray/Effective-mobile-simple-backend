from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from accounts.models import User


class RegisterSerializer(serializers.ModelSerializer[User]):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "email", "password")
        read_only_fields = ("id",)

    def validate_password(self, value: str) -> str:
        """
        AI Annotation:
        - Purpose: Enforce Django password policy at registration boundary.
        - Inputs: Receives a raw password candidate from request payload.
        - Outputs: Returns the same password if valid; otherwise raises serializer validation errors.
        - Security notes: Avoids weak credentials by delegating to configured validators.
        """
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def create(self, validated_data: dict) -> User:
        """
        AI Annotation:
        - Purpose: Create a new application user from validated registration data.
        - Inputs: Requires serializer-validated `email` and `password` fields.
        - Side effects: Persists a user record and stores a hashed password in the database.
        - Security notes: Uses custom manager create flow to avoid raw password persistence.
        """
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        """
        AI Annotation:
        - Purpose: Authenticate login credentials and attach the authenticated user to attrs.
        - Inputs: Expects `email` and `password`; request object is read from serializer context.
        - Outputs: Returns attrs augmented with `user` when authentication succeeds.
        - Failure modes: Raises AuthenticationFailed for invalid credentials or inactive users.
        """
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["email"],
            password=attrs["password"],
        )
        if not user:
            raise AuthenticationFailed("Invalid credentials.")
        if not user.is_active:
            raise AuthenticationFailed("Invalid credentials.")
        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name")


class UserProfileUpdateSerializer(serializers.ModelSerializer[User]):
    password = serializers.CharField(write_only=True, required=False)
    current_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password", "current_password")

    def validate_email(self, value: str) -> str:
        """
        AI Annotation:
        - Purpose: Normalize email and enforce uniqueness excluding the current user.
        - Inputs: New email from PATCH body.
        - Outputs: Normalized email string.
        - Failure modes: ValidationError when another account owns the email.
        """
        user = self.context["request"].user
        normalized = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=normalized).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return normalized

    def validate(self, attrs: dict) -> dict:
        """
        AI Annotation:
        - Purpose: Tie password changes to verified current password and policy validators.
        - Inputs: Optional `password` and `current_password` fields.
        - Failure modes: ValidationError when password change rules are inconsistent or wrong.
        - Security notes: Rejects new password without successful current-password check.
        """
        new_password = attrs.get("password")
        current_password = attrs.get("current_password")
        user = self.context["request"].user
        if new_password:
            if not current_password:
                raise serializers.ValidationError(
                    {"current_password": "Current password is required to set a new password."}
                )
            if not user.check_password(current_password):
                raise serializers.ValidationError({"current_password": "Invalid current password."})
            try:
                validate_password(new_password, user=user)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        elif current_password:
            raise serializers.ValidationError(
                {"password": "Provide a new password when supplying the current password."}
            )
        return attrs

    def update(self, instance: User, validated_data: dict) -> User:
        """
        AI Annotation:
        - Purpose: Apply partial profile fields and optional password rotation.
        - Inputs: Validated serializer data; mutates user row.
        - Side effects: Persists user fields and hashed password when provided.
        """
        validated_data.pop("current_password", None)
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
