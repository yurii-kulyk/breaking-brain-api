from django.conf import settings
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action

from breaking_brain_api.paginators import ResultSetPagination
from quizzes.models import Quiz
from quizzes.search import get_search_query
from quizzes.serializers import QuestionSerializer, QuizSerializer


class QuizViewSet(ReadOnlyModelViewSet):
    """
    list:
    Returns list of all quizzes

    Returns list of all quizzes

    retrieve:
    Return one quiz by its id

    Return one quiz by its id

    questions:
    Get list of questions for single quiz
    
    Get list of questions for single quiz
    """

    serializer_class = QuizSerializer
    permission_classes = (AllowAny,)
    pagination_class = ResultSetPagination

    def get_queryset(self):
        return Quiz.objects.all().prefetch_related('tags', 'lessons')

    @action(detail=False, methods=["GET"])
    def search(self, request, *args, **kwargs):
        q = request.GET.get('q')
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', settings.PAGE_SIZE))
            if q:
                data = get_search_query(q, page, page_size).to_queryset()
                return Response(data=self.get_serializer_class()(data, many=True).data)
        except TypeError:
            pass
        return Response(data=[])

    @action(detail=True, methods=['GET'], serializer_class=QuestionSerializer,
            permission_classes=(IsAuthenticated,))
    def questions(self, request, pk=None, *args, **kwargs):
        quiz = get_object_or_404(Quiz, pk=pk)
        return Response(data=self.serializer_class(quiz.questions.all(), many=True).data)
