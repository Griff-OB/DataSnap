import re
import pandas as pd

class PIIScanner:
    def __init__(self):
        # Compile regex patterns for PII detection
        self.patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            'credit_card': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            'url': re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'),
            'ip_address': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
            'date': re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{1,2}-\d{1,2}\b'),
            'name': re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b') # Simple name pattern
        }

    def scan_column(self, series, column_name):
        """Scan a pandas Series for PII data"""
        if not pd.api.types.is_string_dtype(series):
            return {'detected': False, 'types': [], 'confidence': 0}

        detected_types = []
        total_samples = 0
        matches = {pii_type: 0 for pii_type in self.patterns}

        for value in series.dropna().astype(str):
            total_samples += 1
            for pii_type, pattern in self.patterns.items():
                if pattern.search(value):
                    matches[pii_type] += 1

        # Calculate confidence scores
        results = {'detected': False, 'types': [], 'confidence': 0}

        for pii_type, count in matches.items():
            if count > 0:
                confidence = (count / total_samples) * 100
                if confidence > 5: # 5% threshold
                    detected_types.append({
                        'type': pii_type,
                        'count': count,
                        'confidence': round(confidence, 2)
                    })

        if detected_types:
            results['detected'] = True
            results['types'] = detected_types
            results['confidence'] = round(sum(t['confidence'] for t in detected_types) / len(detected_types), 2)

        return results

    def get_pii_summary(self, df):
        """Get PII summary for entire DataFrame"""
        pii_summary = {}
        total_pii_columns = 0

        for col in df.columns:
            if pd.api.types.is_string_dtype(df[col]):
                result = self.scan_column(df[col], col)
                if result['detected']:
                    pii_summary[col] = result
                    total_pii_columns += 1

        return {
            'pii_detected': total_pii_columns > 0,
            'pii_columns': pii_summary,
            'total_pii_columns': total_pii_columns,
            'recommendations': self._generate_recommendations(pii_summary)
        }

    def _generate_recommendations(self, pii_summary):
        """Generate recommendations based on PII detection"""
        recommendations = []

        if pii_summary:
            recommendations.append("PII data detected in your dataset")

        high_risk_columns = []
        for col, data in pii_summary.items():
            if any(pii['type'] in ['ssn', 'credit_card'] for pii in data['types']):
                high_risk_columns.append(col)

        if high_risk_columns:
            recommendations.append(f"High-risk PII detected in columns: {', '.join(high_risk_columns)}")
            recommendations.append("Consider anonymizing or removing these columns")
        
        recommendations.append("Review data privacy compliance requirements")

        return recommendations
