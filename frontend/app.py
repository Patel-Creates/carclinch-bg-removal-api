import base64
import os
from io import BytesIO
from urllib.parse import quote

import requests
from flask import Flask, render_template, request, send_file

app = Flask(__name__)

API_URL = os.getenv("BG_REMOVE_API_URL", "http://127.0.0.1:8000").rstrip("/")
# DEFAULT_MODE = os.getenv("DEFAULT_MODE", "all-models")
DEFAULT_MODE = os.getenv("DEFAULT_MODE", "single-model")

def to_data_url(file_bytes: bytes, mime_type: str) -> str:
    encoded = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"

def to_bool(value: str | None) -> bool:
    return str(value).lower() in {"1", "true", "on", "yes"}


@app.get("/")
def index():
    return render_template("index.html", selected_mode=DEFAULT_MODE)

@app.post("/process")
def process():
    car_file = request.files.get("image")
    bg_file = request.files.get("background")

    if not car_file or not car_file.filename:
        return render_template(
            "index.html",
            error="Please choose a car image.",
            selected_mode=request.form.get("mode", DEFAULT_MODE),
        )

    if not bg_file or not bg_file.filename:
        return render_template(
            "index.html",
            error="Please choose a background image.",
            selected_mode=request.form.get("mode", DEFAULT_MODE),
        )

    car_bytes = car_file.read()
    bg_bytes = bg_file.read()

    if not car_bytes:
        return render_template(
            "index.html",
            error="The car image is empty.",
            selected_mode=request.form.get("mode", DEFAULT_MODE),
        )

    if not bg_bytes:
        return render_template(
            "index.html",
            error="The background image is empty.",
            selected_mode=request.form.get("mode", DEFAULT_MODE),
        )

    car_preview = to_data_url(car_bytes, car_file.mimetype or "image/jpeg")
    background_preview = to_data_url(bg_bytes, bg_file.mimetype or "image/jpeg")

    car_size = request.form.get("car_size", "60")
    smart_placement = to_bool(request.form.get("smart_placement", "true"))
    mode = request.form.get("mode", DEFAULT_MODE)

    endpoint = (
        f"{API_URL}/replace-background-all-models"
        if mode == "all-models"
        else f"{API_URL}/replace-background"
    )

    files = {
        "image": (car_file.filename, car_bytes, car_file.mimetype or "application/octet-stream"),
        "background": (bg_file.filename, bg_bytes, bg_file.mimetype or "application/octet-stream"),
    }
    data = {
        "car_size": car_size,
        "smart_placement": str(smart_placement).lower(),
    }

    try:
        response = requests.post(endpoint, files=files, data=data, timeout=300)
        response.raise_for_status()
        payload = response.json()

        results = []

        if mode == "all-models":
            for item in payload.get("results", []):
                if item.get("status") != "success":
                    continue

                image_url = item.get("image_url")
                if not image_url:
                    continue

                absolute_url = f"{API_URL}{image_url}" if image_url.startswith("/") else image_url

                results.append(
                    {
                        "model": item.get("model", "unknown"),
                        "preview_url": absolute_url,
                        "download_url": f"/download?file_url={quote(absolute_url, safe=':/?=&')}&filename={item.get('output_filename', 'result.png')}",
                        "output_filename": item.get("output_filename", "result.png"),
                    }
                )
        else:
            image_url = payload.get("image_url")
            if image_url:
                absolute_url = f"{API_URL}{image_url}" if image_url.startswith("/") else image_url
                results.append(
                    {
                        "model": "birefnet-general",
                        "preview_url": absolute_url,
                        "download_url": f"/download?file_url={quote(absolute_url, safe=':/?=&')}&filename={payload.get('output_filename', 'result.png')}",
                        "output_filename": payload.get("output_filename", "result.png"),
                    }
                )

        if not results:
            return render_template(
                "index.html",
                error="The API finished, but no previewable output image was returned.",
                car_preview=car_preview,
                background_preview=background_preview,
                car_size=car_size,
                smart_placement=smart_placement,
                selected_mode=mode,
            )

        return render_template(
            "index.html",
            car_preview=car_preview,
            background_preview=background_preview,
            results=results,
            car_size=car_size,
            smart_placement=smart_placement,
            selected_mode=mode,
        )

    except requests.HTTPError:
        try:
            payload = response.json()
            detail = payload.get("detail", payload)
        except ValueError:
            detail = response.text or "Unexpected server error."

        return render_template(
            "index.html",
            error=f"API error: {detail}",
            car_preview=car_preview,
            background_preview=background_preview,
            car_size=car_size,
            smart_placement=smart_placement,
            selected_mode=mode,
        )

    except requests.RequestException as e:
        return render_template(
            "index.html",
            error=f"Connection issue: {e}",
            car_preview=car_preview,
            background_preview=background_preview,
            car_size=car_size,
            smart_placement=smart_placement,
            selected_mode=mode,
        )
        
    car_file = request.files.get("image")
    bg_file = request.files.get("background")

    if not car_file or not car_file.filename:
        return render_template(
            "index.html",
            error="Please choose a car image.",
            selected_mode=request.form.get("mode", DEFAULT_MODE),
        )

    if not bg_file or not bg_file.filename:
        return render_template(
            "index.html",
            error="Please choose a background image.",
            selected_mode=request.form.get("mode", DEFAULT_MODE),
        )

    car_bytes = car_file.read()
    bg_bytes = bg_file.read()

    if not car_bytes:
        return render_template(
            "index.html",
            error="The car image is empty.",
            selected_mode=request.form.get("mode", DEFAULT_MODE),
        )

    if not bg_bytes:
        return render_template(
            "index.html",
            error="The background image is empty.",
            selected_mode=request.form.get("mode", DEFAULT_MODE),
        )
        
    car_preview = to_data_url(car_bytes, car_file.mimetype or "image/jpeg")
    background_preview = to_data_url(bg_bytes, bg_file.mimetype or "image/jpeg")

    car_size = request.form.get("car_size", "60")
    smart_placement = to_bool(request.form.get("smart_placement", "true"))
    mode = request.form.get("mode", DEFAULT_MODE)

    endpoint = (
        f"{API_URL}/replace-background-all-models"
        if mode == "all-models"
        else f"{API_URL}/replace-background"
    )

    files = {
        "image": (car_file.filename, car_bytes, car_file.mimetype or "application/octet-stream"),
        "background": (bg_file.filename, bg_bytes, bg_file.mimetype or "application/octet-stream"),
    }
    data = {
        "car_size": car_size,
        "smart_placement": str(smart_placement).lower(),
    }

    try:
        response = requests.post(endpoint, files=files, data=data, timeout=300)
        response.raise_for_status()
        payload = response.json()

        results = []

        if mode == "all-models":
            for item in payload.get("results", []):
                if item.get("status") != "success":
                    continue
                image_url = item.get("image_url")
                if not image_url:
                    continue
                absolute_url = f"{API_URL}{image_url}" if image_url.startswith("/") else image_url
                results.append(
                    {
                        "model": item.get("model", "unknown"),
                        "preview_url": absolute_url,
                        "download_url": f"/download?file_url={quote(absolute_url, safe=':/?=&')}&filename={item.get('output_filename', 'result.png')}",
                        "output_filename": item.get("output_filename", "result.png"),
                    }
                )
                
        else:
            image_url = payload.get("image_url")
            if image_url:
                absolute_url = f"{API_URL}{image_url}" if image_url.startswith("/") else image_url
                results.append(
                    {
                        "model": "birefnet-general",
                        "preview_url": absolute_url,
                        "download_url": f"/download?file_url={quote(absolute_url, safe=':/?=&')}&filename={payload.get('output_filename', 'result.png')}",
                        "output_filename": payload.get("output_filename", "result.png"),
                    }
                )
                
        if not results:
            return render_template(
                "index.html",
                error="The API finished, but no previewable output image was returned.",
                car_preview=car_preview,
                background_preview=background_preview,
                car_size=car_size,
                smart_placement=smart_placement,
                selected_mode=mode,
            )
            
        if not results:
            return render_template(
                "index.html",
                error="The API finished, but no previewable output image was returned.",
                car_preview=car_preview,
                background_preview=background_preview,
                car_size=car_size,
                smart_placement=smart_placement,
                selected_mode=mode,
            )
            
    except requests.HTTPError:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text or "Unexpected server error."
        return render_template(
            "index.html",
            error=f"API error: {detail}",
            car_preview=car_preview,
            background_preview=background_preview,
            car_size=car_size,
            smart_placement=smart_placement,
            selected_mode=mode,
        )
    except requests.RequestException:
        return render_template(
            "index.html",
            error="Connection issue. Please try again.",
            car_preview=car_preview,
            background_preview=background_preview,
            car_size=car_size,
            smart_placement=smart_placement,
            selected_mode=mode,
        )
        
@app.get("/download")
def download():
    file_url = request.args.get("file_url")
    filename = request.args.get("filename", "result.png")

    if not file_url:
        return "Missing file URL", 400

    try:
        response = requests.get(file_url, timeout=180)
        response.raise_for_status()
        return send_file(
            BytesIO(response.content),
            mimetype="image/png",
            as_attachment=True,
            download_name=filename,
        )
    except requests.RequestException as exc:
        return f"Download failed: {exc}", 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)