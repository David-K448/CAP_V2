from flask import Flask, render_template, request, session, redirect, url_for, flash, send_from_directory, send_file
import os
import io
import tempfile
import atexit
import shutil
import time
import openai
from google.cloud import translate_v2 as translate
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'tmp'
last_click_time = 0

api_key = os.getenv('OPENAI_KEY')
openai.api_key = api_key
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"C:\Users\killi\OneDrive\Desktop\stuffgpt\translation-stuff-386514-c6a00efd32ba.json"
fileNameA = ''
fileNameB = ''


# Handle requests to the root URL ('/').
@app.route('/')
def index():
    return render_template('index.html')

# Handle the POST request to the '/upload' URL.
@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['file']
    except KeyError:
        # flash("No file selected.")
        # return redirect('/')
        return '''
            <script>
                window.location.href = "/";
                alert("No file selected.");
            </script>'''

    if file.filename == '':
        # flash('No selected file')
        # return redirect('/')
         return '''
            <script>
                window.location.href = "/";
                alert("No file selected.");
            </script>'''

    MAX_FILESIZE = 25 * 1024 * 1024  # 25MB in bytes
    if file.content_length > MAX_FILESIZE:
        # flash("File is too large. Max file size is 25MB.")
        # return redirect('/')
        return '''
            <script>
                window.location.href = "/";
                alert("File is too large. Max file size is 25MB.");
            </script>'''

    # Check the size of the file before saving
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILESIZE:
        # flash("File is too large. Max file size is 25MB.")
        # return redirect('/')
        return '''
            <script>
                window.location.href = "/";
                alert("File is too large. Max file size is 25MB.");
            </script>'''

    try:
        file.save(os.path.join(os.getcwd(), 'tmp', file.filename))
    except FileNotFoundError:
        # flash("File not found.")
        # return redirect('/')
        return '''
            <script>
                window.location.href = "/";
                alert("File is too large. Max file size is 25MB.");
            </script>'''

    return render_template('uploaded.html', file=file)



# Handle requests for the '/uploads/<filename>' URL pattern. occurs when a user clicks on a link or submits a form that includes the URL for a specific file
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    global fileNameA
    fileNameA = filename 
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



# Handle the POST request to the '/scribe_btn_click' URL when a button is clicked.
@app.route('/scribe_btn_click', methods=['POST'])
def button_click():
    global last_click_time, fileNameA
    now = time.time()
    if now - last_click_time < 5:
        # Ignore the button click if it is clicked too quickly
        return '', 204
    else:
        last_click_time = now
        # Handle the button click
        transcription_text = op_api() #gets transcription
        return transcription_text, 200 #returns to the js script 
       
    
#Perform speech transcription using the OpenAI Whisper model or the Google Cloud Speech-to-Text API.
# also saves original transcription to a directory for downloading later
def op_api():
    global transcriptionG
    #still deciding on whether to use OPENAI whisper model or google cloud speech-to-text api
    with open(os.path.join(app.config['UPLOAD_FOLDER'], fileNameA), 'rb') as audio_file:
        transcript = openai.Audio.transcribe(model="whisper-1", file=audio_file, max_tokens=2000)
        transcription_text = transcript.text
        transcriptionG = transcription_text
        # print(transcription_text)

    # makes filename for the og_transcription_outputs directory
    txt_filename = fileNameA.split(".")[0]
    #creates file, filename is based off original files name, stored in
    with open(f'transcripts/og_transcription_output/{txt_filename}.txt', 'w') as f:
        f.write(transcription_text)

    return transcription_text # returns transcription string

# DOWNLOADS ORIGINAL TRANSCRIPTION ON BUTTON CLICK 
@app.route('/transcribe_dwnld_btn_click')
def download_transcription():
    txt_filename = fileNameA.split(".")[0]
    file_path = f'transcripts/og_transcription_output/{txt_filename}.txt'
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found."
    
@app.route('/translate_dwnld_btn_click')
def download_translation():
    txt_filename = fileNameB
    file_path = f'transcripts/translated_transp_output/{txt_filename}.txt'
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found."
    

# performs the translation using the google cloud translation api
@app.route('/translate_btn_click', methods=['POST'])
def translate_button_click():
    global last_click_time, fileNameA
    now = time.time()
    if now - last_click_time < 5:
        # Ignore the button click if it is clicked too quickly
        return '', 204
    else:
        last_click_time = now
        # Handle the button click
        selected_lang = request.form.get('selectedValue')
        translated_text = ggl_trnslt(selected_lang)
        return translated_text, 200
    
def ggl_trnslt(selected_lang):
    global fileNameB
    #create cloud translate instance
    translate_client = translate.Client()

    selected_lang=selected_lang
    

    # detect the language in 'translationG'
    detection = translate_client.detect_language(transcriptionG)
    detected_lang = detection['language']
    print('Language Detected = ' + detected_lang +'\n')

    # get the list of available languages to translate to, based on the originally detected language -- not implemented yet

    translation = translate_client.translate(
        transcriptionG,
        target_language=selected_lang
    )
    translated_text = translation['translatedText']
    print(translated_text)

    # makes filename for the og_transcription_outputs directory
    txt_translate_filename = selected_lang + '_' + fileNameA.split(".")[0]
    fileNameB = txt_translate_filename
    #print("filenameB=" + fileNameB)
    #creates file, filename is based off original files name, adds language code, stored in
    with open(f'transcripts/translated_transp_output/{txt_translate_filename}.txt', 'w') as f:
        f.write(translated_text)

    return translated_text




if __name__ == '__main__':
    app.run()
