import logging
from flask import Blueprint, render_template, request, jsonify, session, escape
from extensions import db
from models.user import User
from models.note import Note
from datetime import datetime
from sqlalchemy import text

notes_bp = Blueprint('notes', __name__, url_prefix='/apps/notes')

@notes_bp.route('/')
def notes():
    """Render notes page with all notes"""
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
    current_user = User.query.filter_by(username=session['user']).first()
    if not current_user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    user_id = request.args.get('user_id', type=int, default=current_user.id)

    all_notes = Note.query.filter_by(user_id=user_id).order_by(Note.created_at.desc()).all()
    print(f"Loading notes page - Found {len(all_notes)} notes for user {user_id}")

    return render_template('notes.html', notes=all_notes, current_user_id=current_user.id)

@notes_bp.route('/create', methods=['POST'])
def create_note():
    """Create a new note securely"""
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
    current_user = User.query.filter_by(username=session['user']).first()
    if not current_user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    title = request.form.get('title')
    content = request.form.get('content')

    if not title or not content:
        return jsonify({'success': False, 'error': 'Title and content are required'}), 400

    # Sanitize inputs to prevent XSS
    title = escape(title)
    content = escape(content)

    try:
        note = Note(
            title=title,
            content=content,
            created_at=datetime.now(),
            user_id=current_user.id
        )
        
        db.session.add(note)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Note created successfully',
            'note': {
                'id': note.id,
                'title': note.title,
                'content': note.content,
                'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': note.user_id
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@notes_bp.route('/search')
def search_notes():
    """Secure search for notes"""
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
    current_user = User.query.filter_by(username=session['user']).first()
    if not current_user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'success': False, 'notes': []})

    try:
        notes = Note.query.filter(
            Note.user_id == current_user.id,
            (Note.title.ilike(f"%{query}%")) | (Note.content.ilike(f"%{query}%"))
        ).all()

        return jsonify({
            'success': True,
            'notes': [
                {
                    'id': note.id,
                    'title': note.title,
                    'content': note.content,
                    'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': note.user_id
                }
                for note in notes
            ]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@notes_bp.route('/delete/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a note securely with access control"""
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
    current_user = User.query.filter_by(username=session['user']).first()
    if not current_user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    try:
        note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
        if not note:
            return jsonify({'success': False, 'error': 'Note not found or unauthorized'}), 403
        
        db.session.delete(note)
        db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@notes_bp.route('/debug')
def debug_database():
    """Secure debug route for admins"""
    if 'user' not in session or session.get('user') != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    try:
        users = User.query.all()
        notes = Note.query.all()

        return jsonify({
            'users': [{'id': u.id, 'username': u.username} for u in users],
            'notes': [{'id': n.id, 'title': n.title, 'user_id': n.user_id} for n in notes]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
