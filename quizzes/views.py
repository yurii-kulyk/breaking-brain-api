import stripe

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action

from breaking_brain_api.paginators import ResultSetPagination
from quizzes.models import Quiz
from quizzes.utils import has_bought_quiz
from search.utils import search_quizzes
from quizzes.serializers import QuestionSerializer, QuizSerializer, BuyQuizSerializer


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

    toggle_favorites:
    Add/Remove quiz from favorites

    Add or Remove quiz from favorites if it is already there

    favorites:
    List of all favorites quizzes

    Get list of user's favorites quizzes
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
                data = search_quizzes(q, page, page_size).to_queryset()
                return Response(data=self.get_serializer_class()(data, many=True).data)
        except TypeError:
            pass
        return Response(data=[])

    @action(detail=True, methods=['GET'], serializer_class=QuestionSerializer,
            permission_classes=(IsAuthenticated,))
    def questions(self, request, pk=None, *args, **kwargs):
        quiz = get_object_or_404(Quiz, pk=pk)
        if not has_bought_quiz(quiz, request.user):
            raise PermissionDenied()
        return Response(data=self.serializer_class(quiz.questions.all(), many=True).data)

    @action(detail=True, methods=['POST'], url_name='toggle-favorites',
            url_path='toggle-favorites', permission_classes=(IsAuthenticated,))
    def toggle_favorites(self, request, pk=None, *args, **kwargs):
        obj = get_object_or_404(Quiz, pk=pk)
        if not has_bought_quiz(obj, request.user):
            raise PermissionDenied()
        if self.request.user.favorites.filter(pk=pk).exists():
            self.request.user.favorites.remove(obj)
            return Response(status=status.HTTP_204_NO_CONTENT)
        self.request.user.favorites.add(obj)
        return Response(data=self.get_serializer_class()(obj).data)

    @action(detail=False, methods=['GET'], permission_classes=(IsAuthenticated,))
    def favorites(self, request, *args, **kwargs):
        return Response(data=self.get_serializer_class()(request.user.favorites.all(),
                                                         many=True).data)

    @action(detail=False, methods=['GET'], url_path='public-key', url_name='public-key')
    def public_key(self, request, *args, **kwargs):
        return Response(data={
            'key': settings.STRIPE_PUBLIC_KEY
        })

    @action(detail=True, methods=['POST'], permission_classes=(IsAuthenticated,),
            serializer_class=BuyQuizSerializer)
    def buy(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = get_object_or_404(Quiz, pk=pk)
        if obj.is_free:
            return Response(data=QuizSerializer(obj).data)
        stripe.api_key = settings.STRIPE_PUBLIC_KEY
        payment_method_id = request.data['payment_method_id']
        confirmation = request.data['confirmation']
        if not confirmation:
            intent = stripe.PaymentIntent.create(
                payment_method=payment_method_id,
                amount=int(obj.price * 100),
                currency='USD',
                confirmation_method='manual',
                confirm=True,
            )
        else:
            intent = stripe.PaymentIntent.confirm(payment_method_id)
        return self.finalize_payment(intent, obj)

    def finalize_payment(self, intent, obj):
        if intent.status == 'requires_action' \
                and intent.next_action.type == 'use_stripe_sdk':
            return Response(data={
                'requires_action': True,
                'payment_intent_client_secret': intent.client_secret
            })
        elif intent.status == 'succeeded':
            self.request.user.bought_quizzes.add(obj)
            return Response(data=QuizSerializer(obj).data)
        return Response(data={
            'error': 'Invalid PaymentIntent status'
        }, status=400)
