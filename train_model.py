import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

print("Starting AI model training...")

data = pd.read_csv("data.csv")

print("Dataset loaded successfully!")

X = data[["temperature", "occupancy", "electricity", "hours"]]
y = data["usage_level"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

print("Training AI model...")

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

accuracy = model.score(X_test, y_test)

print("AI Model trained successfully!")
print("Model Accuracy:", round(accuracy * 100, 2), "%")

joblib.dump(model, "model.pkl")

print("Model saved as model.pkl")
print("Training completed successfully!")