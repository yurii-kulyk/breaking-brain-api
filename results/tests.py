from mixer.backend.django import mixer
from django.urls import reverse

from breaking_brain_api.tests import BaseAPITest
from quizzes.models import Quiz, Question, Option
from results.models import QuizResult, QuestionResult, OptionResult


class TestQuizResult(BaseAPITest):

    def setUp(self):
        self.user = self.create_and_login()
        self.quiz = mixer.blend(Quiz)
        self.quiz_result = mixer.blend(QuizResult, quiz=self.quiz, user=self.user)
        self.question = mixer.blend(Question, quiz=self.quiz)
        self.right_option = mixer.blend(Option, question=self.question, is_right=True)
        self.wrong_option = mixer.blend(Option, question=self.question, is_right=False)

    def test_create_user_quiz_result(self):
        data = {
            'quiz': self.quiz.id
        }
        resp = self.client.post(reverse('quizzes-result-list'), data=data)
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(QuizResult.objects.filter(quiz=self.quiz, is_finished=False).exists())

    def test_create_user_quiz_result_when_logged_out(self):
        self.logout()
        data = {
            'quiz': self.quiz.id
        }
        resp = self.client.post(reverse('quizzes-result-list'), data=data)
        self.assertEqual(resp.status_code, 401)

    def test_create_question_result(self):
        data = {
            'question': self.question.id,
            'quiz': self.quiz_result.id,
            'options': [
                {
                    'option': self.right_option.id
                },
                {
                    'option': self.wrong_option.id
                }
            ]
        }
        resp = self.client.post(reverse('create-question-result'), data=data)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(QuestionResult.objects.count(), 1)
        self.assertEqual(OptionResult.objects.count(), 2)

    def test_create_question_from_one_quiz_to_another(self):
        another_quiz = mixer.blend(QuizResult)
        data = {
            'question': self.question.id,
            'quiz': another_quiz.id,
            'options': [
                {
                    'option': self.right_option.id
                },
                {
                    'option': self.wrong_option.id
                }
            ]
        }
        resp = self.client.post(reverse('create-question-result'), data=data)
        self.assertEqual(resp.status_code, 400)

    def test_get_list_of_results(self):
        resp = self.client.get(reverse('quizzes-result-list'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['results'][0]['id'], self.quiz_result.id)
        self.assertEqual(resp.data['results'][0]['result'], self.quiz_result.result)

    def test_get_list_of_results_when_logged_out(self):
        self.logout()
        mixer.blend(QuizResult, user=self.user)
        resp = self.client.get(reverse('quizzes-result-list'))
        self.assertEqual(resp.status_code, 401)

    def test_get_single_result(self):
        quiz_result = mixer.blend(QuizResult, user=self.user)
        resp = self.client.get(reverse('quizzes-result-detail', args=(quiz_result.id,)))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['id'], quiz_result.id)

    def test_finish_quiz_after_there_are_questions(self):
        data = {
            'question': self.question.id,
            'quiz': self.quiz_result.id,
            'options': [
                {
                    'option': self.right_option.id
                },
                {
                    'option': self.wrong_option.id
                }
            ]
        }
        self.client.post(reverse('create-question-result'), data=data)
        self.client.patch(reverse('quizzes-result-detail', args=(self.quiz_result.id,)),
                          data={
                              'is_finished': True
                          })
        self.quiz_result.refresh_from_db()
        self.assertEqual(self.quiz_result.result, 1)
        self.assertTrue(self.quiz_result.is_finished)

    def test_finish_quiz_without_questions(self):
        self.client.patch(reverse('quizzes-result-detail', args=(self.quiz_result.id,)),
                          data={
                              'is_finished': True
                          })
        self.quiz_result.refresh_from_db()
        self.assertEqual(self.quiz_result.result, 0)
        self.assertTrue(self.quiz_result.is_finished)

    def test_get_last_question(self):
        data = {
            'question': self.question.id,
            'quiz': self.quiz_result.id,
            'options': [
                {
                    'option': self.right_option.id
                },
                {
                    'option': self.wrong_option.id
                }
            ]
        }
        self.client.post(reverse('create-question-result'), data=data)
        resp = self.client.get(reverse('quizzes-result-last-question', args=(self.quiz_result.id,)))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['last_question_id'], self.question.id)

    def test_get_last_question_without_questions(self):
        resp = self.client.get(reverse('quizzes-result-last-question', args=(self.quiz_result.id,)))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.data['last_question_id'])
