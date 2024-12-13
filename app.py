from flask import Flask, jsonify, request  # Include request here
import sqlite3


#Enable CORS
from flask_cors import CORS



app = Flask(__name__)
CORS(app)

# Function to connect to the database
def get_db_connection():
    conn = sqlite3.connect('medicare.db')  # Path to your database
    conn.row_factory = sqlite3.Row  # Enables column access by name
    return conn

# Test database connection
@app.route('/api/test', methods=['GET'])
def test_db():
    conn = get_db_connection()
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row['name'] for row in cursor.fetchall()]
    conn.close()
    return jsonify(tables)


#Search Prescriptions
#Let’s add a route to search for drugs by their brand or generic names.

@app.route('/api/prescriptions/search', methods=['GET'])
def search_prescriptions():
    drug_name = request.args.get('drug_name', '')  # Get 'drug_name' from query parameters
    conn = get_db_connection()
    cursor = conn.execute(
        "SELECT * FROM prescriptions WHERE Brnd_Name LIKE ? OR Gnrc_Name LIKE ? LIMIT 10",
        (f'%{drug_name}%', f'%{drug_name}%')  # Use wildcards for partial matching
    )
    prescriptions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(prescriptions)

#Filter by Provider or State
#Add a route to filter prescriptions by provider or state.

@app.route('/api/prescriptions/filter', methods=['GET'])
def filter_prescriptions():
    provider_name = request.args.get('provider_name', '')
    state_abbreviation = request.args.get('state_abbreviation', '')

    query = "SELECT * FROM prescriptions WHERE 1=1"  # Base query
    params = []

    if provider_name:
        query += " AND Prscrbr_Last_Org_Name LIKE ?"
        params.append(f'%{provider_name}%')
    if state_abbreviation:
        query += " AND Prscrbr_State_Abrvtn = ?"
        params.append(state_abbreviation)

    conn = get_db_connection()
    cursor = conn.execute(query, params)
    prescriptions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(prescriptions)

#Add User Registration
#Add an endpoint for new users to register by providing a username and password.
# The password will be hashed before storing it in the database.

from flask_bcrypt import Bcrypt

# Initialize Bcrypt for hashing passwords
bcrypt = Bcrypt(app)


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')  # Default role is 'user'
    state_code = data.get('state_code')
    provider_type = data.get('provider_type')
    brand_name = data.get('brand_name')

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    # Hash the password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Insert the user into the database
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password, role, state_code, provider_type, brand_name) VALUES (?, ?, ?, ?, ?, ?)",
            (username, hashed_password, role, state_code, provider_type, brand_name)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"message": "Username already exists"}), 400
    finally:
        conn.close()

    return jsonify({"message": "User registered successfully"}), 201


#Add User Login
#The login endpoint will authenticate the user and return a JWT token if the credentials are valid.

from flask_jwt_extended import JWTManager, create_access_token

# Initialize JWT
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Replace with a strong secret key
jwt = JWTManager(app)


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if not user or not bcrypt.check_password_hash(user['password'], password):
        return jsonify({"message": "Invalid username or password"}), 401

    # Add user details to the JWT token
    additional_claims = {
        "role": user["role"],
        "state_code": user["state_code"],
        "provider_type": user["provider_type"],
        "brand_name": user["brand_name"]
    }
    access_token = create_access_token(identity=username, additional_claims=additional_claims)

    return jsonify({"access_token": access_token}), 200


#Secure API Endpoints
#Use the @jwt_required() decorator to secure your API endpoints.
#Users must include the JWT token in the Authorization header to access these routes.
#page and size query parameters.

import pandas as pd
from sklearn.linear_model import LinearRegression
from flask import Flask, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt

@app.route('/api/prescriptions', methods=['GET'])
@jwt_required()
def get_prescriptions():
    claims = get_jwt()  # Extract user claims from the JWT
    role = claims.get("role")
    state_code = claims.get("state_code")
    provider_type = claims.get("provider_type")
    brand_name = claims.get("brand_name")

    conn = get_db_connection()
    query = "SELECT * FROM prescriptions WHERE 1=1"
    params = []

    # Filter prescriptions based on the user's role
    if role == "state_user" and state_code:
        query += " AND Prscrbr_State_Abrvtn = ?"
        params.append(state_code)
    elif role == "provider_user" and provider_type:
        query += " AND Prscrbr_Type = ?"
        params.append(provider_type)
    elif role == "brand_user" and brand_name:
        query += " AND Brnd_Name = ?"
        params.append(brand_name)

    cursor = conn.execute(query, params)
    prescriptions = [dict(row) for row in cursor.fetchall()]  # Fetch all rows
    conn.close()

    if not prescriptions:
        return jsonify({"data": [], "insights": "No data available"}), 200

    # Filter relevant columns based on role
    data = []
    if role == "state_user":
        data = [{  # Include only state-specific columns
            "State": row.get("Prscrbr_State_Abrvtn"),
            "Brand Name": row.get("Brnd_Name"),
            "Generic Name": row.get("Gnrc_Name"),
            "Total Claims": row.get("Tot_Clms"),
            "Total Cost Per Provider": row.get("Total_Cost_Per_Provider"),
            "Average Claims Per Drug": row.get("Average_Claims_Per_Drug"),
        } for row in prescriptions]
    elif role == "provider_user":
        data = [{  # Include only provider-specific columns
            "Provider Type": row.get("Prscrbr_Type"),
            "Brand Name": row.get("Brnd_Name"),
            "Generic Name": row.get("Gnrc_Name"),
            "Total Claims": row.get("Tot_Clms"),
            "Average Claims Per Drug": row.get("Average_Claims_Per_Drug"),
            "Average Cost Per 30-Day Fill": row.get("Average_Cost_Per_30day_Fill"),
        } for row in prescriptions]
    elif role == "brand_user":
        data = [{  # Include only brand-specific columns
            "Brand Name": row.get("Brnd_Name"),
            "State": row.get("Prscrbr_State_Abrvtn"),
            "Total Claims": row.get("Tot_Clms"),
            "Total Cost Per Provider": row.get("Total_Cost_Per_Provider"),
            "Average Cost Per 30-Day Fill": row.get("Average_Cost_Per_30day_Fill"),
        } for row in prescriptions]

    # Convert data to DataFrame
    df = pd.DataFrame(data)

    # Predictive Analytics
    predicted_claims = None
    if not df.empty and "Tot_Clms" in df and "Year" in df.columns:
        # Ensure columns are numeric and drop rows with missing values
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
        df = df.dropna(subset=["Year", "Tot_Clms"])
        if not df.empty:
            model = LinearRegression()
            X = df[["Year"]].values
            y = df["Tot_Clms"].values
            model.fit(X, y)
            next_year = [[max(df["Year"]) + 1]]
            predicted_claims = model.predict(next_year)[0]

    # Role-Based Insights
    insights = {}
    if role == "state_user" and state_code:
        state_data = df[df["State"] == state_code]
        if not state_data.empty:
            top_drugs = state_data["Brand Name"].value_counts().head(3).index.tolist()
            insights["Top Drugs in Your State"] = top_drugs
            insights["Opportunities"] = f"Promote these drugs: {', '.join(top_drugs)}."

    elif role == "provider_user" and provider_type:
        provider_data = df[df["Provider Type"] == provider_type]
        if not provider_data.empty:
            avg_claims = provider_data["Total Claims"].mean()
            top_drugs = provider_data["Brand Name"].value_counts().head(3).index.tolist()
            insights["Provider Comparison"] = f"Your provider type prescribes {top_drugs[0]} {avg_claims}% more than average."
            insights["Top Drugs"] = top_drugs

    elif role == "brand_user" and brand_name:
        brand_data = df[df["Brand Name"] == brand_name]
        if not brand_data.empty:
            popular_states = brand_data["State"].value_counts().head(2).index.tolist()
            top_states_for_claims = (
                brand_data.groupby("State")["Total Claims"].sum()
                .sort_values(ascending=False)
                .head(3)
                .index.tolist()
            )
            insights["Performance"] = f"{brand_name} is most popular in {', '.join(popular_states)}."
            insights["Top States for Claims Volume"] = f"Top states for {brand_name} based on total claims are: {', '.join(top_states_for_claims)}."

    # Include predictive insights
    if predicted_claims is not None:
        insights["Predicted Claims Next Year"] = int(predicted_claims)

    return jsonify({"data": data, "insights": insights})




# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=5000)

