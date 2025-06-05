from flask import render_template, redirect, url_for, request, flash, abort
from app.models import db, User, Quiz, Question, Answer, UserAnswer
from app.functions import generate_game_code
from datetime import datetime, timezone
from time import time
import uuid  


def register_routes(app, google, session, g):

    @app.before_request
    def before_request():
        if 'tab_id' not in session:
            session['tab_id'] = str(uuid.uuid4())
        
        g.tab_id = session.get('tab_id')
        
        tab_key = f"logged_in_{g.tab_id}"
        g.logged_in = session.get(tab_key, False) and google.authorized
        
        if google.authorized:
            resp = google.get("/oauth2/v1/userinfo")
            if resp.ok:
                user_info = resp.json()
                name = user_info.get("name")
                email = user_info.get("email")
                
                session[f'name_{g.tab_id}'] = name
                session[f'email_{g.tab_id}'] = email

                session[tab_key] = True

                user = User.query.filter_by(email=email).first()
                if not user:
                    user = User(
                        name=name,
                        email=email,
                        is_admin=True
                    )
                    db.session.add(user)
                    db.session.commit()
                g.user = user
            else:
                session.pop(f'name_{g.tab_id}', None)
                session.pop(f'email_{g.tab_id}', None)
                session[tab_key] = False
                g.user = None
        else:
            session.pop(f'name_{g.tab_id}', None)
            session.pop(f'email_{g.tab_id}', None)
            session[tab_key] = False
            g.user = None

    @app.route("/admin")
    def admin():
        if not g.logged_in:
            return redirect(url_for("login_page"))
        
        if not hasattr(g, 'user') or not g.user or not g.user.is_admin:
            abort(403)
            
        users = User.query.all()
        quizzes = Quiz.query.all()
        questions = Question.query.all()
        answers = Answer.query.all()
        user_answers = UserAnswer.query.all()
        
        return render_template("admin.html", 
                               users=users, 
                               quizzes=quizzes, 
                               questions=questions,
                               answers=answers,
                               user_answers=user_answers)
    
    @app.route("/admin/user/<int:user_id>/toggle_admin", methods=["POST"])
    def toggle_admin(user_id):
        if not g.logged_in or not hasattr(g, 'user') or not g.user or not g.user.is_admin:
            abort(403)
            
        user = User.query.get_or_404(user_id)
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f"Admin status for {user.name} has been {'enabled' if user.is_admin else 'disabled'}")
        return redirect(url_for("admin"))
        
    @app.route("/admin/delete/<string:model_type>/<int:item_id>", methods=["POST"])
    def delete_item(model_type, item_id):
        if not g.logged_in or not hasattr(g, 'user') or not g.user or not g.user.is_admin:
            abort(403)
            
        model_map = {
            "user": User,
            "quiz": Quiz,
            "question": Question,
            "answer": Answer,
            "user_answer": UserAnswer
        }
        
        if model_type not in model_map:
            abort(404)
            
        item = model_map[model_type].query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        flash(f"{model_type.capitalize()} has been deleted")
        return redirect(url_for("admin"))

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

        print(len(questions), index)

        if index < len(questions):
            question = questions[index]
        else:
            question = questions[-1]

        player_name = request.form.get('player_name') or request.args.get('player_name')
        if player_name:
            session['player_name'] = player_name
        else:
            player_name = session.get('player_name', '')

        if request.method == 'POST':
            selected = request.form.get('answer')
            
            if selected:
                user = User.query.filter_by(name=player_name).first()
                if not user and player_name:
                    user = User(
                        name=player_name,
                        email=f"temp_{uuid.uuid4()}@example.com" 
                    )
                    db.session.add(user)
                    db.session.commit()
                
                user_id = user.id if user else g.user.id if hasattr(g, 'user') and g.user else None
                
                if user_id:
                    user_answer = UserAnswer(
                        user_id=user_id,
                        question_id=question.id,
                        answer_id=selected,
                        game_code=session.get('game_code', '')
                    )
                    db.session.add(user_answer)
                    db.session.commit()

            next_index = index + 1
            if next_index <= len(questions):
                return redirect(url_for('question', quiz_id=quiz_id, index=index, player_name=player_name, start_time=time()))
            else:
                return redirect(url_for('results', quiz_id=quiz_id))

        return render_template('question.html',
                            question=question,
                            current_question_index=index,
                            total_questions=len(questions),
                            game_code=session.get('game_code', ''))


    @app.route('/submit_answer', methods=['POST'])
    def submit_answer():
        question_id = request.form.get('question_id')
        selected_answer_id = request.form.get('selected_answer')
        player_name = request.form.get('player_name')
        
        if player_name:
            session['player_name'] = player_name
        else:
            player_name = session.get('player_name', '')
        
        if selected_answer_id:
            user = User.query.filter_by(name=player_name).first()
            if not user and player_name:
                user = User(
                    name=player_name,
                    email=f"temp_{uuid.uuid4()}@example.com"  
                )
                db.session.add(user)
                db.session.commit()
            
            user_id = user.id if user else g.user.id if hasattr(g, 'user') and g.user else None
            
            if user_id:
                user_answer = UserAnswer(
                    user_id=user_id,
                    question_id=question_id,
                    answer_id=selected_answer_id,
                    game_code=session.get('game_code', '')
                )
                db.session.add(user_answer)
                db.session.commit()
        
        question = Question.query.get_or_404(question_id)
        quiz = Quiz.query.get_or_404(question.quiz_id)
        questions = quiz.questions
        current_index = [i for i, q in enumerate(questions) if q.id == int(question_id)][0] #type: ignore
        
        if current_index < len(questions) - 1:
            return redirect(url_for('question', quiz_id=quiz.id, index=current_index+1, player_name=player_name))
        else:
            return redirect(url_for('results', quiz_id=quiz.id))

    @app.route('/results/<int:quiz_id>')
    def results(quiz_id):
        quiz = Quiz.query.get_or_404(quiz_id)
        game_code = session.get('game_code', '')
        
        questions = quiz.questions
        
        user_scores = {}
        
        all_answers = (UserAnswer.query
                      .join(Question, UserAnswer.question_id == Question.id)
                      .filter(Question.quiz_id == quiz_id, 
                              UserAnswer.game_code == game_code)
                      .all())
        
        for answer in all_answers:
            if answer.user_id not in user_scores:
                user = User.query.get(answer.user_id)
                user_scores[answer.user_id] = {
                    'user': user,
                    'correct': 0,
                    'total': 0
                }
            
            selected_answer = Answer.query.get(answer.answer_id)
            if selected_answer and selected_answer.is_correct:
                user_scores[answer.user_id]['correct'] += 1
            user_scores[answer.user_id]['total'] += 1
            
        for user_id in user_scores:
            score = user_scores[user_id]
            if score['total'] > 0:
                score['percentage'] = round((score['correct'] / score['total']) * 100)
            else:
                score['percentage'] = 0
        
        sorted_scores = sorted(
            user_scores.values(), 
            key=lambda x: (x['percentage'], x['correct']), 
            reverse=True
        )
        
        return render_template('results.html', 
                              quiz=quiz, 
                              scores=sorted_scores, 
                              total_questions=len(questions))

    
    @app.route('/new_quiz', methods=['GET', 'POST'])
    def new_quiz():
        if request.method == 'POST':
            print(request.form)
            name = request.form.get("name")
            category = request.form.get("category")

            new_quiz = Quiz(name=name, category=category, user_id=g.user.id, created_at=datetime.now(timezone.utc)) # type: ignore
            db.session.add(new_quiz)
            db.session.flush()

            index = 0
            while True:
                question_text = request.form.get(f"question_{index}")
                if not question_text:
                    break

                question = Question(text=question_text, quiz_id=new_quiz.id) # type: ignore
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
                        text=answer_text, # type: ignore
                        label=label, # type: ignore
                        is_correct=is_correct, # type: ignore
                        question_id=question.id # type: ignore
                    )
                    db.session.add(answer)

                index += 1
            print("Dodano pytania i odpowiedzi do bazy danych")
            db.session.commit()
            return redirect(url_for('index'))
        return render_template('new_quiz.html')
    
    @app.route("/host_waiting/<int:quiz_id>/<string:game_code>")
    def host_waiting(game_code=None, quiz_id=None):
        if not g.logged_in:
            return redirect(url_for("login_page"))
        
        
        if not game_code or not quiz_id:
            print("Missing game code or quiz ID")
            flash("Missing game code or quiz ID")
            return redirect(url_for("index"))
        
        quiz = Quiz.query.get_or_404(quiz_id)
        
        return render_template("host_waiting.html", 
                               game_code=game_code, 
                               quiz_id=quiz_id,
                               quiz=quiz)

    @app.route("/logout")
    def logout():
        if 'tab_id' in session:
            tab_id = session['tab_id']
            session.pop(f'name_{tab_id}', None)
            session.pop(f'email_{tab_id}', None)
            session.pop(f'logged_in_{tab_id}', None)
        return redirect(url_for("login_page"))

    @app.route("/login/google/callback")
    def google_callback():
        if not google.authorized:
            return "Nie udało się zalogować przez Google.", 400
        return redirect(url_for("index"))
