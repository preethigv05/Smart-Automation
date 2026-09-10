from datetime import datetime
import sqlite3
from database import get_db_connection
from ai_engine import ai_engine

class AutomationEngine:
    """
    Smart Automation Engine.
    Evaluates conditional rules against real-time and simulated resource states.
    Executes automated load-shedding, leak isolation, QoS throttling, and sleep mode activations.
    Maintains an audit trail in the automation_actions database.
    """

    def __init__(self):
        pass

    def get_rules(self):
        """Retrieve all automation rules."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM automation_rules ORDER BY id ASC")
        rules = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rules]

    def toggle_rule(self, rule_id, is_enabled):
        """Enable or disable a specific automation rule."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE automation_rules SET is_enabled = ? WHERE id = ?", (1 if is_enabled else 0, rule_id))
        conn.commit()
        conn.close()
        return True

    def get_recent_actions(self, limit=25):
        """Retrieve recent automation execution audit logs."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, r.name as resource_name, r.unit 
            FROM automation_actions a
            LEFT JOIN resources r ON a.resource_id = r.id
            ORDER BY a.timestamp DESC 
            LIMIT ?
        """, (limit,))
        actions = cursor.fetchall()
        conn.close()
        return [dict(a) for a in actions]

    def evaluate_and_execute(self, force_simulation=False):
        """
        Evaluates active rules against current resource metrics.
        If triggers are met and auto-execution is enabled (or force_simulation is True),
        executes suitable mitigation, optimizes resource state, and logs the action.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # Load system settings
        cursor.execute("SELECT key, value FROM system_settings")
        settings = {row['key']: row['value'] for row in cursor.fetchall()}
        elec_thresh = float(settings.get('electricity_threshold', 85))
        water_thresh = float(settings.get('water_threshold', 75))
        net_thresh = float(settings.get('network_threshold', 90))
        auto_exec_master = settings.get('auto_execute_mode', 'true').lower() == 'true'

        cursor.execute("SELECT * FROM resources")
        resources = cursor.fetchall()

        cursor.execute("SELECT * FROM automation_rules WHERE is_enabled = 1")
        rules = cursor.fetchall()

        executed_actions = []

        for r in resources:
            r_id = r['id']
            r_name = r['name']
            r_type = r['type']
            cap = r['capacity']
            curr = r['current_usage']
            pct = (curr / cap) * 100 if cap > 0 else 0

            # Latest occupancy
            cursor.execute("SELECT occupancy FROM readings WHERE resource_id = ? ORDER BY timestamp DESC LIMIT 1", (r_id,))
            latest_occ_row = cursor.fetchone()
            occ = latest_occ_row['occupancy'] if latest_occ_row and latest_occ_row['occupancy'] is not None else 0

            for rule in rules:
                rule_name = rule['rule_name']
                res_type_target = rule['resource_type']

                if res_type_target != r_type:
                    continue

                triggered = False
                trigger_desc = ""
                action_text = ""
                new_usage = curr

                # 1. Peak Demand Electricity Rule
                if r_type == 'electricity' and "Peak" in rule_name:
                    if pct >= elec_thresh or force_simulation:
                        triggered = True
                        trigger_desc = f"Power draw reached {curr} kWh ({round(pct, 1)}% of {cap} kWh capacity, exceeding {elec_thresh}% threshold)"
                        action_text = f"Automated Load-Shedding: Dimmed non-critical campus lighting by 30% and modulated chiller plant #2 (saved ~{round(curr * 0.16, 1)} kWh)"
                        new_usage = round(curr * 0.84, 1)

                # 2. Zero-Occupancy Ghost Power Cutoff
                elif r_type in ['computing', 'room'] and "Zero-Occupancy" in rule_name:
                    if (occ == 0 and pct > 25) or (force_simulation and "Lab" in r_name):
                        triggered = True
                        trigger_desc = f"Room occupancy = 0 with {curr} active {r['unit']} ({round(pct, 1)}% capacity drawing power)"
                        action_text = f"Smart Eco-Clamp: Dispatched Wake-on-LAN standby signal, putting 35 idle workstations into Deep Sleep (0.8W standby)"
                        new_usage = round(curr * 0.35, 1)

                # 3. Surge Water Leakage Emergency Cutoff
                elif r_type == 'water' and "Water Leakage" in rule_name:
                    anomaly_check = ai_engine.detect_anomaly(r_id, curr)
                    if curr >= water_thresh or anomaly_check['is_anomaly'] or force_simulation:
                        triggered = True
                        trigger_desc = f"Excessive flow rate of {curr} L/min detected (Statistical Z-score: {anomaly_check.get('z_score', 3.2)})"
                        action_text = f"Emergency Solenoid Isolation: Triggered virtual shut-off valve on Sub-manifold B and notified plumbing staff"
                        new_usage = round(min(15.0, curr * 0.2), 1)

                # 4. Dynamic Network QoS Bandwidth Throttling
                elif r_type == 'network' and "QoS" in rule_name:
                    if pct >= net_thresh or force_simulation:
                        triggered = True
                        trigger_desc = f"Core bandwidth reached {curr} Mbps ({round(pct, 1)}% of 1000 Mbps pipeline)"
                        action_text = f"Dynamic Traffic Shaper: Enforced QoS priority for instructional videoconferencing & throttled recreational P2P streams"
                        new_usage = round(curr * 0.72, 1)

                # 5. Consolidation of Underutilized Lab Nodes
                elif r_type == 'computing' and "Consolidation" in rule_name:
                    if pct < 20.0 or force_simulation:
                        triggered = True
                        trigger_desc = f"Low continuous utilization of {round(pct, 1)}% observed in {r_name}"
                        action_text = f"Workload Node Consolidation: Migrated 3 active jobs to Primary Cluster and powered down 12 redundant nodes"
                        new_usage = round(curr * 0.6, 1)

                if triggered:
                    # Check recent action log to prevent repetitive identical executions in short time
                    cursor.execute("""
                        SELECT id FROM automation_actions 
                        WHERE rule_name = ? AND resource_id = ? AND timestamp >= datetime('now', '-10 minutes')
                    """, (rule_name, r_id))
                    existing = cursor.fetchone()

                    if not existing or force_simulation:
                        status_label = 'Executed' if (auto_exec_master and rule['auto_execute']) else 'Simulated'
                        
                        cursor.execute("""
                            INSERT INTO automation_actions (rule_name, resource_id, trigger, action, status, timestamp)
                            VALUES (?, ?, ?, ?, ?, datetime('now'))
                        """, (rule_name, r_id, trigger_desc, action_text, status_label))

                        # Apply simulated reduction to show tangible outcome in the prototype!
                        if status_label == 'Executed':
                            cursor.execute("UPDATE resources SET current_usage = ?, status = 'Optimal' WHERE id = ?", (new_usage, r_id))
                            cursor.execute("""
                                INSERT INTO readings (resource_id, value, occupancy, timestamp)
                                VALUES (?, ?, ?, datetime('now'))
                            """, (r_id, new_usage, occ))

                        executed_actions.append({
                            'rule_name': rule_name,
                            'resource_name': r_name,
                            'trigger': trigger_desc,
                            'action': action_text,
                            'status': status_label,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'savings_impact': f"Usage optimized from {curr} {r['unit']} to {new_usage} {r['unit']}"
                        })

        conn.commit()
        conn.close()

        return executed_actions

automation_engine = AutomationEngine()
