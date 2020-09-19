import canvasapi
import datetime
from typing import List, Callable
from .group import Group


class KudoPointGivingQuiz:
    def __init__(self, user: canvasapi.user.User,
                 group: canvasapi.group.Group,
                 assignment_group: canvasapi.assignment.AssignmentGroup,
                 number_of_kudo_points,
                 due_date: datetime.datetime,
                 unlock_date: datetime.datetime,
                 lock_date: datetime.datetime):
        self.user = user
        self.group = Group(group)
        self.assignment_group = assignment_group
        self.unlock_date = unlock_date
        self.due_date = due_date
        self.lock_date = lock_date
        self.number_of_kudo_points = number_of_kudo_points

        self.quiz_info = self._create_quiz_info()
        self.assignment_info = self._create_assignment_info()
        self.quiz_questions = self._create_quiz_questions()

    def _create_quiz_info(self) -> dict:
        return {
            'title': f"{self.user.name}'s Kudo Point Givings for {self.group.name}",
            'quiz_type': 'assignment',
            'assignment_group_id': self.assignment_group.id,
            'allowed_attempts': 10,
            'scoring_policy': 'keep_latest',
            'published': False,
            'show_correct_answers': False,
            'only_visible_to_overrides': True,
        }

    def _create_assignment_info(self) -> dict:
        date_info = {
            'student_ids': [self.user.id],
            'title': f'Override for {self.user.name}',
            'due_at': self.due_date.isoformat(),
            'unlock_at': self.unlock_date.isoformat(),
            'lock_at': self.lock_date.isoformat()
        }

        return {
            # setting grading_type to not_graded breaks the association between Quiz and Assignment
            # not sure if this is a bug on Canvas's end or what so leaving it out for now.
            # 'grading_type': 'not_graded',
            'omit_from_final_grade': True,
            'only_visible_to_overrides': True,
            'assignment_overrides': [date_info],
            'published': True
        }

    def _create_quiz_questions(self) -> List[dict]:
        answers = self._create_answers()
        return [
            {
                'question_name': f'Kudo Point {point}',
                'question_text': 'Who do you want to give this Kudo Point to?',
                'question_type': 'multiple_choice_question',
                'answers': answers,
                'points_possible': 1
            } for point in range(1, self.number_of_kudo_points + 1)
        ]

    def _create_answers(self) -> List[dict]:
        answers = [
            {
                'answer_html': member.name,
                'answer_text': f'{member.id}',
                'answer_weight': 1

            } for member in self.group.members if self.user.id != member.id
        ]
        answers.append({
            'answer_html': 'I do not want to give this Kudo Point to anyone.',
            'answer_weight': 1
        })
        return answers

    def upload_to_canvas(self, course: canvasapi.course.Course) -> None:
        canvas_quiz = course.create_quiz(self.quiz_info)
        for question in self.quiz_questions:
            canvas_quiz.create_question(question=question)
        canvas_assignment = course.get_assignment(canvas_quiz.assignment_id)
        edited_canvas_assignment = canvas_assignment.edit(assignment=self.assignment_info)
        # edited_quiz = canvas_quiz.edit(quiz={'published': True})
        second_assignment = course.get_assignment(canvas_quiz.assignment_id)
        pass

    @staticmethod
    def create_kudo_point_giving_quiz_for_group_category(course: canvasapi.course.Course,
                                                         group_category: canvasapi.group.GroupCategory,
                                                         assignment_group: canvasapi.assignment.AssignmentGroup,
                                                         number_of_kudo_points,
                                                         due_date: datetime.datetime,
                                                         unlock_date: datetime.datetime,
                                                         lock_date: datetime.datetime,
                                                         on_group_start: Callable[[Group], None] = None,
                                                         on_group_end: Callable[[Group], None] = None,
                                                         on_user_start: Callable[
                                                             [canvasapi.user.User, Group], None] = None,
                                                         on_user_end: Callable[
                                                             [canvasapi.user.User, Group], None] = None
                                                         ):
        for group in group_category.get_groups():
            if on_group_start is not None:
                on_group_start(group)
            for user in group.get_users():
                if on_user_start is not None:
                    on_user_start(user, group)
                quiz = KudoPointGivingQuiz(user, group, assignment_group,
                                           number_of_kudo_points,
                                           due_date,
                                           unlock_date,
                                           lock_date)

                quiz.upload_to_canvas(course)
                if on_user_end is not None:
                    on_user_end(user, group)
            if on_group_end is not None:
                on_group_end(group)
