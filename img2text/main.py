import pytesseract
from PIL import Image
from pathlib import Path
from typing import Union

# Tesseract 실행 파일 경로 설정 (환경에 맞게 조정하세요)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\Tesseract.exe"


def extract_text_from_image(
    image_path: Union[str, Path],
    lang: str = "kor+eng",
    config: str = "--psm 6",
) -> str:
    """
    이미지 파일 경로를 받아 Tesseract로 텍스트를 추출합니다.

    :param image_path: 이미지 파일 경로
    :param lang: 사용할 언어 (기본: 한국어 + 영어)
    :param config: Tesseract 설정 옵션
    :return: 추출된 텍스트
    """
    img = Image.open(str(image_path))
    text = pytesseract.image_to_string(img, lang=lang, config=config)
    return text


if __name__ == "__main__":
    # 예시 실행용 코드 (직접 실행할 때만 동작)
    sample_image = Path("images/test2.jpg")
    if sample_image.exists():
        extracted = extract_text_from_image(sample_image)
        print(extracted)
    else:
        print("샘플 이미지가 존재하지 않습니다: images/test2.jpg")
