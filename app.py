import os
from flask import Flask, render_template, request, redirect, session, url_for
from database.db import get_connection
from services.import_service import parse_import_data, analyze_import, commit_import
from services.followup_service import get_due_actions, complete_action, handle_do_not_contact
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24) # Needed for session/flash if we use it, or just for preview storage

@app.route("/")
def dashboard():
    connection = get_connection()
    cursor = connection.cursor()

    total_creators = cursor.execute("SELECT COUNT(*) FROM creators").fetchone()[0]
    new_creators = cursor.execute("SELECT COUNT(*) FROM creators WHERE status = 'NEW'").fetchone()[0]
    interested_creators = cursor.execute("SELECT COUNT(*) FROM creators WHERE status = 'INTERESTED'").fetchone()[0]
    converted_creators = cursor.execute("SELECT COUNT(*) FROM creators WHERE status = 'CONVERTED'").fetchone()[0]
    
    # Calculate queue using followup service
    due_actions = get_due_actions(connection)
    
    # We aggregate counts from the service output
    pending_initial = sum(1 for a in due_actions['OVERDUE'] + due_actions['DUE_NOW'] if a['action_type'] == 'INITIAL_DM')
    pending_reactivation = sum(1 for a in due_actions['OVERDUE'] + due_actions['DUE_NOW'] if a['action_type'] == 'REACTIVATION')
    pending_followup = sum(1 for a in due_actions['OVERDUE'] + due_actions['DUE_NOW'] if a['action_type'] == 'FOLLOW_UP')

    connection.close()

    return render_template(
        "dashboard.html",
        total_creators=total_creators,
        new_creators=new_creators,
        interested_creators=interested_creators,
        converted_creators=converted_creators,
        pending_initial=pending_initial,
        pending_reactivation=pending_reactivation,
        pending_followup=pending_followup
    )

@app.route("/queue")
def action_queue():
    connection = get_connection()
    due_actions = get_due_actions(connection)
    connection.close()
    return render_template("queue.html", due_actions=due_actions)

@app.route("/action/complete/<int:action_id>", methods=["POST"])
def mark_action_complete(action_id):
    connection = get_connection()
    complete_action(action_id, connection)
    connection.close()
    return redirect(url_for('action_queue'))

@app.route("/creator/<int:creator_id>/dnc", methods=["POST"])
def mark_do_not_contact(creator_id):
    connection = get_connection()
    handle_do_not_contact(creator_id, connection)
    connection.close()
    return redirect(url_for('action_queue'))

@app.route("/creator/<int:creator_id>")
def creator_detail(creator_id):
    connection = get_connection()
    from services.conversation_service import get_creator_details, get_creator_messages
    creator = get_creator_details(creator_id, connection)
    if not creator:
        connection.close()
        return "Creator not found", 404
        
    messages = get_creator_messages(creator_id, connection)
    connection.close()
    
    return render_template("creator_detail.html", creator=creator, messages=messages)

@app.route("/creator/<int:creator_id>/message", methods=["POST"])
def add_manual_message(creator_id):
    direction = request.form.get("direction")
    text = request.form.get("message_text")
    is_ai = request.form.get("is_ai") == "on"
    
    # If it's AI generated mock for testing Phase 3, we set it to PENDING_REVIEW
    sent_status = 'PENDING_REVIEW' if is_ai and direction == 'OUTBOUND' else 'SENT'
    msg_type = 'AI_REPLY' if is_ai else 'MANUAL_REPLY'
    if direction == 'INBOUND':
        msg_type = 'INBOUND'
        sent_status = 'RECEIVED'
        
    connection = get_connection()
    from services.conversation_service import add_message
    add_message(creator_id, direction, text, msg_type, connection, ai_generated=is_ai, sent_status=sent_status)
    connection.close()
    
    return redirect(url_for('creator_detail', creator_id=creator_id))

@app.route("/message/approve/<int:message_id>", methods=["POST"])
def approve_message(message_id):
    creator_id = request.form.get("creator_id")
    connection = get_connection()
    from services.conversation_service import approve_ai_message
    approve_ai_message(message_id, connection)
    connection.close()
    return redirect(url_for('creator_detail', creator_id=creator_id))

@app.route("/message/reject/<int:message_id>", methods=["POST"])
def reject_message(message_id):
    creator_id = request.form.get("creator_id")
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    connection.commit()
    connection.close()
    return redirect(url_for('creator_detail', creator_id=creator_id))

@app.route("/message/edit/<int:message_id>", methods=["POST"])
def edit_message(message_id):
    creator_id = request.form.get("creator_id")
    new_text = request.form.get("message_text")
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE messages SET message_text = ? WHERE id = ?", (new_text, message_id))
    connection.commit()
    connection.close()
    return redirect(url_for('creator_detail', creator_id=creator_id))

@app.route("/message/regenerate/<int:message_id>", methods=["POST"])
def regenerate_message(message_id):
    creator_id = request.form.get("creator_id")
    connection = get_connection()
    cursor = connection.cursor()
    
    # Get creator and history
    cursor.execute("SELECT * FROM creators WHERE id = ?", (creator_id,))
    creator_data = dict(cursor.fetchone())
    
    # Get all messages EXCEPT the one we're regenerating, up to its creation time
    cursor.execute("SELECT * FROM messages WHERE creator_id = ? AND id != ? ORDER BY created_at ASC", (creator_id, message_id))
    messages_history = [dict(row) for row in cursor.fetchall()]
    
    from services.ai_service import generate_reply
    ai_response = generate_reply(creator_data, messages_history)
    
    if ai_response and ai_response.get('reply'):
        cursor.execute("UPDATE messages SET message_text = ? WHERE id = ?", (ai_response['reply'], message_id))
        connection.commit()
        
    connection.close()
    return redirect(url_for('creator_detail', creator_id=creator_id))

@app.route("/import", methods=["GET", "POST"])
def import_creators():
    if request.method == "POST":
        raw_text = request.form.get("csv_data", "")
        
        parsed_rows = parse_import_data(raw_text)
        
        connection = get_connection()
        preview = analyze_import(parsed_rows, connection)
        connection.close()
        
        # Store preview in session to commit later
        session['import_preview'] = preview
        
        return render_template("import_preview.html", preview=preview)

    return render_template("import.html")

@app.route("/import/commit", methods=["POST"])
def commit_import_route():
    preview = session.get('import_preview')
    if not preview:
        return redirect(url_for('import_creators'))
        
    connection = get_connection()
    success = commit_import(preview, connection)
    connection.close()
    
    # Clear session
    session.pop('import_preview', None)
    
    if success:
        return render_template("import_results.html", preview=preview)
    else:
        return "Error committing import", 500
@app.route("/settings/knowledge", methods=["GET", "POST"])
def settings_knowledge():
    from services.knowledge_service import load_knowledge_base, save_knowledge_base
    import json
    
    if request.method == "POST":
        kb_json_str = request.form.get("kb_json")
        try:
            kb_data = json.loads(kb_json_str)
            save_knowledge_base(kb_data)
            return redirect(url_for('settings_knowledge'))
        except Exception as e:
            kb_data = load_knowledge_base()
            return render_template("settings_knowledge.html", kb_json=json.dumps(kb_data, indent=2), error=str(e))
            
    kb_data = load_knowledge_base()
    kb_json_str = json.dumps(kb_data, indent=2)
    return render_template("settings_knowledge.html", kb_json=kb_json_str)
@app.route("/settings/integrations", methods=["GET"])
def settings_integrations():
    import os
    mode = os.environ.get('PROVIDER_MODE', 'MOCK').upper()
    has_token = bool(os.environ.get('META_ACCESS_TOKEN'))
    has_account_id = bool(os.environ.get('META_IG_ACCOUNT_ID'))
    
    return render_template(
        "settings_integrations.html",
        mode=mode,
        has_token=has_token,
        has_account_id=has_account_id
    )

@app.route("/creators")
def creators_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.*, 
               (SELECT COUNT(*) FROM messages m WHERE m.creator_id = c.id) as message_count
        FROM creators c 
        ORDER BY c.updated_at DESC
    ''')
    creators = cursor.fetchall()
    conn.close()
    return render_template("creators.html", creators=creators)

@app.route("/inbox")
def inbox():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Get creators that have messages, ordered by the latest message
    cursor.execute('''
        SELECT c.id, c.username, c.name, c.status,
               (SELECT m.message_text FROM messages m WHERE m.creator_id = c.id ORDER BY m.created_at DESC LIMIT 1) as last_message,
               (SELECT m.created_at FROM messages m WHERE m.creator_id = c.id ORDER BY m.created_at DESC LIMIT 1) as last_message_at,
               (SELECT m.direction FROM messages m WHERE m.creator_id = c.id ORDER BY m.created_at DESC LIMIT 1) as last_direction
        FROM creators c
        WHERE EXISTS (SELECT 1 FROM messages m WHERE m.creator_id = c.id)
        ORDER BY last_message_at DESC
    ''')
    conversations = cursor.fetchall()
    conn.close()
    return render_template("inbox.html", conversations=conversations)

if __name__ == "__main__":
    app.run(debug=True)