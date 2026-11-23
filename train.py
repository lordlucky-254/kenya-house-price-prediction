import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib, pathlib

df = pd.read_csv("data/nairobi_housing.csv")
print(df.head())
print(f"Rows: {len(df)} | Missing: {df.isna().sum().sum()}")

df["total_rooms"] = df["bedrooms"] + df["bathrooms"]
df["price_per_sqft"] = df["price_ksh"] / df["area_sqft"]
df["is_new"] = (df["age_years"] <= 5).astype(int)

X = df.drop(columns=["price_ksh", "price_per_sqft"])
y = df["price_ksh"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), ["location"])], remainder="passthrough")
for name, model in [("LinearRegression", LinearRegression()), ("RandomForest", RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1))]:
    pipe = Pipeline([("pre", pre), ("model", model)])
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)
    print(f"{name}: MAE={mean_absolute_error(y_test, pred):,.0f} RMSE={mean_squared_error(y_test, pred)**0.5:,.0f} R2={r2_score(y_test, pred):.3f}")

pipe = Pipeline([("pre", pre), ("model", RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1))])
pipe.fit(X_train, y_train)
pathlib.Path("models").mkdir(exist_ok=True)
joblib.dump(pipe, "models/house_price_model.pkl")
print("Saved to models/house_price_model.pkl")
