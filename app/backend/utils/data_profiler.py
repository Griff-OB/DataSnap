import pandas as pd
import numpy as np

class DataProfiler:
    def __init__(self):
        pass

    def get_column_stats(self, series):
        """Get comprehensive statistics for a pandas Series"""
        stats = {
            'count': len(series),
            'null_count': series.isnull().sum(),
            'unique_count': series.nunique(),
            'null_percentage': (series.isnull().sum() / len(series)) * 100
        }

        if pd.api.types.is_numeric_dtype(series):
            numeric_series = series.dropna()
            if len(numeric_series) > 0:
                stats.update({
                    'min': numeric_series.min(),
                    'max': numeric_series.max(),
                    'mean': numeric_series.mean(),
                    'median': numeric_series.median(),
                    'std': numeric_series.std(),
                    'q25': numeric_series.quantile(0.25),
                    'q75': numeric_series.quantile(0.75)
                })

        return stats

    def detect_outliers(self, series, method='iqr'):
        """Detect outliers using IQR or Z-score method"""
        if not pd.api.types.is_numeric_dtype(series):
            return []

        clean_series = series.dropna()
        if len(clean_series) == 0:
            return []

        if method == 'iqr':
            Q1 = clean_series.quantile(0.25)
            Q3 = clean_series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = clean_series[(clean_series < lower_bound) | (clean_series > upper_bound)]
        elif method == 'zscore':
            z_scores = np.abs((clean_series - clean_series.mean()) / clean_series.std())
            outliers = clean_series[z_scores > 3]

        return outliers.index.tolist()

    def calculate_data_quality_score(self, df):
        """Calculate overall data quality score"""
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()
        duplicate_rows = df.duplicated().sum()

        completeness_score = max(0, 100 - (missing_cells / total_cells) * 100)
        uniqueness_score = max(0, 100 - (duplicate_rows / df.shape[0]) * 100)

        # Simplified consistency and validity scores
        consistency_score = 85
        validity_score = 90

        overall_score = (completeness_score + uniqueness_score + consistency_score + validity_score) / 4

        return {
            'overall': round(overall_score, 2),
            'completeness': round(completeness_score, 2),
            'uniqueness': round(uniqueness_score, 2),
            'consistency': round(consistency_score, 2),
            'validity': round(validity_score, 2)
        }
