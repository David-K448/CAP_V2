from flask import Flask, render_template, request, session, redirect, url_for, flash, send_from_directory
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
        flash("No file selected.")
        return redirect('/')

    if file.filename == '':
        flash('No selected file')
        return redirect('/')

    MAX_FILESIZE = 25 * 1024 * 1024  # 25MB in bytes
    if file.content_length > MAX_FILESIZE:
        flash("File is too large. Max file size is 25MB.")
        return redirect('/')

    # Check the size of the file before saving
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILESIZE:
        flash("File is too large. Max file size is 25MB.")
        return redirect('/')

    try:
        file.save(os.path.join(os.getcwd(), 'tmp', file.filename))
    except FileNotFoundError:
        flash("File not found.")
        return redirect('/')

    return render_template('uploaded.html', file=file)




# Handle requests for the '/uploads/<filename>' URL pattern. occurs when a user clicks on a link or submits a form that includes the URL for a specific file
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    global fileNameA
    fileNameA = filename 
    print(fileNameA)
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
        op_api()
        return 'Button clicked successfully!', 200
    
#Perform speech transcription using the OpenAI Whisper model or the Google Cloud Speech-to-Text API.
# also saves original transcription to a directory for downloading later
def op_api():
    global transcriptionG
    #still deciding on whether to use OPENAI whisper model or google cloud speech-to-text api
    with open(os.path.join(app.config['UPLOAD_FOLDER'], fileNameA), 'rb') as audio_file:
        transcript = openai.Audio.transcribe(model="whisper-1", file=audio_file, max_tokens=2000)
        transcription_text = transcript.text
        transcriptionG = transcription_text
        print(transcription_text)

    # makes filename for the og_transcription_outputs directory
    txt_filename = fileNameA.split(".")[0]
    #creates file, filename is based off original files name, stored in
    with open(f'transcripts/og_transcription_output/{txt_filename}.txt', 'w') as f:
        f.write(transcription_text)

        

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
        ggl_trnslt()
        return 'Button clicked successfully!', 200
    
def ggl_trnslt():
    #create cloud translate instance
    translate_client = translate.Client()

    # detect the language in 'translationG'
    detection = translate_client.detect_language(transcriptionG)
    detected_lang = detection['language']
    print('Language Detected = ' + detected_lang +'\n')

    # get the list of available languages to translate to, based on the originally detected language -- not implemented yet
    
    # sets target language
    # ----- CHANGE THIS--- 
    # needs to be dynamic based on user selection, implementd via a selection box on the second html page 
    target_language = 'es'

    translation = translate_client.translate(
        transcriptionG,
        target_language=target_language
    )
    translated_text = translation['translatedText']
    print(translated_text)

    # makes filename for the og_transcription_outputs directory
    txt_translate_filename = target_language + '_' + fileNameA.split(".")[0]
    print(txt_translate_filename)
    #creates file, filename is based off original files name, adds language code, stored in
    with open(f'transcripts/translated_transp_output/{txt_translate_filename}.txt', 'w') as f:
        f.write(translated_text)




if __name__ == '__main__':
    app.run()
