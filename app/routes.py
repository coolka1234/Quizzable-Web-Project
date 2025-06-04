from flask import render_template, redirect, url_for, request
from app.models import db, User, Quiz, Question, Answer
from app.functions import generate_game_code
from datetime import datetime, timezone


def register_routes(app, google, session, g):

    @app.before_request
    def before_request():
        g.logged_in = google.authorized
        if g.logged_in:
            resp = google.get("/oauth2/v1/userinfo")
            if resp.ok:
                user_info = resp.json()
                name = user_info.get("name")
                email = user_info.get("email")
                session['name'] = name
                session['email'] = email

                user = User.query.filter_by(email=email).first()
                if not user:
                    user = User(
                        name=name,
                        email=email
                    )
                    db.session.add(user)
                    db.session.commit()
                g.user = user
            else:
                session.pop('name', None)
                session.pop('email', None)
                g.user = None
        else:
            session.pop('name', None)
            session.pop('email', None)
            g.user = None

    @app.route("/")
    def login_page():
        if g.logged_in:
            return redirect(url_for("index"))
        return render_template("login.html")

    @app.route("/index")
    def index():
        if not g.logged_in:
            return redirect(url_for("login_page"))
        
        quizzes = Quiz.query.all()
        return render_template("index.html", quizzes=quizzes)

    @app.route('/create/<quiz_id>', methods=['GET', 'POST'])
    def create(quiz_id=None):
        code = generate_game_code()
        quiz = Quiz.query.get(quiz_id) if quiz_id else None
        if quiz:
            questions = quiz.questions
            answers = {question.id: question.answers for question in questions}
        else:
            questions = []
            answers = {}
        return render_template('lobby_host.html', game_code=code, quiz_id=quiz_id , questions=questions, answers=answers)


    @app.route('/join')
    def join():
        return render_template('lobby_join.html')
    
    @app.route('/quiz/<int:quiz_id>')
    def quiz(quiz_id):
        quiz = Quiz.query.get_or_404(quiz_id)
        questions = quiz.questions
        if not questions:
            return render_template('no_questions.html', quiz=quiz)
        
        session['game_code'] = generate_game_code()
        return render_template('quiz.html', quiz=quiz, questions=questions, game_code=session['game_code'])
    

    @app.route('/question/<int:quiz_id>/<int:index>', methods=['GET', 'POST'])
    def question(quiz_id, index):
        quiz = Quiz.query.get_or_404(quiz_id)
        questions = quiz.questions

        if index < 0 or index >= len(questions):
            return redirect(url_for('index'))

        question = questions[index]

        if request.method == 'POST':
            selected = request.form.get('answer')
            # TODO: Save the selected answer to the database or session
            print(f"User selected answer ID: {selected}")

            return redirect(url_for('question', quiz_id=quiz_id, index=index + 1))

        return render_template('question.html',
                            question=question,
                            current_question_index=index,
                            total_questions=len(questions),
                            game_code=session.get('game_code', ''))


    @app.route('/submit_answer', methods=['POST'])
    def submit_answer():
        question_id = request.form.get('question_id')
        selected_answer_id = request.form.get('selected_answer')
        
        question = Question.query.get_or_404(question_id)
        quiz = Quiz.query.get_or_404(question.quiz_id)
        questions = quiz.questions
        current_index = [i for i, q in enumerate(questions) if q.id == int(question_id)][0]
        
        if current_index < len(questions) - 1:
            return redirect(url_for('question', quiz_id=quiz.id, index=current_index+1))
        else:
            return redirect(url_for('results', quiz_id=quiz.id))

    @app.route('/results/<int:quiz_id>')
    def results(quiz_id):
        # TODO
        return render_template('results.html', quiz_id=quiz_id)
    
    @app.route('/new_quiz', methods=['GET', 'POST'])
    def new_quiz():
        if request.method == 'POST':
            print(request.form)
            name = request.form.get("name")
            category = request.form.get("category")

            new_quiz = Quiz(name=name, category=category, user_id=g.user.id, created_at=datetime.now(timezone.utc))
            db.session.add(new_quiz)
            db.session.flush()

            index = 0
            while True:
                question_text = request.form.get(f"question_{index}")
                if not question_text:
                    break

                question = Question(text=question_text, quiz_id=new_quiz.id)
                db.session.add(question)
                db.session.flush()

                correct_answer = request.form.get(f"correct_answer_{index}")

                for i in range(1, 5):
                    answer_text = request.form.get(f"answer_{index}_{i}")
                    if not answer_text:
                        continue

                    label = chr(64 + i)
                    is_correct = str(i) == correct_answer

                    answer = Answer(
                        text=answer_text,
                        label=label,
                        is_correct=is_correct,
                        question_id=question.id
                    )
                    db.session.add(answer)

                index += 1
            print("Dodano pytania i odpowiedzi do bazy danych")
            db.session.commit()
            return redirect(url_for('index'))
        return render_template('new_quiz.html')

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login_page"))

    @app.route("/login/google/callback")
    def google_callback():
        if not google.authorized:
            return "Nie udało się zalogować przez Google.", 400
        return redirect(url_for("index"))
