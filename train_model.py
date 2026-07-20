import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pickle
import warnings
warnings.filterwarnings('ignore')

DATA_PATH = 'mental_health_dataset.csv'

df = pd.read_csv(DATA_PATH)
df['target'] = (df['mental_health_condition'] != 'Normal').astype(int)

# Match the feature engineering used in app.py
X_raw = pd.DataFrame()
X_raw['sleep_duration'] = df['sleep_hours']
X_raw['quality_of_sleep'] = df['sleep_quality']
# Map physical_activity_days to the same scale as app.py (30/50/75)
def map_activity(days):
    if days <= 1: return 30
    if days <= 4: return 50
    return 75
X_raw['physical_activity_level'] = df['physical_activity_days'].apply(map_activity)
X_raw['stress_level'] = df['stress_level']
X_raw['heart_rate'] = df['heart_rate']
X_raw['daily_steps'] = df['daily_steps']

X_raw['sleep_efficiency'] = X_raw['sleep_duration'] * X_raw['quality_of_sleep'] / 10
X_raw['activity_stress_ratio'] = X_raw['physical_activity_level'] / (X_raw['stress_level'] + 1)
X_raw['sleep_quality_ratio'] = X_raw['quality_of_sleep'] / X_raw['sleep_duration']

y = df['target'].values

print("Target: %d normal, %d at-risk" % ((y==0).sum(), (y==1).sum()))

# Undersample majority to balance
normal_idx = np.where(y == 0)[0]
atrisk_idx = np.where(y == 1)[0]
np.random.seed(42)
min_size = min(len(normal_idx), len(atrisk_idx))
normal_subset = np.random.choice(normal_idx, size=min_size, replace=False)
atrisk_subset = np.random.choice(atrisk_idx, size=min_size, replace=False)
balanced_idx = np.concatenate([normal_subset, atrisk_subset])
X_bal = X_raw.iloc[balanced_idx]
y_bal = y[balanced_idx]

print("Balanced: %d normal, %d at-risk" % ((y_bal==0).sum(), (y_bal==1).sum()))

X_train, X_test, y_train, y_test = train_test_split(
    X_bal, y_bal, test_size=0.2, random_state=42, stratify=y_bal
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)
model.fit(X_train_scaled, y_train)

y_pred = model.predict(X_test_scaled)
print("\nTest results:")
print(classification_report(y_test, y_pred, target_names=['Normal', 'At Risk']))

feature_names = list(X_raw.columns)
importances = model.feature_importances_
fi_df = pd.DataFrame({'feature': feature_names, 'importance': importances})
fi_df = fi_df.sort_values('importance', ascending=False)
print("\nFeature Importance:")
print(fi_df.to_string(index=False))

model_data = {
    'model': model,
    'scaler': scaler,
    'feature_names': feature_names,
    'feature_importance': fi_df,
}

with open('mental_health_model.pkl', 'wb') as f:
    pickle.dump(model_data, f)

print("\nSaved to mental_health_model.pkl")
