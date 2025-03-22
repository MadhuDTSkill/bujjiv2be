from rest_framework.generics import ListAPIView
from .models import LLMResponse
from .serializers import LLMResponseSerializer


class LLMResponseListView(ListAPIView):
    
    queryset = LLMResponse.objects.all()
    serializer_class = LLMResponseSerializer
    
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
    
    