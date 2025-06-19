#!/usr/bin/env python3
"""
Test script for RSI monitoring of personal stocks
This demonstrates the new RSI oversold/overbought detection feature
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

def calculate_rsi(data, period=14):
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

def check_personal_stocks_rsi_demo():
    """Demo RSI checking for personal stocks"""
    personal_stocks = ['GBIME', 'RURU', 'HBL', 'ICFC', 'JBLB', 'JFL', 'UPPER']
    
    print("📊 RSI MONITORING DEMO FOR PERSONAL STOCKS")
    print("=" * 50)
    print(f"🎯 Monitoring: {', '.join(personal_stocks)}")
    print(f"📏 RSI Thresholds: Oversold < 30, Overbought > 70")
    print("=" * 50)
    
    rsi_results = []
    
    for stock_symbol in personal_stocks:
        try:
            file_path = f"data/{stock_symbol}.csv"
            
            if not os.path.exists(file_path):
                print(f"⚠️  {stock_symbol}: No data file found")
                continue
            
            # Load and process data
            data = pd.read_csv(file_path)
            data.columns = [col.lower() for col in data.columns]
            
            if 'close' not in data.columns:
                print(f"⚠️  {stock_symbol}: No 'close' price column found")  
                continue
                
            data = data[['published_date', 'close']]
            data['published_date'] = pd.to_datetime(data['published_date'])
            data['close'] = pd.to_numeric(data['close'], errors='coerce')
            data = data.dropna(subset=['close'])
            data = data.sort_values(by='published_date')
            
            if len(data) < 14:
                print(f"⚠️  {stock_symbol}: Insufficient data for RSI (need 14+ points, have {len(data)})")
                continue
            
            # Calculate RSI
            rsi = calculate_rsi(data)
            current_rsi = rsi.iloc[-1]
            current_price = data['close'].iloc[-1]
            last_date = data['published_date'].iloc[-1].strftime('%Y-%m-%d')
            
            # Determine RSI status
            if current_rsi < 30:
                status = "OVERSOLD"
                emoji = "🟢"  # Green for potential buy
                alert = "💡 Potential BUY opportunity!"
            elif current_rsi > 70:
                status = "OVERBOUGHT"  
                emoji = "🔴"  # Red for potential sell
                alert = "💡 Consider taking profits!"
            else:
                status = "NEUTRAL"
                emoji = "⚪"
                alert = "📊 Normal trading range"
            
            print(f"{emoji} {stock_symbol}")
            print(f"   RSI: {current_rsi:.1f} - {status}")
            print(f"   Price: {current_price:.2f} (as of {last_date})")
            print(f"   {alert}")
            print()
            
            rsi_results.append({
                'stock': stock_symbol,
                'rsi': current_rsi,
                'price': current_price,
                'status': status,
                'date': last_date
            })
            
        except Exception as e:
            print(f"❌ {stock_symbol}: Error - {str(e)}")
            print()
    
    # Summary
    print("=" * 50)
    print("📋 RSI SUMMARY")
    print("=" * 50)
    
    if not rsi_results:
        print("❌ No RSI data available for any stocks")
        return
    
    oversold = [r for r in rsi_results if r['rsi'] < 30]
    overbought = [r for r in rsi_results if r['rsi'] > 70]
    neutral = [r for r in rsi_results if 30 <= r['rsi'] <= 70]
    
    print(f"📊 Total stocks analyzed: {len(rsi_results)}")
    print(f"🟢 Oversold stocks (RSI < 30): {len(oversold)}")
    if oversold:
        for stock in oversold:
            print(f"   • {stock['stock']}: RSI {stock['rsi']:.1f}")
    
    print(f"🔴 Overbought stocks (RSI > 70): {len(overbought)}")
    if overbought:
        for stock in overbought:
            print(f"   • {stock['stock']}: RSI {stock['rsi']:.1f}")
    
    print(f"⚪ Neutral stocks (30-70): {len(neutral)}")
    
    # Generate Telegram-style alert message
    if oversold or overbought:
        print("\n📱 TELEGRAM ALERT MESSAGE:")
        print("-" * 30)
        print("📊 YOUR PORTFOLIO RSI STATUS")
        print("=" * 25)
        
        for stock in oversold:
            print(f"🟢 {stock['stock']}: RSI {stock['rsi']:.1f} - OVERSOLD")
            print(f"   Price: {stock['price']:.2f}")
            print("   💡 Potential BUY opportunity")
            print()
        
        for stock in overbought:
            print(f"🔴 {stock['stock']}: RSI {stock['rsi']:.1f} - OVERBOUGHT")
            print(f"   Price: {stock['price']:.2f}")
            print("   💡 Consider taking profits")
            print()
        
        print("⚠️ Always do your own research before trading!")

if __name__ == "__main__":
    check_personal_stocks_rsi_demo() 