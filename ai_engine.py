import numpy as np
from datetime import datetime, timedelta
import sqlite3
from database import get_db_connection

class AIEngine:
    """
    AI & Intelligence Engine for Smart Resource Automation Platform.
    Implements statistical anomaly detection (Z-Score & IQR), wastage identification,
    time-series diurnal forecasting, composite efficiency scoring, and automated insight generation.
    """

    def __init__(self):
        pass

    def get_resource_readings(self, resource_id, limit=168):
        """Fetch the most recent readings for a resource (default 168 = 7 days of hourly data)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT value, occupancy, timestamp 
            FROM readings 
            WHERE resource_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (resource_id, limit))
        rows = cursor.fetchall()
        conn.close()
        # Return in chronological order
        return list(reversed(rows))

    def detect_anomaly(self, resource_id, current_value=None, z_threshold=2.5):
        """
        Detects statistical anomalies using Z-Score and Interquartile Range (IQR).
        Returns a dict with is_anomaly, z_score, iq_outlier, severity, and details.
        """
        readings = self.get_resource_readings(resource_id, limit=72)
        if len(readings) < 10:
            return {'is_anomaly': False, 'reason': 'Insufficient historical data', 'z_score': 0.0}

        values = [r['value'] for r in readings]
        if current_value is None:
            current_value = values[-1]
            hist_values = values[:-1]
        else:
            hist_values = values

        mean = np.mean(hist_values)
        std = np.std(hist_values)

        # Protect against zero variance
        if std == 0:
            std = 0.001

        z_score = (current_value - mean) / std

        # IQR calculation
        q75, q25 = np.percentile(hist_values, [75, 25])
        iqr = q75 - q25
        iqr_upper = q75 + (1.5 * iqr)
        iqr_lower = q25 - (1.5 * iqr)
        is_iqr_outlier = bool(current_value > iqr_upper or current_value < iqr_lower)

        is_anomaly = bool(abs(z_score) >= z_threshold or (abs(z_score) >= 2.0 and is_iqr_outlier))

        severity = 'LOW'
        if is_anomaly:
            if abs(z_score) >= 3.5:
                severity = 'CRITICAL'
            elif abs(z_score) >= 2.8:
                severity = 'HIGH'
            else:
                severity = 'MEDIUM'

        pct_deviation = round(((current_value - mean) / mean) * 100, 1) if mean != 0 else 0.0

        return {
            'is_anomaly': is_anomaly,
            'current_value': round(float(current_value), 2),
            'baseline_mean': round(float(mean), 2),
            'baseline_std': round(float(std), 2),
            'z_score': round(float(z_score), 2),
            'is_iqr_outlier': is_iqr_outlier,
            'pct_deviation': pct_deviation,
            'severity': severity
        }

    def detect_wastage(self, resource_id):
        """
        Identifies resource wastage patterns:
        1. Ghost Power: Room or lab has 0 occupancy, but usage > 25% capacity.
        2. Off-Hours Base Load Violation: High power draw during 22:00-05:00.
        3. Nocturnal Continuous Water Leak: Sustained non-zero flow between 01:00-04:00.
        4. Idle Server Node: Bandwidth or compute capacity allocated with < 15% utilization.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resources WHERE id = ?", (resource_id,))
        resource = cursor.fetchone()
        if not resource:
            conn.close()
            return []

        readings = self.get_resource_readings(resource_id, limit=24)
        conn.close()

        wastage_flags = []
        if not readings:
            return wastage_flags

        latest = readings[-1]
        latest_val = latest['value']
        latest_occ = latest['occupancy'] if latest['occupancy'] is not None else 0
        latest_time = datetime.strptime(latest['timestamp'], '%Y-%m-%d %H:%M:%S')
        cap = resource['capacity']

        # 1. Ghost Power in computing or room
        if resource['type'] in ['computing', 'room', 'electricity'] and latest_occ == 0:
            if latest_val > (cap * 0.25):
                wastage_flags.append({
                    'type': 'ghost_load',
                    'severity': 'HIGH',
                    'title': f'Ghost Power Detected in {resource["name"]}',
                    'description': f'Zero room occupancy recorded, but drawing {latest_val} {resource["unit"]} ({round((latest_val/cap)*100, 1)}% of capacity).',
                    'recommendation': 'Trigger automated sleep mode for idle terminals and dim perimeter fixtures.'
                })

        # 2. Nocturnal water leak
        if resource['type'] == 'water':
            # Check last 6 hours if during night
            night_readings = [r['value'] for r in readings if 1 <= datetime.strptime(r['timestamp'], '%Y-%m-%d %H:%M:%S').hour <= 5]
            if len(night_readings) >= 3 and min(night_readings) > 20.0:
                wastage_flags.append({
                    'type': 'water_leak',
                    'severity': 'CRITICAL',
                    'title': f'Continuous Off-Hour Water Flow in {resource["name"]}',
                    'description': f'Sustained nocturnal water flow of ~{round(float(np.mean(night_readings)), 1)} L/min detected between 01:00-05:00 AM without building occupancy.',
                    'recommendation': 'Isolate sub-riser via automated solenoid valve and dispatch plumbing maintenance team.'
                })

        # 3. Off-hours electricity spike
        if resource['type'] == 'electricity' and (latest_time.hour >= 22 or latest_time.hour <= 5):
            if latest_val > (cap * 0.65):
                wastage_flags.append({
                    'type': 'off_hours_spike',
                    'severity': 'HIGH',
                    'title': f'Excessive Night-Time Electricity Consumption in {resource["name"]}',
                    'description': f'Electricity draw reached {latest_val} kWh during scheduled curfew hours (expected < {round(cap * 0.3, 1)} kWh).',
                    'recommendation': 'Verify automated HVAC setback schedule and inspect unpowered lab equipment.'
                })

        # 4. Chronic underutilization
        all_vals = [r['value'] for r in readings]
        avg_val = np.mean(all_vals)
        if (avg_val / cap) < 0.18 and resource['type'] in ['computing', 'room']:
            wastage_flags.append({
                'type': 'underutilization',
                'severity': 'MEDIUM',
                'title': f'Low Utilization Detected in {resource["name"]}',
                'description': f'Average operational utilization is only {round((avg_val/cap)*100, 1)}% over the past 24 hours.',
                'recommendation': 'Consolidate active workloads to primary server cluster and schedule low-power hibernation.'
            })

        return wastage_flags

    def calculate_utilization(self, resource_id=None):
        """
        Calculates current and 24-hour average resource utilization rates.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        if resource_id:
            cursor.execute("SELECT * FROM resources WHERE id = ?", (resource_id,))
            resources = cursor.fetchall()
        else:
            cursor.execute("SELECT * FROM resources")
            resources = cursor.fetchall()

        results = {}
        for res in resources:
            r_id = res['id']
            cap = res['capacity']
            curr = res['current_usage']
            curr_pct = round((curr / cap) * 100, 1) if cap > 0 else 0.0

            readings = self.get_resource_readings(r_id, limit=24)
            if readings:
                vals = [r['value'] for r in readings]
                avg_24h = float(np.mean(vals))
                avg_24h_pct = round((avg_24h / cap) * 100, 1) if cap > 0 else 0.0
                peak_24h = float(np.max(vals))
                min_24h = float(np.min(vals))
            else:
                avg_24h = curr
                avg_24h_pct = curr_pct
                peak_24h = curr
                min_24h = curr

            results[r_id] = {
                'id': r_id,
                'name': res['name'],
                'type': res['type'],
                'capacity': cap,
                'current_usage': curr,
                'unit': res['unit'],
                'status': res['status'],
                'current_pct': curr_pct,
                'avg_24h_pct': avg_24h_pct,
                'avg_24h': round(avg_24h, 1),
                'peak_24h': round(peak_24h, 1),
                'min_24h': round(min_24h, 1)
            }

        conn.close()
        return results if resource_id is None else results.get(resource_id)

    def calculate_efficiency_score(self):
        """
        Calculates holistic Resource Efficiency Score (0-100).
        Evaluates utilization balance, active anomalies, wastage instances, and automated interventions.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Resource Utilization Health (Weight: 40 points)
        cursor.execute("SELECT capacity, current_usage FROM resources")
        resources = cursor.fetchall()
        if not resources:
            conn.close()
            return {'score': 85, 'grade': 'A', 'status': 'Optimal', 'breakdown': {}}

        util_scores = []
        for r in resources:
            cap, curr = r['capacity'], r['current_usage']
            pct = (curr / cap) * 100 if cap > 0 else 50
            # Ideal sweet spot: 45% - 80%
            if 45 <= pct <= 80:
                s = 40
            elif 30 <= pct < 45 or 80 < pct <= 88:
                s = 32
            elif 15 <= pct < 30 or 88 < pct <= 95:
                s = 20
            else: # Severe underutilization or overload
                s = 10
            util_scores.append(s)

        util_component = float(np.mean(util_scores))

        # 2. Active Anomalies Penalty (Weight: 25 points, max penalty -25)
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE status = 'Active'")
        active_alerts = cursor.fetchone()[0]
        anomaly_component = max(0.0, 25.0 - (active_alerts * 5.0))

        # 3. Wastage Penalty (Weight: 20 points)
        cursor.execute("SELECT COUNT(*) FROM insights WHERE type IN ('wastage', 'anomaly') AND created_at >= datetime('now', '-24 hours')")
        recent_wastage = cursor.fetchone()[0]
        wastage_component = max(0.0, 20.0 - (recent_wastage * 3.5))

        # 4. Automation Efficacy Bonus (Weight: 15 points)
        cursor.execute("SELECT COUNT(*) FROM automation_actions WHERE timestamp >= datetime('now', '-24 hours')")
        recent_actions = cursor.fetchone()[0]
        automation_component = min(15.0, 8.0 + (recent_actions * 2.0))

        total_score = round(util_component + anomaly_component + wastage_component + automation_component, 1)
        total_score = max(18.0, min(98.5, total_score))

        if total_score >= 90:
            grade = 'A+'
            status_text = 'Peak Operational Efficiency'
            badge_color = 'success'
        elif total_score >= 80:
            grade = 'A'
            status_text = 'High Efficiency'
            badge_color = 'primary'
        elif total_score >= 68:
            grade = 'B'
            status_text = 'Moderate / Minor Waste'
            badge_color = 'info'
        elif total_score >= 50:
            grade = 'C'
            status_text = 'Suboptimal Performance'
            badge_color = 'warning'
        else:
            grade = 'D'
            status_text = 'Critical Inefficiencies Detected'
            badge_color = 'danger'

        conn.close()
        return {
            'score': round(total_score, 0),
            'grade': grade,
            'status': status_text,
            'badge_color': badge_color,
            'breakdown': {
                'utilization_health': round(util_component, 1),
                'anomaly_health': round(anomaly_component, 1),
                'wastage_health': round(wastage_component, 1),
                'automation_bonus': round(automation_component, 1)
            }
        }

    def predict_usage(self, resource_id, horizon_hours=24):
        """
        Statistical time-series forecasting combining historical linear trend
        and diurnal seasonal cycle decomposition.
        Returns predicted hourly values, upper/lower confidence bands.
        """
        readings = self.get_resource_readings(resource_id, limit=168)
        if not readings:
            return {'timestamps': [], 'historical': [], 'predicted': [], 'upper_bound': [], 'lower_bound': []}

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT capacity, unit FROM resources WHERE id = ?", (resource_id,))
        res_info = cursor.fetchone()
        conn.close()
        capacity = res_info['capacity'] if res_info else 1000.0

        # Calculate hour-of-day baselines
        hour_buckets = {h: [] for h in range(24)}
        for r in readings:
            dt = datetime.strptime(r['timestamp'], '%Y-%m-%d %H:%M:%S')
            hour_buckets[dt.hour].append(r['value'])

        hour_means = {h: (float(np.mean(vals)) if vals else 50.0) for h, vals in hour_buckets.items()}
        global_std = float(np.std([r['value'] for r in readings])) if len(readings) > 1 else 5.0

        # Recent trend line (last 48 hours)
        recent_vals = [r['value'] for r in readings[-48:]]
        x = np.arange(len(recent_vals))
        slope, intercept = np.polyfit(x, recent_vals, 1) if len(recent_vals) >= 2 else (0.0, recent_vals[-1])

        last_time = datetime.strptime(readings[-1]['timestamp'], '%Y-%m-%d %H:%M:%S')

        pred_timestamps = []
        pred_values = []
        upper_bounds = []
        lower_bounds = []

        for step in range(1, horizon_hours + 1):
            future_time = last_time + timedelta(hours=step)
            pred_timestamps.append(future_time.strftime('%b %d, %H:00'))

            # Projected seasonal hour component + linear drift
            seasonal_base = hour_means[future_time.hour]
            trend_drift = slope * step * 0.15 # dampened trend drift
            projected = seasonal_base + trend_drift

            # Guard within limits
            projected = max(2.0, min(capacity * 0.96, projected))
            
            ci = 1.96 * global_std * (1.0 + (step * 0.02)) # widening confidence cone
            upper = min(capacity, projected + ci)
            lower = max(0.0, projected - ci)

            pred_values.append(round(float(projected), 1))
            upper_bounds.append(round(float(upper), 1))
            lower_bounds.append(round(float(lower), 1))

        # Recent 24h historical for chart continuity
        recent_hist = readings[-24:]
        hist_timestamps = [datetime.strptime(r['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %H:00') for r in recent_hist]
        hist_values = [round(float(r['value']), 1) for r in recent_hist]

        return {
            'historical_timestamps': hist_timestamps,
            'historical_values': hist_values,
            'future_timestamps': pred_timestamps,
            'predicted_values': pred_values,
            'upper_bound': upper_bounds,
            'lower_bound': lower_bounds,
            'capacity': capacity,
            'unit': res_info['unit'] if res_info else ''
        }

    def analyze_all(self):
        """
        Master intelligence runner:
        1. Checks every resource for statistical anomalies.
        2. Detects wastage patterns.
        3. Generates insights with priority levels.
        4. Triggers alerts where severity is HIGH or CRITICAL.
        5. Generates targeted recommendations.
        6. Updates resource statuses.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, type, capacity, current_usage FROM resources")
        resources = cursor.fetchall()

        new_insights = []
        new_alerts = []
        new_recs = []

        for res in resources:
            r_id, r_name, r_type, cap, curr = res['id'], res['name'], res['type'], res['capacity'], res['current_usage']

            # 1. Statistical anomaly check
            anomaly_res = self.detect_anomaly(r_id, curr)
            if anomaly_res['is_anomaly']:
                dev_sign = "+" if anomaly_res['pct_deviation'] > 0 else ""
                desc = f"{r_name} exhibited an abnormal reading of {curr} ({dev_sign}{anomaly_res['pct_deviation']}% vs normal {anomaly_res['baseline_mean']}). Z-score: {anomaly_res['z_score']}."
                rec_text = f"Audit telemetry load on {r_name} and activate threshold mitigation rule."
                
                # Check if recent insight already exists to avoid redundant flood
                cursor.execute("""
                    SELECT id FROM insights 
                    WHERE resource_id = ? AND description LIKE ? AND created_at >= datetime('now', '-30 minutes')
                """, (r_id, f"%{r_name}%"))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO insights (resource_id, type, severity, description, recommendation)
                        VALUES (?, 'anomaly', ?, ?, ?)
                    """, (r_id, anomaly_res['severity'], desc, rec_text))
                    new_insights.append(desc)

                # Generate alert if HIGH or CRITICAL
                if anomaly_res['severity'] in ['HIGH', 'CRITICAL']:
                    alert_msg = f"{anomaly_res['severity']} Anomaly: {r_name} usage spike ({curr} vs normal {anomaly_res['baseline_mean']})"
                    cursor.execute("""
                        SELECT id FROM alerts 
                        WHERE resource_id = ? AND message = ? AND status = 'Active'
                    """, (r_id, alert_msg))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO alerts (resource_id, severity, message, status)
                            VALUES (?, ?, ?, 'Active')
                        """, (r_id, anomaly_res['severity'], alert_msg))
                        new_alerts.append(alert_msg)

                # Set resource status
                status_to_set = 'Critical' if anomaly_res['severity'] == 'CRITICAL' else 'Warning'
                cursor.execute("UPDATE resources SET status = ? WHERE id = ?", (status_to_set, r_id))
            else:
                # If usage is reasonable, keep Optimal
                if (curr / cap) < 0.85:
                    cursor.execute("UPDATE resources SET status = 'Optimal' WHERE id = ? AND status != 'Inactive'", (r_id,))

            # 2. Wastage check
            wastages = self.detect_wastage(r_id)
            for w in wastages:
                cursor.execute("""
                    SELECT id FROM insights 
                    WHERE resource_id = ? AND description LIKE ? AND created_at >= datetime('now', '-30 minutes')
                """, (r_id, f"%{w['title'][:20]}%"))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO insights (resource_id, type, severity, description, recommendation)
                        VALUES (?, 'wastage', ?, ?, ?)
                    """, (r_id, w['severity'], f"{w['title']}: {w['description']}", w['recommendation']))
                    new_insights.append(w['title'])

                if w['severity'] in ['HIGH', 'CRITICAL']:
                    cursor.execute("""
                        SELECT id FROM alerts WHERE resource_id = ? AND message = ? AND status = 'Active'
                    """, (r_id, w['title']))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO alerts (resource_id, severity, message, status)
                            VALUES (?, ?, ?, 'Active')
                        """, (r_id, w['severity'], f"{w['title']} - Potential Wastage Detected"))
                        new_alerts.append(w['title'])

                # Generate matching recommendation
                rec_title = f"Mitigate {w['title']}"
                cursor.execute("SELECT id FROM recommendations WHERE resource_id = ? AND title = ? AND status = 'Pending'", (r_id, rec_title))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO recommendations (resource_id, title, description, expected_benefit, priority, status)
                        VALUES (?, ?, ?, ?, ?, 'Pending')
                    """, (r_id, rec_title, w['recommendation'], 'Estimated 15-25% reduction in recurring resource wastage', w['severity']))
                    new_recs.append(rec_title)

        conn.commit()
        conn.close()

        return {
            'new_insights_count': len(new_insights),
            'new_alerts_count': len(new_alerts),
            'new_recommendations_count': len(new_recs),
            'insights': new_insights,
            'alerts': new_alerts
        }

ai_engine = AIEngine()
