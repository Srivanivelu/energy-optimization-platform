from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import numpy as np
from scipy.optimize import minimize

app = Flask(__name__)
app.secret_key = 'energy_optimization_2025'

# Admin PIN
ADMIN_PIN = '1234'

# Your energy data storage class
class EnergyDatabase:
    def __init__(self):
        # Non-renewable consumption data (from your dataset)
        self.nre_consumption = {
            '2024': {'coal': 1330, 'petroleum': 243, 'natural_gas': 70.5},
            '2025': {'coal': 1425, 'petroleum': 252, 'natural_gas': 73},
            '2026': {'coal': 1520, 'petroleum': 261, 'natural_gas': 75.5},
            '2027': {'coal': 1615, 'petroleum': 270, 'natural_gas': 78},
            '2028': {'coal': 1710, 'petroleum': 279, 'natural_gas': 80.5},
            '2029': {'coal': 1805, 'petroleum': 288, 'natural_gas': 83},
            '2030': {'coal': 1900, 'petroleum': 297, 'natural_gas': 85.5},
            '2031': {'coal': 1995, 'petroleum': 306, 'natural_gas': 88},
            '2032': {'coal': 2090, 'petroleum': 315, 'natural_gas': 90.5},
            '2033': {'coal': 2185, 'petroleum': 324, 'natural_gas': 93}
        }
        
        # Renewable availability (from your optimization results)
        self.renewable_availability = {
            '2024': {'wind': 88.90333, 'solar': 129.95, 'bio_power': 17.82655, 'small_hydro': 10.85519},
            '2025': {'wind': 94.41667, 'solar': 143.92, 'bio_power': 18.10433, 'small_hydro': 11.17043},
            '2026': {'wind': 99.93, 'solar': 157.89, 'bio_power': 18.38212, 'small_hydro': 11.48567},
            '2027': {'wind': 105.44333, 'solar': 171.86, 'bio_power': 18.65991, 'small_hydro': 11.80091},
            '2028': {'wind': 110.95667, 'solar': 185.83, 'bio_power': 18.9377, 'small_hydro': 12.11614},
            '2029': {'wind': 116.47, 'solar': 199.8, 'bio_power': 19.21549, 'small_hydro': 12.43138},
            '2030': {'wind': 121.98333, 'solar': 213.77, 'bio_power': 19.49328, 'small_hydro': 12.74662},
            '2031': {'wind': 127.49667, 'solar': 227.74, 'bio_power': 19.77106, 'small_hydro': 13.06185},
            '2032': {'wind': 133.01, 'solar': 241.71, 'bio_power': 20.04885, 'small_hydro': 13.37709},
            '2033': {'wind': 138.52333, 'solar': 255.68, 'bio_power': 20.32664, 'small_hydro': 13.69233}
        }
        
        # Your optimization results
        self.optimization_results = {
            '2024': {'total_met': 247.54, 'percentage': 17.21, 'demand': 1437.91},
            '2025': {'total_met': 267.61, 'percentage': 18.17, 'demand': 1472.93},
            '2026': {'total_met': 287.69, 'percentage': 19.08, 'demand': 1508.45},
            '2027': {'total_met': 307.76, 'percentage': 19.94, 'demand': 1544.47},
            '2028': {'total_met': 327.84, 'percentage': 20.77, 'demand': 1580.99},
            '2029': {'total_met': 347.92, 'percentage': 21.56, 'demand': 1618.01},
            '2030': {'total_met': 367.99, 'percentage': 22.32, 'demand': 1655.53},
            '2031': {'total_met': 388.07, 'percentage': 23.05, 'demand': 1693.55},
            '2032': {'total_met': 408.15, 'percentage': 23.75, 'demand': 1732.07},
            '2033': {'total_met': 428.22, 'percentage': 24.42, 'demand': 1771.09}
        }

# Initialize database
db = EnergyDatabase()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_login():
    return render_template('admin_login.html')

@app.route('/admin/auth', methods=['POST'])
def admin_auth():
    pin = request.form.get('pin')
    if pin == ADMIN_PIN:
        session['admin'] = True
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html', error='Invalid PIN')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/api/energy_data/<year>')
def get_energy_data(year):
    if year not in db.optimization_results:
        return jsonify({'error': 'Year not found'}), 404
    
    renewable_data = db.renewable_availability[year]
    nre_data = db.nre_consumption[year]
    optimization_data = db.optimization_results[year]
    
    return jsonify({
        'year': year,
        'renewable': renewable_data,
        'non_renewable': nre_data,
        'optimization': optimization_data
    })

@app.route('/api/all_years_data')
def get_all_years_data():
    years_data = {}
    for year in db.optimization_results.keys():
        years_data[year] = {
            'renewable': db.renewable_availability[year],
            'non_renewable': db.nre_consumption[year],
            'optimization': db.optimization_results[year]
        }
    return jsonify(years_data)

@app.route('/api/update_data', methods=['POST'])
def update_data():
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    year = data.get('year')
    category = data.get('category')
    values = data.get('values')
    
    if category == 'renewable':
        db.renewable_availability[year] = values
    elif category == 'non_renewable':
        db.nre_consumption[year] = values
    elif category == 'optimization':
        db.optimization_results[year] = values
    
    return jsonify({'success': True})

@app.route('/api/run_optimization/<year>')
def run_optimization(year):
    if year not in db.renewable_availability:
        return jsonify({'error': 'Year not found'}), 404
    
    availability = db.renewable_availability[year]
    demand = db.optimization_results[year]['demand']
    
    # Run optimization (your exact algorithm)
    sources = ["wind", "solar", "bio_power", "small_hydro"]
    availability_array = np.array([availability[src] for src in sources])
    
    x0 = np.full_like(availability_array, demand / len(availability_array))
    
    def objective(x):
        return (np.sum(x) - demand) ** 2
    
    bounds = [(0, a) for a in availability_array]
    constraints = [{'type': 'ineq', 'fun': lambda x: demand - np.sum(x)}]
    
    result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
    
    if result.success:
        allocation = result.x
        total_met = np.sum(allocation)
        percentage_met = (total_met / demand) * 100
        
        allocation_dict = {
            sources[i]: allocation[i] for i in range(len(sources))
        }
        
        return jsonify({
            'success': True,
            'allocation': allocation_dict,
            'total_met': total_met,
            'percentage_met': percentage_met,
            'demand': demand
        })
    
    return jsonify({'success': False, 'error': 'Optimization failed'})

# Cloud deployment configuration
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
