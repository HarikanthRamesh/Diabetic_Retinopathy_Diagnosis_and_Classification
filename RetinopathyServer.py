import os
import urllib.request
from flask import Flask, request, redirect, url_for, render_template
import numpy as np
# import matplotlib.pyplot as plt
from keras.models import load_model
from werkzeug.utils import secure_filename
import sqlite3
import cv2
from PIL import Image
import tensorflow as tf
import pandas as pd

import numpy as np
app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'
app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
    # Load the trained model and label encoder

# Load model ONCE (very important)
@tf.keras.utils.register_keras_serializable()
class Cast(tf.keras.layers.Layer):
    def call(self, inputs):
        return inputs

model = load_model("../best_model_densenet.h5", custom_objects={'Cast': Cast})

# Class labels
class_names = [
    "No_DR",
    "Mild",
    "Moderate",
    "Severe",
    "Proliferate_DR"
]

IMG_SIZE = (384, 384)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def model_predict(img_path):
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, IMG_SIZE)
    img = img / 255.0
    img = np.expand_dims(img, axis=0)

    preds = model.predict(img)
    pred_index = np.argmax(preds)
    confidence = float(np.max(preds))

    return class_names[pred_index], confidence

@app.route("/")
def index():
    return render_template("index1.html")


@app.route("/sign")
def sign():
    return render_template("index1.html")


@app.route("/next")
def next():
    return render_template("next.html")


@app.route("/signup", methods=["POST"])
def signup():
    va = dict(request.form)
    con = sqlite3.connect('signup.db')
    cur = con.cursor()
    cur.execute("insert into `info`  VALUES (?, ?, ?)",
                (va["username"], va["pas"], va["email"]))
    con.commit()
    con.close()
    return redirect("/")


@app.route("/signin", methods=["POST"])
def signin():
    va = dict(request.form)
    print(va)
    con = sqlite3.connect('signup.db')
    k = "select * from info "
    e = con.execute(k)
    n = e.fetchall()
    print(n)
    k = "select count(*) from info where username='%s' and password='%s'" % (
        va["username"], va["pas"])
    e = con.execute(k)
    n = e.fetchall()[0][0]
    if n != 0:
        return render_template("upload3.html")
    else:
        return render_template("index1.html")


@app.route('/store', methods=['POST'])
def upload_image():

    # Load remedies Excel
    df = pd.read_excel("REMEDIES.xlsx")

    if 'files[]' not in request.files:
        return render_template("upload3.html")

    files = request.files.getlist('files[]')

    # Clear old uploads
    for f in os.listdir(UPLOAD_FOLDER):
        os.remove(os.path.join(UPLOAD_FOLDER, f))

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Predict
            predicted_class, confidence = model_predict(filepath)

    print("Prediction:", predicted_class)

    # Filter remedies
    filtered_df = df[df['LEVEL'] == predicted_class]
    remedies_list = filtered_df['REMEDIES'].tolist()

    # Progress bar logic
    progress_style = "width:0%;font-size:3vw;background-color:violet;"
    val = 0
    vx = 0

    if predicted_class == 'No_DR':
        progress_style = "width:0%;font-size:3vw;background-color:violet;"
        val = 45
        vx = 0

    elif predicted_class == 'Mild':
        progress_style = "width:20%;font-size:3vw;background-color:blue;"
        val = 5
        vx = 20

    elif predicted_class == 'Moderate':
        progress_style = "width:40%;font-size:3vw;background-color:orange;"
        val = 20
        vx = 30

    elif predicted_class == 'Severe':
        progress_style = "width:100%;font-size:3vw;background-color:red;"
        val = 0
        vx = 120

    elif predicted_class == 'Proliferate_DR':
        progress_style = "width:80%;font-size:3vw;background-color:green;"
        val = 120
        vx = 30

    return render_template(
        "next.html",
        prediction=predicted_class,
        confidence=round(confidence * 100, 2),
        v=progress_style,
        val=val,
        vk=vx,
        remedies=remedies_list
    )


if __name__ == '__main__':
    app.run(debug=True, port="85")
