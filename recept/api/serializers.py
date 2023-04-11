from djoser.serializers import UserSerializer, serializers
from django.contrib.auth.password_validation import validate_password
from users.models import User
from django.core import exceptions as django_exceptions


class NewUserSerializer(UserSerializer):
    password = serializers.CharField(write_only=True,
                                     style={'input_type': 'password'})
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'password')
    
    def validate_username(self, value):
        if value.lower() == "me":
            raise serializers.ValidationError("Username 'me' is not valid")
        return value

class ProfilesSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',)


class NewPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, obj):
        try:
            validate_password(obj['new_password'])
        except django_exceptions.ValidationError as e:
            raise serializers.ValidationError(
                {'new_password': list(e.messages)}
            )
        return super().validate(obj)

    def update(self, instance, validated_data):

        if (validated_data['current_password']
           == validated_data['new_password']):
            raise serializers.ValidationError(
                {'new_password': 'Change password'}
            )
        instance.set_password(validated_data['new_password'])
        instance.save()
        return validated_data
