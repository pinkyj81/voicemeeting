from flask import Flask, jsonify, render_template, request
from deep_translator import GoogleTranslator
import os
import re

import pyodbc

app = Flask(__name__)


def get_db_connection():
    conn_str = (
        f"DRIVER={{{os.getenv('DB_DRIVER', 'ODBC Driver 18 for SQL Server')}}};"
        f"SERVER={os.getenv('DB_SERVER', 'ms1901.gabiadb.com')};"
        f"DATABASE={os.getenv('DB_DATABASE', 'yujincast')};"
        f"UID={os.getenv('DB_USERNAME', 'pinkyj81')};"
        f"PWD={os.getenv('DB_PASSWORD', 'zoskek38!!')};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)


def normalize_user_name(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return "참가자"
    return text[:40]


@app.route("/")
def lobby():
    return render_template("rooms.html")


@app.route("/meeting/<room_code>")
def meeting_page(room_code):
    if not re.fullmatch(r"\d{6}", room_code or ""):
        return "invalid room code", 400

    room_name = ""
    user_name = normalize_user_name(request.args.get("name", ""))
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT TOP 1 RoomName
                FROM dbo.MeetingRooms
                WHERE RoomCode = ? AND IsActive = 1
                ORDER BY RoomID DESC
                """,
                room_code,
            )
            row = cursor.fetchone()
            if not row:
                return "room not found", 404
            room_name = row[0] or ""
    except Exception as exc:
        return f"database error: {exc}", 500

    return render_template(
        "index.html",
        room_code=room_code,
        room_name=room_name,
        user_name=user_name,
    )


@app.route("/iphone")
def iphone():
    return render_template("iphone.html")


@app.route("/meeting/<room_code>/iphone")
def iphone_room(room_code):
    if not re.fullmatch(r"\d{6}", room_code or ""):
        return "invalid room code", 400
    user_name = normalize_user_name(request.args.get("name", ""))
    return render_template("iphone.html", room_code=room_code, user_name=user_name)


@app.get("/api/rooms")
def list_rooms():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT TOP 100
                    RoomCode,
                    RoomName,
                    ISNULL(CreatedBy, '') AS CreatedBy,
                    CONVERT(VARCHAR(19), SWITCHOFFSET(CreatedAt, '+09:00'), 120) AS CreatedAt
                FROM dbo.MeetingRooms
                WHERE IsActive = 1
                ORDER BY RoomID DESC
                """
            )
            rows = cursor.fetchall()

        rooms = [
            {
                "room_code": row[0],
                "room_name": row[1],
                "created_by": row[2],
                "created_at": row[3],
            }
            for row in rows
        ]
        return jsonify({"rooms": rooms})
    except Exception as exc:
        return jsonify({"error": f"failed to load rooms: {exc}"}), 500


@app.get("/api/speakers")
def list_speakers():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT TOP 200 Name
                FROM (
                    SELECT LTRIM(RTRIM(ISNULL(SpeakerName, ''))) AS Name
                    FROM dbo.MeetingMessages
                    UNION
                    SELECT LTRIM(RTRIM(ISNULL(CreatedBy, ''))) AS Name
                    FROM dbo.MeetingRooms
                ) Names
                WHERE Name <> ''
                ORDER BY Name ASC
                """
            )
            rows = cursor.fetchall()

        names = [row[0] for row in rows]
        return jsonify({"names": names})
    except Exception as exc:
        return jsonify({"error": f"failed to load names: {exc}"}), 500


@app.post("/api/rooms")
def create_room():
    payload = request.get_json(silent=True) or {}
    room_name = str(payload.get("room_name", "")).strip()
    created_by = str(payload.get("created_by", "")).strip()

    if not room_name:
        return jsonify({"error": "room_name is required"}), 400

    if len(room_name) > 200:
        return jsonify({"error": "room_name is too long (max 200)"}), 400

    if len(created_by) > 100:
        return jsonify({"error": "created_by is too long (max 100)"}), 400

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO dbo.MeetingRooms (RoomName, CreatedBy)
                OUTPUT inserted.RoomCode, inserted.RoomName
                VALUES (?, ?)
                """,
                room_name,
                (created_by or None),
            )
            row = cursor.fetchone()
            conn.commit()

        return jsonify(
            {
                "room_code": row[0],
                "room_name": row[1],
                "entry_url": f"/meeting/{row[0]}",
            }
        )
    except Exception as exc:
        return jsonify({"error": f"failed to create room: {exc}"}), 500


@app.post("/api/messages")
def save_message():
    payload = request.get_json(silent=True) or {}
    room_code = str(payload.get("room_code", "")).strip()
    speaker_name = str(payload.get("speaker_name", "")).strip()
    language_code = str(payload.get("language_code", "")).strip().lower()
    original_text = str(payload.get("original_text", "")).strip()
    translated_text_raw = payload.get("translated_text")
    translated_text = "" if translated_text_raw is None else str(translated_text_raw).strip()

    if not re.fullmatch(r"\d{6}", room_code):
        return jsonify({"error": "room_code must be 6 digits"}), 400
    if language_code not in {"ko", "ja"}:
        return jsonify({"error": "language_code must be ko or ja"}), 400
    if not original_text:
        return jsonify({"error": "original_text is required"}), 400
    if len(speaker_name) > 100:
        return jsonify({"error": "speaker_name is too long (max 100)"}), 400

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT TOP 1 RoomID
                FROM dbo.MeetingRooms
                WHERE RoomCode = ? AND IsActive = 1
                ORDER BY RoomID DESC
                """,
                room_code,
            )
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "room not found"}), 404

            room_id = row[0]
            cursor.execute(
                """
                INSERT INTO dbo.MeetingMessages (
                    RoomID,
                    RoomCode,
                    SpeakerName,
                    LanguageCode,
                    OriginalText,
                    TranslatedText
                )
                OUTPUT
                    inserted.MessageID,
                    CONVERT(VARCHAR(19), SWITCHOFFSET(inserted.MessageAt, '+09:00'), 120) AS MessageAt
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                room_id,
                room_code,
                (speaker_name or None),
                language_code,
                original_text,
                (translated_text or None),
            )
            inserted = cursor.fetchone()
            conn.commit()

        return jsonify(
            {
                "saved": True,
                "message_id": inserted[0] if inserted else None,
                "message_at": inserted[1] if inserted else None,
            }
        )
    except Exception as exc:
        return jsonify({"error": f"failed to save message: {exc}"}), 500


@app.get("/api/messages")
def list_messages():
    room_code = str(request.args.get("room_code", "")).strip()
    since_id_raw = str(request.args.get("since_id", "")).strip()
    if not re.fullmatch(r"\d{6}", room_code):
        return jsonify({"error": "room_code must be 6 digits"}), 400

    since_id = None
    if since_id_raw:
        if not since_id_raw.isdigit():
            return jsonify({"error": "since_id must be a positive integer"}), 400
        since_id = int(since_id_raw)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if since_id is None:
                cursor.execute(
                    """
                    SELECT TOP 300
                        MessageID,
                        ISNULL(SpeakerName, '') AS SpeakerName,
                        LanguageCode,
                        OriginalText,
                        ISNULL(TranslatedText, '') AS TranslatedText,
                        CONVERT(VARCHAR(19), SWITCHOFFSET(MessageAt, '+09:00'), 120) AS MessageAt
                    FROM dbo.MeetingMessages
                    WHERE RoomCode = ?
                    ORDER BY MessageID ASC
                    """,
                    room_code,
                )
            else:
                cursor.execute(
                    """
                    SELECT TOP 300
                        MessageID,
                        ISNULL(SpeakerName, '') AS SpeakerName,
                        LanguageCode,
                        OriginalText,
                        ISNULL(TranslatedText, '') AS TranslatedText,
                        CONVERT(VARCHAR(19), SWITCHOFFSET(MessageAt, '+09:00'), 120) AS MessageAt
                    FROM dbo.MeetingMessages
                    WHERE RoomCode = ? AND MessageID > ?
                    ORDER BY MessageID ASC
                    """,
                    room_code,
                    since_id,
                )
            rows = cursor.fetchall()

        messages = [
            {
                "message_id": row[0],
                "speaker_name": row[1],
                "language_code": row[2],
                "original_text": row[3],
                "translated_text": row[4],
                "message_at": row[5],
            }
            for row in rows
        ]
        return jsonify({"messages": messages})
    except Exception as exc:
        return jsonify({"error": f"failed to load messages: {exc}"}), 500


@app.post("/api/translate")
def translate_text():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    source_lang = str(payload.get("source", "")).strip().lower()
    target_lang = str(payload.get("target", "")).strip().lower()

    allowed = {"ko", "ja"}
    if not text:
        return jsonify({"error": "text is required"}), 400
    if source_lang not in allowed or target_lang not in allowed:
        return jsonify({"error": "source/target must be ko or ja"}), 400

    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        translated = translator.translate(text)
    except Exception as exc:
        return jsonify({"error": f"translation failed: {exc}"}), 500

    return jsonify({"translated_text": translated})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5055))
    debug = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    app.run(host="0.0.0.0", port=port, debug=debug)
