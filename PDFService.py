from flask import Flask, request, jsonify, render_template_string
import requests
import json
from flask_cors import CORS
from PIL import Image
import io
from fpdf import FPDF
import base64
import uuid


app = Flask(__name__)
CORS(app)

@app.route('/imagenes', methods=['POST'])
def generar_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No se enviaron archivos"}), 400

        archivos = request.files.getlist('file')

        if not archivos:
            return jsonify({"error": "Lista de archivos vacía"}), 400

        imgArray = []
        for archivo in archivos:
            img = Image.open(archivo.stream).convert("RGB")
            imgArray.append(img)

        if not imgArray:
            return jsonify({"error": "No se pudieron procesar imágenes"}), 400

        # Configuración del PDF
        num_img = len(imgArray)
        num_img_page = 4 if num_img > 1 else 1
        margin = 10
        pages = (num_img + num_img_page - 1) // num_img_page
        ancho_total = (941 * 2) + (3 * margin)
        alto_total = (1224 * 2) + (3 * margin)
        ancho, alto = int(ancho_total / 2 - 1.5 * margin), int(alto_total / 2 - 1.5 * margin)

        pdf_pages = []

        for page in range(pages):
            combined = Image.new('RGB', (ancho_total, alto_total), (255, 255, 255))
            start = page * num_img_page
            end = min(start + num_img_page, num_img)

            for i in range(start, end):
                img = imgArray[i].resize((ancho, alto))
                x = ((i - start) % 2) * (ancho + margin) + margin
                y = ((i - start) // 2) * (alto + margin) + margin
                combined.paste(img, (x, y))

            pdf_pages.append(combined)

        # Guardar el PDF en memoria
        guid_pdf = str(uuid.uuid4())
        output_pdf = io.BytesIO()
        pdf_pages[0].save(output_pdf, format="PDF", save_all=True, append_images=pdf_pages[1:], resolution=300)
        output_pdf.seek(0)

        # Convertir PDF a base64 y guardar
        base64_pdf = base64.b64encode(output_pdf.read()).decode("utf-8")
        with open(f"{guid_pdf}.txt", "w") as f:
            f.write(base64_pdf)

        return jsonify({
            "message": "PDF generado exitosamente",
            "NamePDF": guid_pdf
            # "base64": base64_pdf  # <- puedes descomentar si deseas retornar también el base64
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    

# **************************************************************************************

@app.route('/namefile', methods=['GET'])
def mi_vista():

    filename = request.args.get('file')
    # almacenamos en uan variable el html en el que se va a visualizar el pdf esto con el fin de que las personas
    # puedan ver el pdf sin tener que descargarlo de manera manual
    # el pdf se muestra en un iframe en el html, para que el tamaño sea el mismo que el del viewport
    # el tamaño del iframe se ajusta al tamaño del viewport del dispositivo del usuario
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ title }}</title>
    </head>
    <body>
        <object data="data:application/pdf;base64,{{ pdfBase64txt }}"  width="100%" height="100%">
    </body>

    <style>
        html, body {
        height: 100%; 
        margin: 0;    
        padding: 0;  
        }

        body{
        display: flex;}s

    </style>
    </html>
    """
    # se extraen los datos para cargarlo en la plantilla
    with open(f"{filename}.txt", 'r') as file_pdf_base64:
        base64_pdf = file_pdf_base64.read()

    data = {
        'pdfBase64txt': base64_pdf
    }
    return render_template_string(html_template, **data)


@app.route('/ExtractBase64img', methods= ['POST'])
def extract_base64():
    dataImgB64= []
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        File_zip = request.files.getlist()
        for File_zip in File_zip:
            encode_data= File_zip.read()
            data_str= base64.b64encode(encode_data)
            decode_string= data_str.decode("utf-8")
            # data_str= data_str.strip('"')
            # if "base64,"  in data_str:
            #     base64_str= data_str.split('base64,')[1] 
            # base64_str= base64_str.encode('utf-8')
            # print(base64_str)
            dataImgB64.append({"Base64img":decode_string})



        return jsonify(dataImgB64), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500
    
if __name__ == '__main__':
    app.run(host="127.0.0.1", port="8081")