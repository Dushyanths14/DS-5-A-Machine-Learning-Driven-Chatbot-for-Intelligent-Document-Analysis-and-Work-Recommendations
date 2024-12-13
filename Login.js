import React, { useState } from "react";
import axios from "axios";

function Login() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [role, setRole] = useState("state_user");

    const handleLogin = async () => {
        try {
            const response = await axios.post("http://127.0.0.1:5000/login", {
                username,
                password,
            });

            const token = response.data.access_token;
            localStorage.setItem("jwt", token); // Store token for later use
            alert("Login successful!");

            // Redirect based on role
            if (role === "state_user") {
                window.location.href = "/state-prescriptions";
            } else if (role === "provider_user") {
                window.location.href = "/provider-prescriptions";
            } else if (role === "brand_user") {
                window.location.href = "/brand-prescriptions";
            }
        } catch (error) {
            console.error("Login error:", error.response?.data || error.message);
            alert("Login failed! Please check your credentials.");
        }
    };

    return (
        <div>
            <h2>Login</h2>
            <input
                type="text"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
            />
            <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
            />
            <select value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="state_user">State User</option>
                <option value="provider_user">Provider User</option>
                <option value="brand_user">Brand User</option>
            </select>
            <button onClick={handleLogin}>Login</button>
        </div>
    );
}

export default Login;
