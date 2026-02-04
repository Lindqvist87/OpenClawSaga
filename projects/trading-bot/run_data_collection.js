const https = require('https');
const fs = require('fs');
const sqlite3 = require('better-sqlite3');

const now = new Date().toISOString();
console.log('📊 Trading Bot Data Collection -', now);
console.log('='.repeat(60));

// Symbols to track
const symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'];
const prices = {};

// Helper function for HTTPS requests
function fetchJson(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch (e) { reject(e); }
      });
    }).on('error', reject);
  });
}

async function fetchPrices() {
  console.log('\n1️⃣ Fetching prices from Binance...');
  for (const symbol of symbols) {
    try {
      const [priceData, statsData] = await Promise.all([
        fetchJson(`https://api.binance.com/api/v3/ticker/price?symbol=${symbol}`),
        fetchJson(`https://api.binance.com/api/v3/ticker/24hr?symbol=${symbol}`)
      ]);
      
      prices[symbol] = {
        price: parseFloat(priceData.price),
        change_24h: parseFloat(statsData.priceChangePercent),
        high_24h: parseFloat(statsData.highPrice),
        low_24h: parseFloat(statsData.lowPrice),
        volume: parseFloat(statsData.volume)
      };
      console.log(`  ${symbol}: $${prices[symbol].price.toLocaleString()} (${prices[symbol].change_24h >= 0 ? '+' : ''}${prices[symbol].change_24h.toFixed(2)}%)`);
    } catch (e) {
      console.log(`  Error fetching ${symbol}: ${e.message}`);
    }
  }
}

function updateDatabase() {
  console.log('\n2️⃣ Updating paper_trades.db...');
  const db = new sqlite3('projects/trading-bot/paper_trades.db');
  
  // Insert price data
  const insertPrice = db.prepare(`
    INSERT INTO price_data (symbol, price, change_24h, high_24h, low_24h, volume, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `);
  
  let inserted = 0;
  for (const [symbol, data] of Object.entries(prices)) {
    insertPrice.run(symbol, data.price, data.change_24h, data.high_24h, data.low_24h, data.volume, now);
    inserted++;
  }
  console.log(`  Inserted ${inserted} price records`);
  
  // Check and close trades
  console.log('\n3️⃣ Managing open trades...');
  const openTrades = db.prepare('SELECT * FROM trades WHERE status = ?').all('OPEN');
  console.log(`  Found ${openTrades.length} open trades`);
  
  let closedCount = 0;
  let stopLosses = 0;
  let takeProfits = 0;
  
  const updateTrade = db.prepare(`
    UPDATE trades SET exit_price = ?, exit_time = ?, status = 'CLOSED', 
    profit_loss = ?, profit_loss_pct = ? WHERE id = ?
  `);
  
  for (const trade of openTrades) {
    const currentPrice = prices[trade.symbol]?.price;
    if (!currentPrice) continue;
    
    const stopLoss = trade.stop_loss || (trade.side === 'BUY' ? trade.entry_price * 0.99 : trade.entry_price * 1.01);
    const takeProfit = trade.take_profit || (trade.side === 'BUY' ? trade.entry_price * 1.02 : trade.entry_price * 0.98);
    
    let shouldClose = false;
    let exitReason = '';
    
    if (trade.side === 'BUY') {
      if (currentPrice <= stopLoss) {
        shouldClose = true;
        exitReason = 'STOP_LOSS';
        stopLosses++;
      } else if (currentPrice >= takeProfit) {
        shouldClose = true;
        exitReason = 'TAKE_PROFIT';
        takeProfits++;
      }
    }
    
    if (shouldClose) {
      const pnl = (currentPrice - trade.entry_price) * trade.quantity;
      const pnlPct = ((currentPrice - trade.entry_price) / trade.entry_price) * 100;
      updateTrade.run(currentPrice, now, pnl, pnlPct, trade.id);
      console.log(`  ✅ CLOSED ${trade.symbol} @ $${currentPrice.toLocaleString()} | ${exitReason} | P&L: $${pnl.toFixed(2)} (${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%)`);
      closedCount++;
    }
  }
  
  // Get stats
  const closedTrades = db.prepare('SELECT * FROM trades WHERE status = ?').all('CLOSED');
  const allOpen = db.prepare('SELECT * FROM trades WHERE status = ?').all('OPEN');
  
  const winning = closedTrades.filter(t => t.profit_loss > 0).length;
  const losing = closedTrades.filter(t => t.profit_loss <= 0).length;
  const totalPnl = closedTrades.reduce((sum, t) => sum + (t.profit_loss || 0), 0);
  const winRate = closedTrades.length > 0 ? (winning / closedTrades.length * 100) : 0;
  
  db.close();
  
  return { closedCount, stopLosses, takeProfits, allOpen, closedTrades, winning, losing, totalPnl, winRate };
}

async function generateSignals() {
  console.log('\n4️⃣ Generating trade signals...');
  const signals = {};
  
  for (const symbol of symbols) {
    try {
      const klines = await fetchJson(`https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=5m&limit=50`);
      const closes = klines.map(k => parseFloat(k[4]));
      
      if (closes.length >= 20) {
        const sma10 = closes.slice(-10).reduce((a, b) => a + b, 0) / 10;
        const sma20 = closes.slice(-20).reduce((a, b) => a + b, 0) / 20;
        const current = closes[closes.length - 1];
        
        const signal = sma10 > sma20 ? 'BUY' : 'HOLD';
        const confidence = sma10 > sma20 ? (sma10 / sma20 - 1 > 0.002 ? 0.6 : 0.55) : 0.5;
        
        signals[symbol] = { signal, confidence, current_price: current };
        console.log(`  ${symbol}: ${signal} (conf: ${confidence})`);
      }
    } catch (e) {
      console.log(`  Error generating signal for ${symbol}: ${e.message}`);
    }
  }
  
  return signals;
}

function updateReport(stats, signals) {
  console.log('\n5️⃣ Updating daily_trading_report.json...');
  
  const alerts = [];
  if (Math.abs(prices.SOLUSDT?.change_24h || 0) > 3) {
    alerts.push(`SOL: Significant move (${prices.SOLUSDT.change_24h >= 0 ? '+' : ''}${prices.SOLUSDT.change_24h.toFixed(2)}%)`);
  }
  
  const nextCheck = new Date();
  nextCheck.setMinutes(nextCheck.getMinutes() + 5);
  
  const report = {
    timestamp: now,
    status: 'PAPER_TRADING_ACTIVE',
    market_summary: {
      btc: prices.BTCUSDT,
      eth: prices.ETHUSDT,
      sol: prices.SOLUSDT
    },
    trading_stats: {
      total_trades: stats.closedTrades.length,
      winning_trades: stats.winning,
      losing_trades: stats.losing,
      win_rate: Math.round(stats.winRate * 10) / 10,
      total_pnl: Math.round(stats.totalPnl * 100) / 100,
      open_trades: stats.allOpen.length
    },
    signals,
    closed_trades: stats.closedCount,
    stop_losses_triggered: stats.stopLosses,
    take_profits_triggered: stats.takeProfits,
    alerts,
    next_check: nextCheck.toISOString()
  };
  
  fs.writeFileSync('projects/trading-bot/daily_trading_report.json', JSON.stringify(report, null, 2));
  console.log('  Report updated');
  
  return report;
}

async function main() {
  try {
    await fetchPrices();
    const stats = updateDatabase();
    const signals = await generateSignals();
    const report = updateReport(stats, signals);
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ DATA COLLECTION COMPLETE');
    console.log('='.repeat(60));
    console.log(`Prices updated: ${symbols.length} symbols`);
    console.log(`Trades closed: ${stats.closedCount}`);
    console.log(`  - Stop losses: ${stats.stopLosses}`);
    console.log(`  - Take profits: ${stats.takeProfits}`);
    console.log(`Open trades: ${stats.allOpen.length}`);
    console.log(`Total P&L: $${stats.totalPnl.toFixed(2)}`);
    console.log(`Win rate: ${stats.winRate.toFixed(1)}%`);
    console.log('='.repeat(60));
    
    // Output for Discord message
    const discordMsg = {
      content: `🤖 **Trading Bot Update**\n` +
        `⏰ ${new Date().toLocaleTimeString('sv-SE')}\n\n` +
        `📊 **Market:**\n` +
        `• BTC: $${prices.BTCUSDT?.price.toLocaleString()} (${prices.BTCUSDT?.change_24h >= 0 ? '+' : ''}${prices.BTCUSDT?.change_24h.toFixed(2)}%)\n` +
        `• ETH: $${prices.ETHUSDT?.price.toLocaleString()} (${prices.ETHUSDT?.change_24h >= 0 ? '+' : ''}${prices.ETHUSDT?.change_24h.toFixed(2)}%)\n` +
        `• SOL: $${prices.SOLUSDT?.price.toLocaleString()} (${prices.SOLUSDT?.change_24h >= 0 ? '+' : ''}${prices.SOLUSDT?.change_24h.toFixed(2)}%)\n\n` +
        `📈 **Stats:**\n` +
        `• Open trades: ${stats.allOpen.length}\n` +
        `• Total P&L: $${stats.totalPnl.toFixed(2)}\n` +
        `• Win rate: ${stats.winRate.toFixed(1)}%\n` +
        `• Closed this run: ${stats.closedCount}\n\n` +
        `🎯 **Signals:**\n` +
        Object.entries(signals).map(([s, d]) => `• ${s}: ${d.signal} (${(d.confidence * 100).toFixed(0)}%)`).join('\n')
    };
    
    fs.writeFileSync('projects/trading-bot/discord_update.json', JSON.stringify(discordMsg, null, 2));
    console.log('\n📱 Discord update saved to discord_update.json');
    
  } catch (e) {
    console.error('❌ Error:', e.message);
    process.exit(1);
  }
}

main();
