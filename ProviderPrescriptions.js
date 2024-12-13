import React, { useEffect, useState } from 'react';
import axios from 'axios';

function ProviderPrescriptions() {
  const [data, setData] = useState([]);
  const [insights, setInsights] = useState({});
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('jwt');
        const response = await axios.get('http://127.0.0.1:5000/api/prescriptions', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setData(response.data.data);
        setInsights(response.data.insights);
      } catch (err) {
        setError('Failed to fetch data. Please try again.');
      }
    };

    fetchData();
  }, []);

  return (
    <div>
      <h2>Prescriptions for Provider Type</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <div>
        <h3>Insights</h3>
        <ul>
          {Object.entries(insights).map(([key, value]) => (
            <li key={key}>
              <strong>{key}:</strong> {value}
            </li>
          ))}
        </ul>
      </div>
      <table border="1">
        <thead>
          <tr>
            <th>Provider Type</th>
            <th>Brand Name</th>
            <th>Generic Name</th>
            <th>Total Claims</th>
            <th>Average Claims Per Drug</th>
            <th>Average Cost Per 30-Day Fill</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr key={index}>
              <td>{row['Provider Type']}</td>
              <td>{row['Brand Name']}</td>
              <td>{row['Generic Name']}</td>
              <td>{row['Total Claims']}</td>
              <td>{row['Average Claims Per Drug']}</td>
              <td>{row['Average Cost Per 30-Day Fill']}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ProviderPrescriptions;
