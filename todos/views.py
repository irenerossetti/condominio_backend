# todos/views.py
from rest_framework import generics, permissions
from .models import Todo
from .serializers import TodoSerializer

class TodoListCreate(generics.ListCreateAPIView):
    queryset = Todo.objects.all().order_by("-id")
    serializer_class = TodoSerializer
    permission_classes = [permissions.AllowAny]

class TodoDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer
    permission_classes = [permissions.AllowAny]

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        data = request.data
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {}

        identifier = (data.get("email") or data.get("username") or "").strip()
        password   = (data.get("password") or "").strip()