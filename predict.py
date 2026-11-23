import joblib, pandas as pd
model = joblib.load("models/house_price_model.pkl")
sample = pd.DataFrame([{"location": "Westlands", "bedrooms": 3, "bathrooms": 2, "area_sqft": 1500, "age_years": 5, "parking": 1, "furnished": 1, "near_school": 1, "total_rooms": 5, "is_new": 1}])
print(f"Predicted price: KES {model.predict(sample)[0]:,.0f}")
