from mixer.backend.django import mixer
from django.urls import reverse

from breaking_brain_api.tests import BaseAPITest
from quizzes.models import Quiz, Question, Option, Lesson


class QuizTest(BaseAPITest):

    def setUp(self):
        self.quiz = mixer.blend(Quiz)
        self.question = mixer.blend(Question, quiz=self.quiz)
        self.option = mixer.blend(Option, question=self.question)
        self.lesson = mixer.blend(Lesson, quiz=self.quiz)
        self.user = self.create_and_login()

    def test_get_list_of_quizes(self):
        resp = self.client.get(reverse('quizzes-list'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['id'], self.quiz.id)
        self.assertEqual(resp.data['results'][0]['title'], self.quiz.title)
        self.assertEqual(resp.data['results'][0]['lessons'][0]['id'], self.lesson.id)
        self.assertEqual(resp.data['results'][0]['lessons'][0]['title'], self.lesson.title)

    def test_get_list_of_quizes_when_logged_out(self):
        self.logout()
        resp = self.client.get(reverse('quizzes-list'))
        self.assertEqual(resp.status_code, 200)

    def test_get_single_quiz(self):
        resp = self.client.get(reverse('quizzes-detail', args=(self.quiz.id,)))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['id'], self.quiz.id)
        self.assertEqual(resp.data['title'], self.quiz.title)
        self.assertEqual(resp.data['lessons'][0]['id'],
                         self.lesson.id)

    def test_get_single_quiz_when_logout(self):
        self.logout()
        resp = self.client.get(reverse('quizzes-detail', args=(self.quiz.id,)))
        self.assertEqual(resp.status_code, 200)

    def test_get_non_existed_quiz(self):
        resp = self.client.get(reverse('quizzes-detail', args=(123123,)))
        self.assertEqual(resp.status_code, 404)
    
    def test_get_questions_from_quiz(self):
        resp = self.client.get(reverse('quizzes-questions', args=(self.quiz.id,)))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data[0]['id'], self.question.id)
        self.assertEqual(resp.data[0]['options'][0]['id'], self.option.id)
        self.assertEqual(len(resp.data), 1)
    
    def test_get_quesionts_from_non_existed_quiz(self):
        resp = self.client.get(reverse('quizzes-questions', args=(12311,)))
        self.assertEqual(resp.status_code, 404)

    def test_get_questions_from_quiz_when_logout(self):
        self.logout()
        resp = self.client.get(reverse('quizzes-questions', args=(self.quiz.id,)))
        self.assertEqual(resp.status_code, 401)
