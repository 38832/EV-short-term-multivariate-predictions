# EV Short-Term Multivariate Prediction

This project implements advanced neural network architectures for predicting electric vehicle charging demand using multivariate time series data from the ACN (Adaptive Charging Network).

## Overview

The implementation includes:
- **Novel Architectures**: Graph-Informer with Exogenous Attention, Multi-Resolution TCN-Transformer, and Residual Boosted Probabilistic Transformer
- **Baseline Models**: ARIMAX, XGBoost, CatBoost, CNN-LSTM-AM, and Informer
- **Multivariate Features**: Weather (NOAA), Solar irradiance (NSRDB), Electricity pricing (SCE TOU), and CAISO renewables/carbon data
- **Multi-site Analysis**: Caltech and JPL charging station data with cross-site validation

## Quick Start (Google Colab)

1. Open [Google Colab](https://colab.research.google.com/)
2. Upload `ev_shortterm_multivariate_prediction.py`
3. Copy and paste sections sequentially into Colab cells
4. Follow the Markdown comments to understand each section

## File Structure

- `ev_shortterm_multivariate_prediction.py` - Main notebook-style script with all implementations

## Key Features

### Data Sources
- **EV Data**: ACN API (Caltech, JPL sites)
- **Weather**: NOAA Climate Data API
- **Solar**: NREL NSRDB API  
- **Pricing**: SCE Time-of-Use tariffs + CAISO market data
- **Grid**: CAISO renewables percentage and carbon intensity

### Models Implemented
- **Graph-Informer**: Novel graph attention + transformer with exogenous attention
- **Multi-Resolution TCN-Transformer**: Multi-scale temporal convolutions + transformers
- **Residual Boosted Transformer**: Deep residual networks + CatBoost integration
- **Baselines**: ARIMAX, XGBoost, CatBoost, CNN-LSTM-AM, Informer

### Evaluation
- **Metrics**: MAE, RMSE, probabilistic metrics (pinball loss, coverage, interval width)
- **Cross-site validation**: Train on one site, test on another
- **Per-site analysis**: Individual site performance evaluation
- **Feature importance**: XGBoost and CatBoost feature ranking

## Results Summary

Based on test runs, neural models significantly outperform traditional baselines:
- Best neural model MAE: ~0.75-0.79 kWh
- Traditional models MAE: 4.5-5.9 kWh
- Cross-site generalization challenging but implementable

## Requirements

```bash
pip install requests pandas numpy scikit-learn torch statsmodels catboost xgboost matplotlib
pip install torch_geometric
pip install pytorch_lightning
```

## Usage Notes

- The script is designed for sequential execution in Colab
- API keys for NOAA and NREL are included (replace with your own for production)
- Fallback data generation ensures the pipeline works even if APIs fail
- All visualizations save automatically as PNG files

## Academic Citation

If using this work for research, please cite appropriately and acknowledge the ACN data source.
