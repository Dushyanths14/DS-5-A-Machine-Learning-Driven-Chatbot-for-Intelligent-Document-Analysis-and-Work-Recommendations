import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./Login";
import StatePrescriptions from "./StatePrescriptions";
import ProviderPrescriptions from "./ProviderPrescriptions";
import BrandPrescriptions from "./BrandPrescriptions";
import AIInsights from './AIInsights';

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<Login />} />
                <Route path="/state-prescriptions" element={<StatePrescriptions />} />
                <Route path="/provider-prescriptions" element={<ProviderPrescriptions />} />
                <Route path="/brand-prescriptions" element={<BrandPrescriptions />} />
            </Routes>
        </Router>
    );
}

export default App;