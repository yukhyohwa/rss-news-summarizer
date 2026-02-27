
import os
import datetime
from app.core.arb_reporter import fetch_daily_data, format_liq, format_table
from app.core.processor import truncate_summary
from config.settings import STRATEGY_CONFIG

def generate_unified_report(categorized_news=None, include_arb=True):
    """
    Combines News Summary and Market Arbitrage into a single report.
    """
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    filename = os.path.join(output_dir, f"Global_Digest_{today}.md")
    
    report_content = f"# Global News & Market Digest Report ({today})\n\n"
    
    # 1. News Section
    if categorized_news:
        report_content += "## 🌏 Global News Summary\n\n"
        all_categories = list(categorized_news.keys())
        categories_order = [c for c in all_categories if c != "Others"]
        if "Others" in all_categories:
            categories_order.append("Others")
        
        for category in categories_order:
            articles = categorized_news.get(category, [])
            if not articles:
                continue
            
            report_content += f"### 📰 {category} ({len(articles)} items)\n\n"
            for article in articles:
                source_line = ", ".join([f"[{s['name']}]({s['link']})" for s in article['sources']])
                report_content += f"#### {article['translated_title']} (Source: {source_line})\n\n"
                if article['translated_summary']:
                    truncated_summary = truncate_summary(article['translated_summary'], word_limit=100)
                    report_content += f"{truncated_summary}\n\n"
                report_content += "---\n\n"
    
    # 2. Arbitrage Section (from DB)
    if include_arb:
        report_content += "## 💰 Market Arbitrage & Opportunities\n\n"
        
        # We can reuse the logic from arb_reporter.py but append to our report_content
        # Let's extract the core sections from arb_reporter logic
        
        # 1. Market Indices (Global)
        rows, cols = fetch_daily_data('market_indices', today)
        if rows:
            display_rows = [[r[2], f"{r[3]:.2f}", f"{r[5]:.2f}%"] for r in rows]
            report_content += "### 1. Market Indices (Global)\n"
            report_content += format_table(display_rows, ['Index', 'Price', 'Change %'], ['left', 'right', 'right']) + "\n\n"

        # 2. Forex Rates
        rows, cols = fetch_daily_data('forex_rates', today)
        if rows:
            forex_data = {r[1]: {'buy': f"{r[4]:.4f}", 'sell': f"{r[5]:.4f}"} for r in rows}
            available_currencies = [r[1] for r in rows]
            priority = ['美元', '欧元', '日元', '英镑']
            sorted_currencies = [p for p in priority if p in available_currencies] + [c for c in available_currencies if c not in priority]
            header = ['Rate'] + sorted_currencies
            row_buy = ['Buy'] + [forex_data[c]['buy'] for c in sorted_currencies]
            row_sell = ['Sell'] + [forex_data[c]['sell'] for c in sorted_currencies]
            report_content += "### 2. Forex Rates (BOC)\n"
            report_content += format_table([row_sell, row_buy], header, ['left'] + ['right'] * len(sorted_currencies)) + "\n\n"

        # 3. Commodities
        rows, cols = fetch_daily_data('commodities', today)
        if rows:
            display_rows = [[r[2], f"{r[3]:.2f}", f"{r[5]:.2f}%"] for r in rows]
            report_content += "### 3. Commodities\n"
            report_content += format_table(display_rows, ['Name', 'Price', 'Change %'], ['left', 'right', 'right']) + "\n\n"

        # 4. LOF/IOF
        rows, cols = fetch_daily_data('lof_funds', today, "fund_id, fund_name, price, premium_rate, amount, volume, apply_status")
        if rows:
            display_rows = []
            for r in rows:
                details = []
                if r[4] > 0: details.append(f"Amt:{format_liq(r[4])}")
                if r[5] > 0: details.append(f"Vol:{format_liq(r[5])}")
                display_rows.append([r[0], r[1], f"{r[2]:.3f}", f"{r[3]:.2f}%", r[6] or "-", ", ".join(details)])
            report_content += f"### 4. LOF/IOF Funds (Premium > {STRATEGY_CONFIG['lof']['min_premium_rate']}%)\n"
            report_content += format_table(display_rows, ['Code', 'Name', 'Price', 'Premium', 'Status', 'Liquidity'], ['left', 'left', 'right', 'right', 'left', 'left']) + "\n\n"

        # 5. QDII
        rows, cols = fetch_daily_data('qdii_arbitrage', today)
        if rows:
            display_rows = []
            for r in rows:
                fund_name = r[2]
                # Double filter to ensure no ETF/EOF in report
                if 'ETF' in fund_name.upper() or 'EOF' in fund_name.upper():
                    continue
                
                details = []
                if r[9] > 0: details.append(f"Amt:{format_liq(r[9])}")
                if r[8] > 0: details.append(f"Vol:{format_liq(r[8])}")
                
                # Show market as APAC if Asia
                market = "APAC" if r[12] == "Asia" else r[12]
                
                display_rows.append([r[1], fund_name, market, f"{r[4]:.2f}%", f"{r[6]:.2f}%" if r[6] is not None else "-", r[11] or "-", ", ".join(details)])
            
            if display_rows:
                report_content += f"### 5. QDII Arbitrage (Premium > {STRATEGY_CONFIG['qdii']['min_premium_rate']}%)\n"
                report_content += format_table(display_rows, ['Code', 'Name', 'Market', 'T-1 Prem', 'Realtime', 'Status', 'Liquidity'], ['left', 'left', 'left', 'right', 'right', 'left', 'left']) + "\n\n"

        # 6. A-share
        rows, cols = fetch_daily_data('stock_arbitrage', today)
        if rows:
            display_rows = [[r[1], r[2], f"{r[3]:.2f}", f"{r[4]:.2f}", r[5], r[6]] for r in rows]
            report_content += "### 6. A-share Arbitrage\n"
            report_content += format_table(display_rows, ['Code', 'Name', 'Price', 'Cash Price', 'Type', 'Description'], ['left', 'left', 'right', 'right', 'left', 'left']) + "\n\n"

        # 7. Bond Issuance
        rows, cols = fetch_daily_data('bond_issuance', today)
        if rows:
            display_rows = [[r[1], r[2], r[3], r[4], r[5]] for r in rows]
            report_content += "### 7. Bond Issuance & Listing\n"
            report_content += format_table(display_rows, ['Code', 'Name', 'Sub Date', 'List Date', 'Details'], ['left', 'left', 'left', 'left', 'left']) + "\n\n"

        # 8/9. Cbond
        rows, cols = fetch_daily_data('cbond_double_low', today)
        if rows:
            display_rows = [[r[1], r[2], f"{r[3]:.2f}", f"{r[4]:.2f}%", f"{r[5]:.2f}", f"{r[6]:.2f}y"] for r in rows]
            report_content += f"### 8. Cbond Double Low (< {STRATEGY_CONFIG['cbond']['max_dblow']})\n"
            report_content += format_table(display_rows, ['Code', 'Name', 'Price', 'Premium', 'LowIndex', 'Rem.Y'], ['left', 'left', 'right', 'right', 'right', 'right']) + "\n\n"

        rows, cols = fetch_daily_data('cbond_putback', today)
        if rows:
            display_rows = [[r[1], r[2], f"{r[3]:.2f}", f"{r[4]:.2f}%", r[6] or "-", f"{r[7]:.2f}y"] for r in rows]
            report_content += f"### 9. Cbond Put-back Opportunity (< {STRATEGY_CONFIG['cbond']['max_putback_price']})\n"
            report_content += format_table(display_rows, ['Code', 'Name', 'Price', 'Premium', 'Put Date', 'Rem.Y'], ['left', 'left', 'right', 'right', 'left', 'right']) + "\n\n"

        # 10. SPAC
        rows, cols = fetch_daily_data('spac_arbitrage', today)
        if rows:
            display_rows = [[r[1], r[2], r[3], f"{r[4]:.2f}", f"{r[5]:.2f}", f"{r[6]:.2f}%", str(r[7])] for r in rows]
            report_content += "### 10. SPAC Arbitrage\n"
            report_content += format_table(display_rows, ['Symbol', 'Name', 'IPO Date', 'Price', 'NAV', 'Yield', 'Days'], ['left', 'left', 'left', 'right', 'right', 'right', 'right']) + "\n\n"

        # 11. CEF
        rows, cols = fetch_daily_data('cef_arbitrage', today)
        if rows:
            display_rows = []
            for r in rows:
                ticker = r[1]
                price = r[5]
                discount = r[7]
                avg_disc = r[8]
                diff = discount - avg_disc
                zscore = r[9]
                vol_usd = (r[10] or 0) * price
                dist_status = r[11] if len(r) > 11 else ""
                
                display_rows.append([ticker, r[2], f"{discount:.2f}%", f"{diff:.2f}%", f"{zscore:.2f}", f"${vol_usd/1000:.0f}K", dist_status])
            
            report_content += f"### 11. CEF Arbitrage (Disc < {STRATEGY_CONFIG['cef']['min_discount']}%)\n"
            report_content += format_table(display_rows, ['Ticker', 'Name', 'Discount', 'Diff', 'Z-Score', 'Vol USD', 'Div Qual'], ['left', 'left', 'right', 'right', 'right', 'right', 'left']) + "\n\n"

    # Sources
    report_content += "## 📚 Sources\n"
    report_content += "- **News**: TechCrunch, NY Times, BBC, Le Figaro\n"
    report_content += "- **Market Data**: Yahoo Finance, Bank of China, Jisilu, Eastmoney, StockAnalysis, CEFConnect\n"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    return filename
