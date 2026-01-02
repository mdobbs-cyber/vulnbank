import os
import json
import csv
import datetime
import pandas as pd
import splunklib.client as client
import splunklib.results as results

class IOCManager:
    def __init__(self, filepath="iocs.csv"):
        self.filepath = filepath
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Type", "Value", "Description", "Timestamp"])

    def save_ioc(self, ioc_type: str, value: str, description: str) -> str:
        """
        Saves an Indicator of Compromise (IOC) to the tracking database.

        Args:
            ioc_type: The type of IOC (e.g., 'IP', 'Hash', 'Domain', 'URL').
            value: The actual value of the IOC (e.g., '192.168.1.5').
            description: A brief reason why this is an IOC.

        Returns:
            A confirmation message.
        """
        timestamp = datetime.datetime.now().isoformat()
        try:
            with open(self.filepath, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([ioc_type, value, description, timestamp])
            return f"Successfully saved IOC: {value} ({ioc_type})"
        except Exception as e:
            return f"Error saving IOC: {e}"

    def get_iocs(self):
        if os.path.exists(self.filepath):
            return pd.read_csv(self.filepath)
        return pd.DataFrame(columns=["Type", "Value", "Description", "Timestamp"])

class SplunkConnector:
    def __init__(self):
        self.host = os.environ.get("SPLUNK_HOST", "splunk")
        self.port = int(os.environ.get("SPLUNK_PORT", 8089))
        self.username = os.environ.get("SPLUNK_USERNAME", "admin")
        self.password = os.environ.get("SPLUNK_PASSWORD", "password123")
        self.service = None

    def connect(self):
        if not self.service:
            try:
                self.service = client.connect(
                    host=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    verify=False # Splunk uses self-signed certs by default
                )
            except Exception as e:
                return f"Error connecting to Splunk: {e}"
        return None

    def search(self, query: str) -> str:
        """
        Executes a search query against the Splunk instance.
        
        Args:
            query: The Splunk Search Processing Language (SPL) query string.
        
        Returns:
            A JSON string containing the search results (limited to top 20).
        """
        conn_err = self.connect()
        if conn_err:
            return json.dumps({"error": conn_err})

        if not query.strip().startswith("search") and not query.strip().startswith("|"):
            query = "search " + query

        try:
            kwargs_oneshot = {
                "earliest_time": "-24h",
                "latest_time": "now",
                "output_mode": "json",
                "count": 20
            }
            
            # Oneshot search
            search_job = self.service.jobs.oneshot(query, **kwargs_oneshot)
            
            reader = results.JSONResultsReader(search_job)
            data = []
            for item in reader:
                if isinstance(item, dict):
                    data.append(item)
                elif isinstance(item, results.Message):
                    data.append({"message": str(item)})
            
            return json.dumps(data, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Search failed: {str(e)}"})
