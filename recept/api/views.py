from django.shortcuts import get_object_or_404
from rest_framework.response import Response, responses
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from users.models import User
from .serializers import NewPasswordSerializer, NewUserSerializer, ProfilesSerializer, UserTokenSerializer
from .permissions import Admin, AdminOrUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.authtoken.models import Token




class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProfilesSerializer
        return NewUserSerializer
    
    def get_permissions(self):
        self.permission_classes = [permissions.AllowAny]
        if self.request.method == "GET":
            self.permission_classes = [AdminOrUser]
        return super(UserViewSet, self).get_permissions()

    @action(
        methods=[
            "get",
            "post",
        ],
        detail=False,
    )
    def profile(self, request):
        user = request.user
        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == "POST":
            serializer = NewUserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'],
            pagination_class=None,
            permission_classes=(permissions.IsAuthenticated,))
    def me(self, request):
        serializer = ProfilesSerializer(request.user)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'],
            permission_classes=(permissions.IsAuthenticated,))
    def set_password(self, request):
        serializer = NewPasswordSerializer(request.user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response({'detail': 'New password save'},
                        status=status.HTTP_204_NO_CONTENT)

    


class UserTokenViewSet(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)

    def token(self, request):
        serializer = UserTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_form = serializer.initial_data.get('email')
        user_form_pas = serializer.initial_data.get('password')
        user = get_object_or_404(User, email=user_form, password=user_form_pas)
        token = AccessToken.for_user(user)
       # token = Token.objects.create(user=user)
        return Response({"token": str(token)}, status=status.HTTP_200_OK)

class UserProfile(viewsets.ModelViewSet):
    lookup_field = "username"
    queryset = User.objects.all()
    serializer_class = ProfilesSerializer
    permission_classes = (Admin,)

    @action(
        methods=[
            "get",
            "patch",
        ],
        detail=False,
        url_path="me",
        permission_classes=(permissions.IsAuthenticated,),
        serializer_class=ProfilesSerializer,
    )
    def profile(self, request):
        user = request.user
        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
