from fastapi import FastAPI, UploadFile, File
import pandas as pd
import joblib
from joblib import load, dump
import os

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

model_path = os.path.join(UPLOAD_DIR, "model.joblib")

@app.post("/upload-data")
async def upload_data(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)
    df.to_csv(os.path.join(UPLOAD_DIR, file.filename), index=False)
    
    df = df.dropna()
    if 'Churn' not in df.columns:
        return {"error": "Target column 'Churn' not found."}
    
    df['Churn'] = LabelEncoder().fit_transform(df['Churn'])
    df = pd.get_dummies(df.select_dtypes(include=['object', 'int', 'float']), drop_first=True)

    X = df.drop('Churn', axis=1)
    y = df['Churn']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    dump(model, model_path)

    return {
        "message": f"File '{file.filename}' processed.",
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "model_saved": model_path,
        "log_saved": os.path.join(UPLOAD_DIR, "predictions_log.txt")
    }

@app.post("/predict")
def predict(data: dict):
    try:
        model = joblib.load("uploads/model.joblib")
    except FileNotFoundError:
        return {"error": "Model not found. Please upload and train data first."}
    
    try:
        df = pd.DataFrame([data])
        prediction = model.predict(df)
        return {"prediction": prediction.tolist()}
    except Exception as e:
        return {"error": str(e)}