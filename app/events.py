from flask_socketio import emit, join_room, leave_room
from . import socketio, db
from .models import Flag, QuizQuestion, QuizResponse, Session
from flask import request, session

@socketio.on('join')
def on_join(data):
    room = data['session_id']
    join_room(room)
    # Send existing flags to the user who just joined
    flags = Flag.query.filter_by(session_id=room).all()
    flags_data = [{
        'id': f.id,
        'region_id': f.region_id,
        'x': f.x,
        'y': f.y,
        'text_content': f.text_content,
        'file_path': f.file_path,
        'thumbnail_path': f.thumbnail_path,
        'author_name': f.author_name,
        'client_id': f.client_id,
        'post_type': f.post_type
    } for f in flags]
    emit('load_flags', flags_data, to=request.sid)

    # Quiz Questions
    questions = QuizQuestion.query.filter_by(session_id=room).order_by(QuizQuestion.index).all()
    q_data = [{
        'id': q.id,
        'index': q.index,
        'q_type': q.q_type,
        'question': q.question,
        'options': q.options,
        'correct_answer': q.correct_answer
    } for q in questions]
    emit('load_quiz_questions', q_data, to=request.sid)

    # Participant's own responses
    client_id = request.args.get('client_id') # Note: client_id might need to be sent in join or inferred
    # Actually, the client handles its own client_id. We can filter by client_id if provided.
    
    # Send all responses to Admin
    if session.get('admin_logged_in'):
        responses = QuizResponse.query.filter_by(session_id=room).all()
        r_data = [{
            'id': r.id,
            'question_id': r.question_id,
            'client_id': r.client_id,
            'author_name': r.author_name,
            'response': r.response,
            'is_correct': r.is_correct
        } for r in responses]
        emit('load_all_responses', r_data, to=request.sid)
    else:
        # If we had a way to get client_id here, we'd filter. 
        # For now, let the client emit a 'get_my_responses' event if needed, 
        # or we just rely on local state since it's a live session.
        pass

@socketio.on('leave')
def on_leave(data):
    room = data['session_id']
    leave_room(room)

@socketio.on('add_flag')
def on_add_flag(data):
    session_id = data.get('session_id')
    region_id = data.get('region_id')
    x = data.get('x')
    y = data.get('y')
    text_content = data.get('text_content')
    file_path = data.get('file_path')
    thumbnail_path = data.get('thumbnail_path')
    author_name = data.get('author_name', 'Participant')
    client_id = data.get('client_id')
    post_type = data.get('post_type', 'normal')
    
    # Permission check: Only admin can create notice or objective
    is_admin = session.get('admin_logged_in', False)
    if not is_admin and post_type in ['notice', 'objective']:
        post_type = 'normal'

    new_flag = Flag(
        session_id=session_id,
        region_id=region_id,
        x=x,
        y=y,
        text_content=text_content,
        file_path=file_path,
        thumbnail_path=thumbnail_path,
        author_name=author_name,
        client_id=client_id,
        post_type=post_type
    )
    db.session.add(new_flag)
    db.session.commit()

    flag_data = {
        'id': new_flag.id,
        'region_id': new_flag.region_id,
        'x': new_flag.x,
        'y': new_flag.y,
        'text_content': new_flag.text_content,
        'file_path': new_flag.file_path,
        'thumbnail_path': new_flag.thumbnail_path,
        'author_name': new_flag.author_name,
        'client_id': new_flag.client_id,
        'post_type': new_flag.post_type
    }
    
    # Broadcast to everyone in the room (session)
    emit('new_flag', flag_data, to=session_id)

@socketio.on('edit_flag')
def on_edit_flag(data):
    session_id = data.get('session_id')
    flag_id = data.get('flag_id')
    
    flag = Flag.query.get(flag_id)
    if flag:
        # Authorization check: Admin or the person who created the flag
        is_admin = session.get('admin_logged_in', False)
        requester_client_id = data.get('client_id')
        
        # Permission check:
        # 1. If it's a notice or objective, ONLY admin can edit.
        # 2. Otherwise, admin OR the owner can edit.
        is_special_type = flag.post_type in ['notice', 'objective']
        
        if is_special_type:
            if not is_admin:
                print(f"Unauthorized edit attempt for special type {flag.post_type} by client {requester_client_id}")
                return
        else:
            if not is_admin and flag.client_id != requester_client_id:
                print(f"Unauthorized edit attempt for flag {flag_id} by client {requester_client_id}")
                return
            
        flag.text_content = data.get('text_content', flag.text_content)
        flag.post_type = data.get('post_type', flag.post_type)
        
        # If new file is uploaded, update paths
        if 'file_path' in data:
            flag.file_path = data.get('file_path')
            flag.thumbnail_path = data.get('thumbnail_path')
            
        db.session.commit()
        
        flag_data = {
            'id': flag.id,
            'region_id': flag.region_id,
            'x': flag.x,
            'y': flag.y,
            'text_content': flag.text_content,
            'file_path': flag.file_path,
            'thumbnail_path': flag.thumbnail_path,
            'author_name': flag.author_name,
            'client_id': flag.client_id,
            'post_type': flag.post_type
        }
        
        emit('flag_edited', flag_data, to=session_id)

@socketio.on('delete_flag')
def on_delete_flag(data):
    session_id = data.get('session_id')
    flag_id = data.get('flag_id')
    
    try:
        flag = Flag.query.get(int(flag_id))
    except (TypeError, ValueError):
        flag = Flag.query.get(flag_id)
        
    if flag:
        # Permission check:
        # 1. If it's a notice or objective, ONLY admin can delete.
        # 2. Otherwise, admin OR the owner can delete.
        is_admin = session.get('admin_logged_in', False)
        requester_client_id = data.get('client_id')
        
        is_special_type = flag.post_type in ['notice', 'objective']
        
        if is_special_type:
            if not is_admin:
                print(f"Unauthorized delete attempt for special type {flag.post_type} by client {requester_client_id}")
                return
        else:
            if not is_admin and flag.client_id != requester_client_id:
                print(f"Unauthorized delete attempt for flag {flag_id} by client {requester_client_id}")
                return
 
        db.session.delete(flag)
        db.session.commit()
        
        emit('flag_deleted', {'id': flag_id, 'session_id': session_id}, to=session_id)
        
@socketio.on('draw_data')
def on_draw_data(data):
    session_id = data.get('session_id')
    # Broadcast drawing data to everyone else in the room
    emit('draw_data', data, to=session_id, include_self=False)

@socketio.on('clear_canvas')
def on_clear_canvas(data):
    session_id = data.get('session_id')
    # Authorization check for clearing canvas (admin only)
    if session.get('admin_logged_in'):
        emit('clear_canvas', {}, to=session_id)

# --- ClassQuiz Events ---

@socketio.on('add_quiz_question')
def on_add_quiz_question(data):
    if not session.get('admin_logged_in'): return
    
    session_id = data.get('session_id')
    new_q = QuizQuestion(
        session_id=session_id,
        index=data.get('index'),
        q_type=data.get('q_type'),
        question=data.get('question'),
        options=data.get('options'),
        correct_answer=data.get('correct_answer')
    )
    db.session.add(new_q)
    db.session.commit()
    
    broadcast_questions(session_id)

@socketio.on('bulk_add_questions')
def on_bulk_add_questions(data):
    if not session.get('admin_logged_in'): return
    session_id = data.get('session_id')
    new_questions = data.get('questions', [])
    
    for q in new_questions:
        new_q = QuizQuestion(
            session_id=session_id,
            index=q.get('index'),
            q_type=q.get('q_type'),
            question=q.get('question'),
            options=q.get('options'),
            correct_answer=q.get('correct_answer')
        )
        db.session.add(new_q)
    
    db.session.commit()
    broadcast_questions(session_id)

@socketio.on('edit_quiz_question')
def on_edit_quiz_question(data):
    if not session.get('admin_logged_in'): return
    session_id = data.get('session_id')
    q_id = data.get('question_id')
    
    q = QuizQuestion.query.get(q_id)
    if q:
        q.index = data.get('index', q.index)
        q.q_type = data.get('q_type', q.q_type)
        q.question = data.get('question', q.question)
        q.options = data.get('options', q.options)
        q.correct_answer = data.get('correct_answer', q.correct_answer)
        db.session.commit()
        broadcast_questions(session_id)

@socketio.on('delete_quiz_question')
def on_delete_quiz_question(data):
    if not session.get('admin_logged_in'): return
    session_id = data.get('session_id')
    q_id = data.get('question_id')
    
    q = QuizQuestion.query.get(q_id)
    if q:
        db.session.delete(q)
        db.session.commit()
        broadcast_questions(session_id)

@socketio.on('submit_quiz_response')
def on_submit_quiz_response(data):
    session_id = data.get('session_id')
    q_id = data.get('question_id')
    client_id = data.get('client_id')
    response_text = data.get('response')
    author_name = data.get('author_name', 'Participant')

    # Check for existing response by this client for this question
    resp = QuizResponse.query.filter_by(session_id=session_id, question_id=q_id, client_id=client_id).first()
    
    # Grading logic
    q = QuizQuestion.query.get(q_id)
    is_correct = False
    if q:
        if q.q_type == 'long':
            is_correct = bool(response_text and response_text.strip())
        elif q.q_type in ['choice', 'short']:
            if q.correct_answer:
                is_correct = (str(response_text).strip().lower() == str(q.correct_answer).strip().lower())

    if resp:
        resp.response = response_text
        resp.is_correct = is_correct
        resp.author_name = author_name
    else:
        resp = QuizResponse(
            session_id=session_id,
            question_id=q_id,
            client_id=client_id,
            author_name=author_name,
            response=response_text,
            is_correct=is_correct
        )
        db.session.add(resp)
    
    db.session.commit()
    
    resp_data = {
        'id': resp.id,
        'question_id': resp.question_id,
        'client_id': resp.client_id,
        'author_name': resp.author_name,
        'response': resp.response,
        'is_correct': resp.is_correct
    }
    
    # Notify admin
    emit('new_response', resp_data, to=session_id)
    # Notify the student specifically about their own response (for live grading)
    emit('my_response_update', resp_data, to=request.sid)

@socketio.on('get_admin_results')
def on_get_admin_results(data):
    if not session.get('admin_logged_in'): return
    session_id = data.get('session_id')
    
    questions = QuizQuestion.query.filter_by(session_id=session_id).all()
    responses = QuizResponse.query.filter_by(session_id=session_id).all()
    
    q_data = [{'id': q.id, 'index': q.index, 'q_type': q.q_type, 'question': q.question, 'correct_answer': q.correct_answer} for q in questions]
    r_data = [{'id': r.id, 'question_id': r.question_id, 'client_id': r.client_id, 'author_name': r.author_name, 'response': r.response, 'is_correct': r.is_correct} for r in responses]
    
    emit('admin_results_data', {
        'session_id': session_id,
        'questions': q_data,
        'responses': r_data
    }, to=request.sid)

def broadcast_questions(session_id):
    questions = QuizQuestion.query.filter_by(session_id=session_id).order_by(QuizQuestion.index).all()
    q_data = [{
        'id': q.id,
        'index': q.index,
        'q_type': q.q_type,
        'question': q.question,
        'options': q.options,
        'correct_answer': q.correct_answer
    } for q in questions]
    emit('quiz_update', q_data, to=session_id)
