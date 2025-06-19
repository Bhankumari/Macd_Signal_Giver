#!/usr/bin/env python3
"""
Corrected RSI Calculation using Wilder's Smoothing Method
This matches the standard RSI calculation used by most trading platforms
"""

import pandas as pd
import numpy as np
import os

def calculate_rsi_wilder(data, period=14):
    """
    Calculate RSI using Wilder's smoothing method (the correct/standard way)
    This matches what you see on TradingView, Yahoo Finance, etc.
    """
    close_prices = data['close'].copy()
    
    # Calculate price changes
    delta = close_prices.diff()
    
    # Separate gains and losses
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    
    # Calculate the first averages using simple moving average
    avg_gain = gains.rolling(window=period).mean()
    avg_loss = losses.rolling(window=period).mean()
    
    # Apply Wilder's smoothing for subsequent values
    for i in range(period, len(gains)):
        avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period - 1) + gains.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period - 1) + losses.iloc[i]) / period
    
    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_rsi_pandas_ewm(data, period=14):
    """
    Alternative RSI calculation using pandas EWM (Exponential Weighted Moving Average)
    This is closer to the standard but uses different alpha calculation
    """
    close_prices = data['close'].copy()
    delta = close_prices.diff()
    
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    
    # Use exponential weighted moving average with alpha = 1/period
    alpha = 1.0 / period
    avg_gain = gains.ewm(alpha=alpha, adjust=False).mean()
    avg_loss = losses.ewm(alpha=alpha, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_rsi_simple_ma(data, period=14):
    """
    The incorrect RSI calculation (what we were using before)
    Uses simple moving average instead of Wilder's smoothing
    """
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compare_rsi_methods(stock_symbol):
    """Compare different RSI calculation methods for a stock"""
    
    file_path = f"data/{stock_symbol}.csv"
    
    if not os.path.exists(file_path):
        print(f"❌ No data file found for {stock_symbol}")
        return
    
    # Load data
    data = pd.read_csv(file_path)
    data.columns = [col.lower() for col in data.columns]
    data = data[['published_date', 'close']]
    data['published_date'] = pd.to_datetime(data['published_date'])
    data['close'] = pd.to_numeric(data['close'], errors='coerce')
    data = data.dropna(subset=['close'])
    data = data.sort_values(by='published_date')
    
    if len(data) < 20:
        print(f"❌ Insufficient data for {stock_symbol}")
        return
    
    # Calculate RSI using different methods
    rsi_wilder = calculate_rsi_wilder(data)
    rsi_ewm = calculate_rsi_pandas_ewm(data)
    rsi_simple = calculate_rsi_simple_ma(data)
    
    # Get the latest values
    latest_wilder = rsi_wilder.iloc[-1]
    latest_ewm = rsi_ewm.iloc[-1]
    latest_simple = rsi_simple.iloc[-1]
    latest_price = data['close'].iloc[-1]
    latest_date = data['published_date'].iloc[-1].strftime('%Y-%m-%d')
    
    print(f"\n📊 RSI COMPARISON FOR {stock_symbol}")
    print("=" * 50)
    print(f"📅 Date: {latest_date}")
    print(f"💰 Price: {latest_price:.2f}")
    print("-" * 50)
    print(f"🎯 Wilder's RSI (CORRECT):  {latest_wilder:.1f}")
    print(f"📈 EWM RSI (Alternative):   {latest_ewm:.1f}")
    print(f"❌ Simple MA RSI (Wrong):   {latest_simple:.1f}")
    print("-" * 50)
    
    # Determine status using correct Wilder's RSI
    if latest_wilder < 30:
        status = "🟢 OVERSOLD - Potential BUY"
    elif latest_wilder > 70:
        status = "🔴 OVERBOUGHT - Consider SELL"
    else:
        status = "⚪ NEUTRAL - Normal range"
    
    print(f"📊 Status: {status}")
    
    return {
        'stock': stock_symbol,
        'wilder_rsi': latest_wilder,
        'ewm_rsi': latest_ewm,
        'simple_rsi': latest_simple,
        'price': latest_price,
        'date': latest_date
    }

def test_all_personal_stocks():
    """Test RSI calculation for all personal stocks"""
    personal_stocks = ['GBIME', 'RURU', 'HBL', 'ICFC', 'JBLB', 'JFL', 'UPPER']
    
    print("🔍 RSI CALCULATION COMPARISON")
    print("=" * 60)
    print("Comparing different RSI calculation methods:")
    print("• Wilder's RSI = Standard/Correct method")
    print("• EWM RSI = Alternative exponential method")
    print("• Simple MA RSI = Incorrect method (what we used before)")
    print("=" * 60)
    
    results = []
    
    for stock in personal_stocks:
        try:
            result = compare_rsi_methods(stock)
            if result:
                results.append(result)
        except Exception as e:
            print(f"❌ Error processing {stock}: {e}")
    
    # Summary
    print(f"\n📋 SUMMARY - CORRECTED RSI VALUES")
    print("=" * 60)
    
    oversold = []
    overbought = []
    neutral = []
    
    for result in results:
        stock = result['stock']
        rsi = result['wilder_rsi']
        price = result['price']
        
        if rsi < 30:
            oversold.append(f"{stock}: {rsi:.1f}")
            print(f"🟢 {stock}: RSI {rsi:.1f} - OVERSOLD (Price: {price:.2f})")
        elif rsi > 70:
            overbought.append(f"{stock}: {rsi:.1f}")
            print(f"🔴 {stock}: RSI {rsi:.1f} - OVERBOUGHT (Price: {price:.2f})")
        else:
            neutral.append(f"{stock}: {rsi:.1f}")
            print(f"⚪ {stock}: RSI {rsi:.1f} - NEUTRAL (Price: {price:.2f})")
    
    print(f"\n📊 TOTALS:")
    print(f"🟢 Oversold: {len(oversold)}")
    print(f"🔴 Overbought: {len(overbought)}")
    print(f"⚪ Neutral: {len(neutral)}")

if __name__ == "__main__":
    test_all_personal_stocks() 