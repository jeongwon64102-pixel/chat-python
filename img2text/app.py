from flask import Flask, render_template_string, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from pathlib import Path

from main import extract_text_from_image

try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False


app = Flask(__name__)
app.secret_key = "change-this-secret-key"

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "tiff", "tif", "gif", "pdf"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8" />
    <title>이미지 / PDF 텍스트 추출</title>
    <style>
        * {
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        body {
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #e0f3ff, #f5fbff);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #123;
        }
        .container {
            background: #ffffff;
            border-radius: 18px;
            box-shadow: 0 18px 45px rgba(0, 140, 255, 0.18);
            max-width: 900px;
            width: 100%;
            padding: 32px 36px 28px;
        }
        .title {
            font-size: 24px;
            font-weight: 700;
            color: #0167c4;
            margin-bottom: 6px;
        }
        .subtitle {
            font-size: 13px;
            color: #5b7a99;
            margin-bottom: 24px;
        }
        .upload-card {
            border: 1px dashed #8dc6ff;
            background: #f3f9ff;
            border-radius: 14px;
            padding: 20px 18px;
            display: flex;
            align-items: center;
            gap: 18px;
            margin-bottom: 18px;
        }
        .upload-icon {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: linear-gradient(145deg, #4ca8ff, #2f7fe5);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-size: 22px;
        }
        .upload-info-main {
            flex: 1;
        }
        .upload-label {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 9px 18px;
            border-radius: 999px;
            border: none;
            background: #0f8fff;
            color: #fff;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s ease-in-out;
            margin-right: 10px;
        }
        .upload-label:hover {
            background: #0073d1;
            box-shadow: 0 8px 15px rgba(0, 129, 255, 0.3);
            transform: translateY(-1px);
        }
        .upload-label:active {
            transform: translateY(0);
            box-shadow: none;
        }
        .filename {
            font-size: 13px;
            color: #44617c;
        }
        .helper-text {
            font-size: 12px;
            color: #8aa2b8;
            margin-top: 4px;
        }
        .options {
            display: flex;
            gap: 16px;
            align-items: center;
            margin-bottom: 16px;
        }
        .radio-group {
            display: flex;
            gap: 10px;
            align-items: center;
            font-size: 12px;
            color: #456;
        }
        .submit-btn {
            padding: 10px 22px;
            border-radius: 999px;
            border: none;
            background: linear-gradient(135deg, #00a6ff, #0084ff);
            color: #fff;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            margin-left: auto;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 10px 20px rgba(0, 140, 255, 0.4);
            transition: all 0.15s ease-in-out;
        }
        .submit-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 14px 26px rgba(0, 140, 255, 0.45);
        }
        .submit-btn:active {
            transform: translateY(0);
            box-shadow: 0 6px 16px rgba(0, 140, 255, 0.35);
        }
        .result-card {
            margin-top: 18px;
            border-radius: 14px;
            background: #f7fbff;
            border: 1px solid #d3e7ff;
            padding: 14px 14px 12px;
        }
        .result-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        .result-title {
            font-size: 13px;
            font-weight: 600;
            color: #225;
        }
        .result-badge {
            font-size: 11px;
            color: #0b6fd6;
            padding: 2px 8px;
            border-radius: 999px;
            background: #e1f0ff;
        }
        .result-textarea {
            width: 100%;
            min-height: 200px;
            resize: vertical;
            border-radius: 10px;
            border: none;
            padding: 10px 11px;
            font-size: 13px;
            line-height: 1.5;
            background: #ffffff;
            box-shadow: inset 0 0 0 1px #e2edf9;
            outline: none;
        }
        .result-textarea:focus {
            box-shadow: inset 0 0 0 1px #3a98ff;
        }
        .flash {
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 12px;
        }
        .flash-error {
            background: #ffecec;
            color: #b30000;
            border: 1px solid #ffc5c5;
        }
        .flash-info {
            background: #e6f3ff;
            color: #0a4f9e;
            border: 1px solid #c6e1ff;
        }
        .top-row {
            display: flex;
            gap: 16px;
            align-items: center;
            justify-content: space-between;
        }
        .lang-chip {
            font-size: 11px;
            color: #1b4f80;
            background: #e1f2ff;
            padding: 3px 9px;
            border-radius: 999px;
        }
        /* display:none 으로 완전히 숨기면 일부 환경에서 label 클릭 업로드가 동작하지 않는 경우가 있어
           접근성/호환성 좋은 방식(화면 밖 + 투명)으로 숨깁니다. */
        input[type="file"] {
            position: absolute;
            left: -9999px;
            width: 1px;
            height: 1px;
            opacity: 0;
        }
        @media (max-width: 640px) {
            .container {
                margin: 16px;
                padding: 18px 16px 18px;
            }
            .upload-card {
                flex-direction: column;
                align-items: flex-start;
            }
            .top-row {
                flex-direction: column;
                align-items: flex-start;
            }
            .submit-btn {
                margin-top: 8px;
                width: 100%;
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="top-row">
            <div>
                <div class="title">이미지 / PDF 텍스트 추출</div>
                <div class="subtitle">이미지 또는 PDF 문서를 업로드하면 한국어를 기본으로, 영어 텍스트도 함께 인식합니다.</div>
            </div>
            <div class="lang-chip">기본 언어: 한국어 + 영어</div>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="flash {% if category == 'error' %}flash-error{% else %}flash-info{% endif %}">
                {{ message }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <form method="post" enctype="multipart/form-data">
            <div class="upload-card">
                <div class="upload-icon">⤒</div>
                <div class="upload-info-main">
                    <label for="file" class="upload-label">파일 선택</label>
                    <span class="filename" id="filename">선택된 파일이 없습니다.</span>
                    <div class="helper-text">
                        지원 형식: 이미지 (JPG, PNG, BMP, TIFF 등) 또는 PDF · 최대 1파일
                    </div>
                </div>
            </div>

            <input type="file" id="file" name="file" accept=".png,.jpg,.jpeg,.bmp,.tiff,.tif,.gif,.pdf" required />

            <div class="options">
                <div class="radio-group">
                    <span style="font-weight:600; font-size:12px; color:#234;">언어 설정</span>
                    <label>
                        <input type="radio" name="lang_mode" value="kor" {% if lang_mode == 'kor' %}checked{% endif %} />
                        한국어
                    </label>
                    <label>
                        <input type="radio" name="lang_mode" value="kor+eng" {% if lang_mode == 'kor+eng' %}checked{% endif %} />
                        한국어 + 영어
                    </label>
                </div>
                <button type="submit" class="submit-btn">
                    텍스트 추출
                    <span>⮞</span>
                </button>
            </div>
        </form>

        <div class="result-card">
            <div class="result-header">
                <div class="result-title">추출된 텍스트</div>
                <span class="result-badge">
                    {% if result %}{{ (result|length) }}자 인식{% else %}결과가 여기에 표시됩니다{% endif %}
                </span>
            </div>
            <textarea class="result-textarea" readonly>{{ result or "" }}</textarea>
        </div>
    </div>

    <script>
        const fileInput = document.getElementById('file');
        const filenameSpan = document.getElementById('filename');

        fileInput.addEventListener('change', function () {
            if (this.files && this.files.length > 0) {
                filenameSpan.textContent = this.files[0].name;
            } else {
                filenameSpan.textContent = '선택된 파일이 없습니다.';
            }
        });
    </script>
</body>
</html>
"""


def extract_text_from_pdf(pdf_path: Path, lang: str) -> str:
    """
    PDF 파일에서 이미지를 추출한 뒤, 페이지별로 OCR을 수행해 하나의 문자열로 합칩니다.
    """
    if not HAS_PDF2IMAGE:
        raise RuntimeError(
            "pdf2image 모듈이 설치되어 있지 않습니다. 'pip install pdf2image' 후 다시 시도하세요."
        )

    # Windows에서 pdf2image를 사용하려면 poppler가 설치되어 있고 PATH가 설정되어 있어야 합니다.
    images = convert_from_path(str(pdf_path))

    texts = []
    for img in images:
        # PIL Image 객체를 그대로 pytesseract에 전달
        import pytesseract

        text = pytesseract.image_to_string(img, lang=lang, config="--psm 6")
        texts.append(text)

    return "\n\n".join(texts)


@app.route("/", methods=["GET", "POST"])
def index():
    result_text = ""
    lang_mode = "kor+eng"

    if request.method == "POST":
        lang_mode = request.form.get("lang_mode", "kor+eng")

        if "file" not in request.files:
            flash("파일이 전송되지 않았습니다.", "error")
            return redirect(url_for("index"))

        file = request.files["file"]

        if file.filename == "":
            flash("선택된 파일이 없습니다.", "error")
            return redirect(url_for("index"))

        if not allowed_file(file.filename):
            flash("지원하지 않는 파일 형식입니다.", "error")
            return redirect(url_for("index"))

        filename = secure_filename(file.filename)
        save_path = UPLOAD_FOLDER / filename
        file.save(save_path)

        try:
            ext = save_path.suffix.lower()
            if ext == ".pdf":
                result_text = extract_text_from_pdf(save_path, lang=lang_mode)
            else:
                result_text = extract_text_from_image(save_path, lang=lang_mode)

            if not result_text.strip():
                flash("텍스트를 인식하지 못했습니다. 이미지/문서를 확인해 주세요.", "info")

        except Exception as e:
            flash(f"텍스트 추출 중 오류가 발생했습니다: {e}", "error")
        finally:
            # 임시 업로드 파일 삭제 (PDF → 이미지 변환은 메모리에서 처리)
            try:
                save_path.unlink(missing_ok=True)
            except Exception:
                pass

    return render_template_string(HTML_TEMPLATE, result=result_text, lang_mode=lang_mode)


if __name__ == "__main__":
    # 개발용 서버 실행
    app.run(host="0.0.0.0", port=5000, debug=True)

