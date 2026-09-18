from rest_framework.response import Response
from rest_framework.views import APIView

from kot7k.authentication.serializers.user import MeSerializer
from rest_framework.permissions import IsAuthenticated


class MeView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(
        self,
        request,
    ):
        data = MeSerializer(
            request.user,
        ).data

        return Response(
            data,
        )
