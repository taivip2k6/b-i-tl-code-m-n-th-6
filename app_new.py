from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import base64
import hashlib
import hmac
import logging
import os
import re
import secrets
from datetime import datetime

from cipher_utils import (
    aes_decrypt,
    aes_encrypt,
    caesar_cipher_decrypt,
    generate_and_save_keys,
    rsa_decrypt,
    rsa_encrypt,
    rsa_private_key,
    rsa_public_key,
    vigenere_cipher_decrypt,
)


app = Flask(__name__, template_folder=".")
CORS(app, origins=["http://localhost:5000", "http://127.0.0.1:5000"])
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(24)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///game.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AES_KEY = base64.b64decode(os.getenv("AES_KEY", base64.b64encode(secrets.token_bytes(16)).decode()))
if len(AES_KEY) != 16:
    raise ValueError("AES_KEY must be a base64 string of 16 bytes")

GAME_HMAC_KEY = os.getenv("GAME_HMAC_KEY", secrets.token_hex(16)).encode("utf-8")


generate_and_save_keys()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    score = db.Column(db.Integer, default=0)
    current_level = db.Column(db.Integer, default=1)
    attempts = db.relationship("UserAttempt", backref="user", lazy=True)


class UserAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    attempts_left = db.Column(db.Integer, default=5)
    last_attempt = db.Column(db.DateTime, nullable=True)


with app.app_context():
    db.create_all()


LEVELS = [
    {
        "level": 1,
        "algorithm": "caesar",
        "title": "Màn 1: Caesar",
        "ciphertext": "KhoiF, Zruog!",
        "correct_output": "Hello, World!",
        "hint": "Số bước dịch là số ngọn nến trong hang động.",
        "story": "Bạn tìm thấy một mẩu giấy cổ trong hang động, ghi thông điệp bí ẩn dẫn đến kho báu.",
        "solution_param": "3",
        "explanation": "Caesar Cipher dịch từng chữ cái đi một số vị trí cố định. Việc tìm đúng độ dịch là bước đầu để hiểu mật mã cổ điển.",
        "answer_label": "Độ dịch chuyển",
        "input_type": "number",
    },
    {
        "level": 2,
        "algorithm": "vigenere",
        "title": "Màn 2: Vigenère",
        "ciphertext": "Rijvs, Uyvzr!",
        "correct_output": "Hello, World!",
        "hint": "Từ khóa là tên của vị thần bảo vệ ngôi đền.",
        "story": "Thông điệp dẫn bạn đến ngôi đền cổ, nơi ẩn chứa câu đố phức tạp hơn.",
        "solution_param": "KEY",
        "explanation": "Vigenère Cipher sử dụng một từ khóa để dịch các chữ cái khác nhau, tăng độ khó hơn Caesar vì khóa làm thay đổi cách dịch theo vị trí.",
        "answer_label": "Từ khóa",
        "input_type": "text",
    },
    {
        "level": 3,
        "algorithm": "hash",
        "title": "Màn 3: Hash & toàn vẹn",
        "ciphertext": "The map is safe",
        "correct_output": hmac.new(GAME_HMAC_KEY, b"The map is safe", hashlib.sha256).hexdigest(),
        "hint": "Tạo HMAC-SHA256 cho thông điệp và nhập giá trị đúng.",
        "story": "Một tấm bản đồ gửi qua kênh không an toàn; bạn cần kiểm tra xem liệu nội dung có bị thay đổi hay không.",
        "solution_param": "",
        "explanation": "Hash và HMAC được dùng để kiểm tra toàn vẹn dữ liệu. Nếu nội dung thay đổi, giá trị băm cũng đổi, giúp phát hiện dữ liệu bị sửa.",
        "answer_label": "HMAC-SHA256",
        "input_type": "text",
    },
    {
        "level": 4,
        "algorithm": "aes",
        "title": "Màn 4: AES",
        "ciphertext": base64.b64encode(aes_encrypt(AES_KEY, "You found the treasure!")).decode(),
        "correct_output": "You found the treasure!",
        "hint": "Khóa AES là một chuỗi base64 16 byte.",
        "story": "Chiếc hộp khóa mở ra, nhưng phần cuối cùng cần một khóa mật mã hiện đại.",
        "solution_param": base64.b64encode(AES_KEY).decode(),
        "explanation": "AES là thuật toán mã hóa đối xứng hiện đại, dùng chung một khóa cho cả mã hóa và giải mã. Nó cung cấp bảo mật tốt hơn nhiều mật mã cổ điển.",
        "answer_label": "Khóa AES",
        "input_type": "text",
    },
    {
        "level": 5,
        "algorithm": "rsa",
        "title": "Màn 5: RSA",
        "ciphertext": base64.b64encode(rsa_encrypt(rsa_public_key, "Find the key!")).decode(),
        "correct_output": "Find the key!",
        "hint": "Khóa riêng phải bắt đầu bằng '-----BEGIN RSA PRIVATE KEY-----'.",
        "story": "Trong ngăn kéo cổ, bạn phát hiện ra một khóa công khai và cần dùng khóa riêng để mở chiếc hộp cuối cùng.",
        "solution_param": rsa_private_key.decode(),
        "explanation": "RSA là hệ thống khóa công khai: khóa công khai dùng để mã hóa, khóa riêng dùng để giải mã. Đây là cơ sở cho trao đổi khóa và chữ ký số hiện đại.",
        "answer_label": "Khóa riêng RSA",
        "input_type": "text",
    },
    {
        "level": 6,
        "algorithm": "detect_nonce",
        "title": "Màn 6: Phát hiện lỗi thiết kế",
        "ciphertext": "Two sessions used the same nonce to encrypt the treasure map.",
        "correct_output": "nonce_reuse",
        "hint": "Hãy chọn lỗi bảo mật mà bạn thấy trong tình huống này.",
        "story": "Một hệ thống mã hóa đã dùng lại cùng một nonce cho nhiều bản ghi, làm giảm bảo mật của giao thức.",
        "solution_param": "nonce_reuse",
        "explanation": "Dùng lại nonce trong giao thức mã hóa có thể làm lộ thông tin khóa và phá vỡ bảo mật. Đây là lỗi thiết kế thường gặp trong các hệ thống triển khai sai.",
        "answer_label": "Lỗi bảo mật",
        "input_type": "select",
        "options": [
            {"value": "nonce_reuse", "label": "Dùng lại nonce"},
            {"value": "hash_without_salt", "label": "Hash không dùng salt"},
            {"value": "replay_attack", "label": "Replay attack"},
        ],
    },
    {
        "level": 7,
        "algorithm": "detect_replay",
        "title": "Màn 7: Replay attack",
        "ciphertext": "A message was received twice from the same session without any freshness check.",
        "correct_output": "replay_attack",
        "hint": "Hãy chọn lỗi bảo mật tương ứng với tình huống.",
        "story": "Một tin nhắn bị gửi lại nhiều lần; hệ thống không có nonce, timestamp hoặc sequence number để phát hiện.",
        "solution_param": "replay_attack",
        "explanation": "Replay attack xảy ra khi một gói tin cũ được gửi lại. Cơ chế nonce, timestamp hoặc số thứ tự giúp ngăn chặn điều này.",
        "answer_label": "Lỗi bảo mật",
        "input_type": "select",
        "options": [
            {"value": "nonce_reuse", "label": "Dùng lại nonce"},
            {"value": "hash_without_salt", "label": "Hash không dùng salt"},
            {"value": "replay_attack", "label": "Replay attack"},
        ],
    },
]


@app.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    confirm_password = data.get("confirm_password") or ""

    if not username or not password or not confirm_password:
        return jsonify({"error": "Tên người dùng, mật khẩu và xác nhận mật khẩu không được để trống!"}), 400
    if password != confirm_password:
        return jsonify({"error": "Mật khẩu không khớp!"}), 400
    if not re.match(r"^[a-zA-Z0-9_-]{3,20}$", username):
        return jsonify({"error": "Tên người dùng phải dài 3-20 ký tự, chỉ chứa chữ cái, số, dấu gạch dưới hoặc dấu gạch ngang!"}), 400
    if len(password) < 6:
        return jsonify({"error": "Mật khẩu phải có ít nhất 6 ký tự!"}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "Tên người dùng đã tồn tại!"}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(username=username, password_hash=hashed_password)
    db.session.add(user)
    db.session.commit()
    logger.info("User registered: %s", username)
    return jsonify({"message": "Đăng ký thành công!"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        logger.warning("Failed login attempt for user: %s", username)
        return jsonify({"error": "Tên người dùng hoặc mật khẩu không đúng!"}), 401

    session["user_id"] = user.id
    session["username"] = user.username
    logger.info("User logged in: %s", username)
    return jsonify({
        "message": "Đăng nhập thành công!",
        "username": user.username,
        "score": user.score,
        "current_level": user.current_level,
    }), 200


@app.route("/logout", methods=["POST"])
def logout():
    username = session.get("username", "Guest")
    session.clear()
    logger.info("User logged out: %s", username)
    return jsonify({"message": "Đăng xuất thành công!"}), 200


@app.route("/get_user_data", methods=["GET"])
def get_user_data():
    if "user_id" not in session:
        return jsonify({"error": "Chưa đăng nhập!"}), 401
    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return jsonify({"error": "Người dùng không tồn tại hoặc phiên không hợp lệ!"}), 404
    return jsonify({"username": user.username, "score": user.score, "current_level": user.current_level}), 200


@app.route("/reset", methods=["POST"])
def reset_game():
    if "user_id" not in session:
        return jsonify({"error": "Vui lòng đăng nhập để chơi!"}), 401
    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return jsonify({"error": "Người dùng không tồn tại hoặc phiên không hợp lệ!"}), 404
    user.score = 0
    user.current_level = 1
    UserAttempt.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    logger.info("Reset game for user: %s", user.username)
    return jsonify({"message": "Trò chơi đã được đặt lại!", "score": 0, "current_level": 1}), 200


@app.route("/level/<int:level>", methods=["GET"])
def get_level(level):
    if "user_id" not in session:
        return jsonify({"error": "Vui lòng đăng nhập để chơi!"}), 401
    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return jsonify({"error": "Người dùng không tồn tại hoặc phiên không hợp lệ!"}), 404
    if level < 1 or level > len(LEVELS):
        return jsonify({"error": "Cấp độ không hợp lệ!"}), 400
    if level > user.current_level:
        return jsonify({"error": "Bạn chưa mở khóa cấp độ này!"}), 403

    level_data = LEVELS[level - 1]
    attempt = UserAttempt.query.filter_by(user_id=user.id, level=level).first()
    attempts_left = 5 if not attempt else attempt.attempts_left
    return jsonify({
        "level": level_data["level"],
        "title": level_data["title"],
        "algorithm": level_data["algorithm"],
        "ciphertext": level_data["ciphertext"],
        "hint": level_data["hint"],
        "story": level_data["story"],
        "points": user.score,
        "current_user_level": user.current_level,
        "attempts_left": attempts_left,
        "explanation": level_data["explanation"],
        "answer_label": level_data["answer_label"],
        "input_type": level_data["input_type"],
        "options": level_data.get("options", []),
    })


@app.route("/decode/<int:level>", methods=["POST"])
def decode(level):
    if "user_id" not in session:
        return jsonify({"error": "Vui lòng đăng nhập để chơi!"}), 401
    if level < 1 or level > len(LEVELS):
        return jsonify({"error": "Cấp độ không hợp lệ!"}), 400

    data = request.json or {}
    submitted_ciphertext = data.get("ciphertext")
    submitted_param = data.get("param")
    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return jsonify({"error": "Người dùng không tồn tại hoặc phiên không hợp lệ!"}), 404
    if level > user.current_level:
        return jsonify({"error": "Bạn chưa mở khóa cấp độ này!"}), 403

    level_data = LEVELS[level - 1]
    if submitted_ciphertext != level_data["ciphertext"]:
        return jsonify({"success": False, "message": "Thông điệp mã hóa không khớp với cấp độ hiện tại!"}), 400

    attempt = UserAttempt.query.filter_by(user_id=user.id, level=level).first()
    if not attempt:
        attempt = UserAttempt(user_id=user.id, level=level, attempts_left=5)
        db.session.add(attempt)
    if attempt.attempts_left <= 0:
        return jsonify({"success": False, "message": "Bạn đã hết số lần thử cho cấp độ này! Vui lòng đặt lại trò chơi."}), 403

    attempt.attempts_left -= 1
    attempt.last_attempt = datetime.utcnow()
    db.session.commit()

    if level_data["algorithm"] in {"detect_nonce", "detect_replay"}:
        seen = session.setdefault("replay_checks", [])
        token = f"{user.id}:{level}:{submitted_ciphertext}:{submitted_param}"
        if token in seen:
            logger.warning("Replay attempt blocked for user %s level %s", user.username, level)
            return jsonify({"success": False, "message": "Phát hiện gửi lại dữ liệu cũ. Hệ thống đã chặn lượt thử này.", "attempts_left": attempt.attempts_left}), 400
        seen.append(token)
        if len(seen) > 50:
            session["replay_checks"] = seen[-50:]

    try:
        if level_data["algorithm"] == "caesar":
            if not submitted_param or not str(submitted_param).isdigit() or not (1 <= int(submitted_param) <= 25):
                return jsonify({"success": False, "message": "Độ dịch chuyển phải là số nguyên từ 1 đến 25!", "attempts_left": attempt.attempts_left}), 400
            decrypted_result = caesar_cipher_decrypt(submitted_ciphertext, int(submitted_param))
        elif level_data["algorithm"] == "vigenere":
            if not submitted_param or not re.match(r"^[a-zA-Z]+$", str(submitted_param)):
                return jsonify({"success": False, "message": "Từ khóa chỉ được chứa chữ cái!", "attempts_left": attempt.attempts_left}), 400
            decrypted_result = vigenere_cipher_decrypt(submitted_ciphertext, str(submitted_param))
        elif level_data["algorithm"] == "rsa":
            if not submitted_param or not str(submitted_param).strip().startswith("-----BEGIN RSA PRIVATE KEY-----"):
                return jsonify({"success": False, "message": "Khóa RSA không hợp lệ. Phải bắt đầu bằng '-----BEGIN RSA PRIVATE KEY-----'!", "attempts_left": attempt.attempts_left}), 400
            try:
                encrypted_message_bytes = base64.b64decode(submitted_ciphertext)
                decrypted_result = rsa_decrypt(str(submitted_param).encode("utf-8"), encrypted_message_bytes)
            except Exception as exc:
                logger.error("RSA decryption error for user %s at level %s: %s", user.username, level, exc)
                return jsonify({"success": False, "message": f"Khóa RSA không hợp lệ: {exc}", "attempts_left": attempt.attempts_left}), 400
        elif level_data["algorithm"] == "aes":
            if not submitted_param:
                return jsonify({"success": False, "message": "Khóa AES không được để trống!", "attempts_left": attempt.attempts_left}), 400
            try:
                aes_key_bytes_from_param = base64.b64decode(submitted_param)
                if len(aes_key_bytes_from_param) != 16:
                    return jsonify({"success": False, "message": "Khóa AES phải là 16 byte sau khi giải mã base64!", "attempts_left": attempt.attempts_left}), 400
                iv_and_ciphertext_bytes = base64.b64decode(submitted_ciphertext)
                decrypted_result = aes_decrypt(aes_key_bytes_from_param, iv_and_ciphertext_bytes)
            except Exception as exc:
                logger.error("AES decryption error for user %s at level %s: %s", user.username, level, exc)
                return jsonify({"success": False, "message": f"Khóa AES không hợp lệ: {exc}", "attempts_left": attempt.attempts_left}), 400
        elif level_data["algorithm"] == "hash":
            if not submitted_param:
                return jsonify({"success": False, "message": "Vui lòng nhập giá trị HMAC-SHA256!", "attempts_left": attempt.attempts_left}), 400
            expected_digest = level_data["correct_output"]
            decrypted_result = expected_digest if str(submitted_param).strip().lower() == expected_digest.lower() else ""
        else:
            if not submitted_param:
                return jsonify({"success": False, "message": "Vui lòng chọn một lỗi bảo mật!", "attempts_left": attempt.attempts_left}), 400
            decrypted_result = str(submitted_param).strip().lower()

        if decrypted_result == level_data["correct_output"] or (level_data["algorithm"] in {"detect_nonce", "detect_replay"} and str(submitted_param).strip().lower() == level_data["correct_output"]):
            points_earned = 100 * level
            user.score += points_earned
            if level == user.current_level:
                user.current_level = level + 1 if level < len(LEVELS) else level
            attempt.attempts_left = 5
            db.session.commit()
            logger.info("User %s completed level %s. Score: %s", user.username, level, user.score)
            return jsonify({
                "success": True,
                "message": f"Chúc mừng! Bạn đã hoàn thành {level_data['title']}.",
                "points_earned": points_earned,
                "total_points": user.score,
                "next_level": user.current_level if user.current_level > level else None,
                "attempts_left": attempt.attempts_left,
                "explanation": level_data["explanation"],
            })

        logger.info("User %s failed level %s. Incorrect output.", user.username, level)
        return jsonify({
            "success": False,
            "message": f"Đáp án chưa đúng. Còn {attempt.attempts_left} lần thử!",
            "attempts_left": attempt.attempts_left,
        })
    except Exception as exc:
        logger.error("Unhandled decryption error for user %s at level %s: %s", user.username, level, exc, exc_info=True)
        return jsonify({"success": False, "message": f"Lỗi hệ thống: {exc}", "attempts_left": attempt.attempts_left}), 500


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
