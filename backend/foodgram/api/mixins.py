from rest_framework import mixins, viewsets


class ListSubscriptionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Вазовый класс представления списка подписок."""
