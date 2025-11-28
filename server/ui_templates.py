"""
UI Templates
============
HTML/CSS/JS templates for the web interface.
Separated for cleaner main.py.
"""


def get_main_ui() -> str:
    """Return the main web UI HTML."""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧊 Arctic Debate Card Agent</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --bg-dark: #0f1419;
            --bg-card: #1a1f2e;
            --bg-input: #252b3b;
            --accent-blue: #00d9ff;
            --accent-green: #00ff88;
            --accent-red: #ff6b6b;
            --accent-yellow: #ffd93d;
            --text-primary: #e8e8e8;
            --text-secondary: #888;
            --border: rgba(255,255,255,0.1);
        }
        
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, var(--bg-dark) 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: var(--text-primary);
        }
        
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        /* Header */
        header { text-align: center; padding: 20px 0; }
        h1 {
            font-size: 2.2rem;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }
        .subtitle { color: var(--text-secondary); font-size: 1rem; }
        
        /* Google Login Button */
        .google-login-btn {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            color: #333;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        .google-login-btn:hover {
            background: #f8f8f8;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        /* User Info Display */
        .user-info {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            background: rgba(0,217,255,0.1);
            border: 1px solid rgba(0,217,255,0.3);
            border-radius: 8px;
        }
        .user-avatar {
            width: 28px;
            height: 28px;
            border-radius: 50%;
        }
        .user-name {
            color: var(--text-primary);
            font-size: 0.85rem;
        }
        .logout-link {
            text-decoration: none;
            font-size: 1rem;
            opacity: 0.7;
            transition: opacity 0.2s;
        }
        .logout-link:hover { opacity: 1; }
        
        /* Admin Link */
        .admin-link {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            background: rgba(255,107,107,0.1);
            border: 1px solid rgba(255,107,107,0.3);
            border-radius: 8px;
            color: #ff6b6b;
            text-decoration: none;
            font-size: 0.9rem;
            transition: all 0.2s;
        }
        .admin-link:hover {
            background: rgba(255,107,107,0.2);
            transform: translateY(-1px);
        }
        .admin-text { font-weight: 500; }
        
        /* Usage Warning Banner */
        .usage-warning {
            background: linear-gradient(135deg, rgba(255,217,61,0.2), rgba(255,107,107,0.2));
            border: 1px solid rgba(255,217,61,0.5);
            color: #ffd93d;
            padding: 12px 20px;
            border-radius: 8px;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 500;
        }
        
        /* Navigation Tabs */
        .nav-tabs {
            display: flex;
            justify-content: center;
            gap: 8px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .nav-tab {
            padding: 10px 24px;
            border: 1px solid var(--border);
            border-radius: 25px;
            background: transparent;
            color: var(--text-secondary);
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .nav-tab:hover { border-color: var(--accent-blue); color: var(--accent-blue); }
        .nav-tab.active {
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
            color: var(--bg-dark);
            border-color: transparent;
            font-weight: 600;
        }
        
        /* Tab Content */
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        /* Cards */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        .card-title { font-size: 1.1rem; font-weight: 600; }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: var(--bg-input);
            padding: 16px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value {
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stat-label { font-size: 0.75rem; color: var(--text-secondary); margin-top: 4px; }
        
        /* Form Elements */
        input[type="text"], input[type="url"], select, textarea {
            width: 100%;
            padding: 12px 16px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--bg-input);
            color: var(--text-primary);
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s;
        }
        input:focus, select:focus, textarea:focus { border-color: var(--accent-blue); }
        input::placeholder { color: var(--text-secondary); }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary {
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
            color: var(--bg-dark);
        }
        .btn-primary:hover { transform: scale(1.02); box-shadow: 0 4px 15px rgba(0,217,255,0.3); }
        .btn-secondary { background: var(--bg-input); color: var(--text-primary); border: 1px solid var(--border); }
        .btn-danger { background: var(--accent-red); color: white; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        
        /* Article List */
        .article-list { max-height: 600px; overflow-y: auto; }
        .article-item {
            display: flex;
            gap: 16px;
            padding: 16px;
            background: var(--bg-input);
            border-radius: 10px;
            margin-bottom: 10px;
            transition: transform 0.2s;
        }
        .article-item:hover { transform: translateX(4px); }
        
        .article-side {
            width: 50px;
            height: 50px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            flex-shrink: 0;
        }
        .article-side.aff { background: rgba(0,255,136,0.2); }
        .article-side.neg { background: rgba(255,107,107,0.2); }
        .article-side.both { background: rgba(255,217,61,0.2); }
        .article-side.neutral { background: rgba(136,136,136,0.2); }
        
        .article-content { flex: 1; min-width: 0; }
        .article-title {
            font-weight: 600;
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .article-meta { font-size: 0.8rem; color: var(--text-secondary); }
        .article-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
        .tag {
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.7rem;
            background: var(--bg-card);
        }
        .tag.topic { border: 1px solid var(--accent-blue); color: var(--accent-blue); }
        .tag.source { border: 1px solid var(--accent-green); color: var(--accent-green); }
        
        .article-actions { display: flex; gap: 8px; align-items: center; }
        .article-actions button {
            padding: 6px 12px;
            border: none;
            border-radius: 6px;
            font-size: 0.8rem;
            cursor: pointer;
            background: var(--bg-card);
            color: var(--text-primary);
        }
        .article-actions button:hover { background: var(--accent-blue); color: var(--bg-dark); }
        
        /* Filters */
        .filters {
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }
        .filters select { width: auto; min-width: 140px; }
        
        /* Add Article Form */
        .add-form {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
        }
        .add-form input { flex: 1; }
        
        /* Article Detail Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        .modal.active { display: flex; }
        .modal-content {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 24px;
            max-width: 800px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .modal-close {
            background: none;
            border: none;
            font-size: 1.5rem;
            color: var(--text-secondary);
            cursor: pointer;
        }
        
        /* Chat Section */
        .chat-container { height: 400px; display: flex; flex-direction: column; }
        .messages { flex: 1; overflow-y: auto; padding: 16px; }
        .message { margin-bottom: 12px; }
        .message.user { text-align: right; }
        .message-content {
            display: inline-block;
            max-width: 80%;
            padding: 10px 16px;
            border-radius: 12px;
            line-height: 1.4;
        }
        .user .message-content { background: linear-gradient(135deg, #0066ff, var(--accent-blue)); }
        .assistant .message-content { background: var(--bg-input); }
        .message-meta { font-size: 0.7rem; color: var(--text-secondary); margin-top: 4px; }
        .url-add-btn {
            background: var(--accent-green);
            border: none;
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 0.75rem;
            cursor: pointer;
            margin-left: 4px;
            vertical-align: middle;
        }
        .url-add-btn:hover { opacity: 0.8; }
        
        .input-area { display: flex; gap: 12px; padding: 16px; background: var(--bg-input); border-radius: 0 0 12px 12px; }
        .input-area input { flex: 1; }
        
        /* Typing indicator */
        .typing { display: flex; gap: 4px; padding: 10px 16px; }
        .typing span {
            width: 8px; height: 8px;
            background: var(--accent-blue);
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out;
        }
        .typing span:nth-child(1) { animation-delay: -0.32s; }
        .typing span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
        
        /* Database Cards */
        .db-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }
        .db-card { background: var(--bg-input); border-radius: 12px; padding: 16px; }
        .db-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
        .db-icon { font-size: 1.8rem; }
        .db-name { font-weight: 600; }
        .db-type { font-size: 0.75rem; color: var(--text-secondary); }
        .db-status {
            margin-left: auto;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .db-status.connected { background: rgba(0,255,136,0.2); color: var(--accent-green); }
        .db-status.disconnected { background: rgba(255,107,107,0.2); color: var(--accent-red); }
        .db-stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
        .db-stat { background: var(--bg-card); padding: 10px; border-radius: 8px; text-align: center; }
        .db-stat-value { font-size: 1.2rem; font-weight: 700; color: var(--accent-blue); }
        .db-stat-label { font-size: 0.7rem; color: var(--text-secondary); }
        
        /* Loading */
        .loading { text-align: center; padding: 40px; color: var(--text-secondary); }
        .spinner {
            width: 40px; height: 40px;
            border: 3px solid var(--border);
            border-top-color: var(--accent-blue);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 16px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        
        /* Toast notifications */
        .toast-container { position: fixed; bottom: 20px; right: 20px; z-index: 1001; }
        .toast {
            background: var(--bg-card);
            padding: 12px 20px;
            border-radius: 8px;
            margin-bottom: 8px;
            animation: slideIn 0.3s ease;
            border-left: 4px solid var(--accent-blue);
        }
        .toast.success { border-left-color: var(--accent-green); }
        .toast.error { border-left-color: var(--accent-red); }
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h1>🧊 Arctic Debate Card Agent</h1>
                    <p class="subtitle">Policy Debate Research Assistant • 2025-2026 Topic</p>
                </div>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <button id="googleLoginBtn" class="google-login-btn" onclick="loginWithGoogle()" style="display: none;">
                        <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google" style="width:18px;height:18px;">
                        <span>Sign in</span>
                    </button>
                    <div id="userInfo" class="user-info" style="display: none;"></div>
                    <a href="/admin/ui" class="admin-link" title="Admin Panel">
                        <span>⚙️</span>
                        <span class="admin-text">Admin</span>
                    </a>
                </div>
            </div>
        </header>
        
        <!-- Usage Warning Banner -->
        <div id="usageWarning" class="usage-warning" style="display: none;">
            <span>⚠️ <span id="usageWarningText"></span></span>
            <button onclick="this.parentElement.style.display='none'" style="background:none;border:none;color:inherit;cursor:pointer;font-size:1.2rem;">&times;</button>
        </div>
        
        <!-- Navigation -->
        <nav class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('articles', event)">📚 Articles</button>
            <button class="nav-tab" onclick="showTab('cards', event)">🃏 Card Editor</button>
            <button class="nav-tab" onclick="showTab('chat', event)">💬 Chat</button>
            <button class="nav-tab" onclick="showTab('databases', event)">💾 Databases</button>
        </nav>
        
        <!-- Articles Tab -->
        <div id="tab-articles" class="tab-content active">
            <div class="stats-grid" id="articleStats">
                <div class="stat-card"><div class="stat-value" id="statTotal">-</div><div class="stat-label">Total Articles</div></div>
                <div class="stat-card"><div class="stat-value" id="statAff">-</div><div class="stat-label">Affirmative</div></div>
                <div class="stat-card"><div class="stat-value" id="statNeg">-</div><div class="stat-label">Negative</div></div>
                <div class="stat-card"><div class="stat-value" id="statProcessed">-</div><div class="stat-label">Analyzed</div></div>
            </div>
            
            <!-- Batch Action Bar -->
            <div id="batchActionBar" style="display: none; background: linear-gradient(135deg, #ff6b6b, #ffd93d); padding: 12px 20px; border-radius: 8px; margin-bottom: 16px; align-items: center; justify-content: space-between;">
                <span style="color: #000; font-weight: 600;">
                    <span id="selectedCount">0</span> articles selected
                </span>
                <div style="display: flex; gap: 12px;">
                    <button class="btn" onclick="batchCutCards()" style="background: #000; color: #fff;">🃏 Cut Cards from Selected</button>
                    <button class="btn" onclick="clearSelection()" style="background: rgba(0,0,0,0.2); color: #000;">✕ Clear</button>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">➕ Add New Article</span>
                </div>
                <div class="add-form">
                    <input type="url" id="articleUrl" placeholder="Paste article URL here...">
                    <button class="btn btn-primary" onclick="addArticle()" id="addBtn">Add & Analyze</button>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">📖 Article Library</span>
                    <button class="btn btn-secondary" onclick="seedArticles()">🌱 Seed 30 Articles</button>
                </div>
                
                <div class="filters">
                    <button onclick="selectAllArticles()" class="btn btn-secondary" style="padding: 8px 12px; font-size: 0.85rem;">☑️ Select All</button>
                    <select id="filterSide" onchange="loadArticles()">
                        <option value="">All Sides</option>
                        <option value="aff">🟢 Affirmative</option>
                        <option value="neg">🔴 Negative</option>
                        <option value="both">🟡 Both</option>
                    </select>
                    <select id="filterSource" onchange="loadArticles()">
                        <option value="">All Sources</option>
                        <option value="news">📰 News</option>
                        <option value="think_tank">🏛️ Think Tank</option>
                        <option value="academic">📚 Academic</option>
                        <option value="government">🏢 Government</option>
                    </select>
                    <select id="filterTopic" onchange="loadArticles()">
                        <option value="">All Topics</option>
                        <option value="security">🛡️ Security</option>
                        <option value="climate">🌡️ Climate</option>
                        <option value="economy">💰 Economy</option>
                        <option value="shipping">🚢 Shipping</option>
                        <option value="energy">⚡ Energy</option>
                        <option value="indigenous">👥 Indigenous</option>
                        <option value="environment">🌿 Environment</option>
                    </select>
                    <input type="text" id="searchQuery" placeholder="Search articles..." style="width: 200px;" onkeyup="debounceSearch()">
                </div>
                
                <div class="article-list" id="articleList">
                    <div class="loading"><div class="spinner"></div>Loading articles...</div>
                </div>
            </div>
        </div>
        
        <!-- Card Editor Tab -->
        <div id="tab-cards" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">🃏 Debate Card Formatter</span>
                    <span style="font-size: 0.8rem; color: var(--text-secondary);">Paste evidence → Get formatted card → Copy to Google Docs</span>
                </div>
                
                <!-- Input Section -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                    <!-- Left: Evidence Input -->
                    <div>
                        <label style="display: block; margin-bottom: 8px; font-weight: 600;">📝 Evidence Text</label>
                        <textarea id="cardEvidence" placeholder="Paste the evidence/quote here..." style="width: 100%; height: 200px; resize: vertical;"></textarea>
                    </div>
                    
                    <!-- Right: Citation Info -->
                    <div>
                        <label style="display: block; margin-bottom: 8px; font-weight: 600;">📖 Citation Info</label>
                        <div style="display: grid; gap: 10px;">
                            <input type="text" id="cardAuthor" placeholder="Author (e.g., Geoffroy et al.)">
                            <input type="text" id="cardYear" placeholder="Year (e.g., 2023)">
                            <input type="text" id="cardTitle" placeholder="Article Title">
                            <input type="text" id="cardSource" placeholder="Source (e.g., Nature, NOAA)">
                            <input type="url" id="cardUrl" placeholder="URL (for citation)">
                            <input type="text" id="cardQuals" placeholder="Qualifications (optional)">
                            <input type="text" id="cardContext" placeholder="Argument context (e.g., Ecosystem Advantage)">
                        </div>
                    </div>
                </div>
                
                <div style="display: flex; gap: 12px; margin-bottom: 20px;">
                    <button class="btn btn-primary" onclick="formatCard()" id="formatBtn">✨ Format Card</button>
                    <button class="btn btn-secondary" onclick="extractCards()">📚 Extract Multiple Cards</button>
                    <label style="display: flex; align-items: center; gap: 6px; color: var(--text-secondary);">
                        <input type="checkbox" id="autoHighlight" checked> Auto-highlight key phrases
                    </label>
                </div>
            </div>
            
            <!-- Output Section - The Formatted Card -->
            <div class="card" id="cardOutputSection" style="display: none;">
                <div class="card-header">
                    <span class="card-title">📄 Formatted Card</span>
                    <div style="display: flex; gap: 8px;">
                        <button class="btn btn-primary" onclick="copyCard()" title="Copy with formatting for Google Docs">📋 Copy to Clipboard</button>
                        <button class="btn btn-secondary" onclick="copyPlainCard()" title="Copy as plain text">📝 Plain Text</button>
                    </div>
                </div>
                
                <!-- The actual card display - styled for copying -->
                <div id="formattedCard" style="background: white; color: #000; padding: 20px; border-radius: 8px; font-family: 'Times New Roman', serif; font-size: 12pt; line-height: 1.5;">
                    <!-- Card content will be inserted here -->
                </div>
                
                <div style="margin-top: 16px; padding: 12px; background: var(--bg-input); border-radius: 8px;">
                    <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 8px;">
                        💡 <strong>Formatting Guide:</strong>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); display: flex; gap: 20px; flex-wrap: wrap;">
                        <span><strong style="color: var(--accent-blue);">BOLD</strong> = Tag (the claim)</span>
                        <span style="background: #ffff00; color: #000; padding: 0 4px;">Yellow Highlight</span> = Key phrases (read in round)</span>
                    </div>
                </div>
            </div>
            
            <!-- Extracted Cards Section -->
            <div class="card" id="extractedCardsSection" style="display: none;">
                <div class="card-header">
                    <span class="card-title">📚 Extracted Cards</span>
                    <button class="btn btn-secondary" onclick="document.getElementById('extractedCardsSection').style.display='none'">✕ Close</button>
                </div>
                <div id="extractedCardsList"></div>
            </div>
        </div>
        
        <!-- Chat Tab -->
        <div id="tab-chat" class="tab-content">
            <div class="card chat-container" style="height: auto; min-height: 500px;">
                <div class="messages" id="messages" style="height: 350px;">
                    <div class="message assistant">
                        <div class="message-content">
                            👋 Hi! I'm your Arctic Debate Research Assistant. I can help you:<br><br>
                            • Find evidence for arguments<br>
                            • Explain Arctic policy topics<br>
                            • Suggest debate strategies<br>
                            • Analyze documents you paste<br><br>
                            What would you like to know about the Arctic topic?
                        </div>
                    </div>
                </div>
                
                <!-- Attachment Area -->
                <div id="attachmentArea" style="display: none; padding: 12px; background: var(--bg-input); border-top: 1px solid var(--border);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 0.85rem; color: var(--accent-blue);">📎 Attached Document</span>
                        <button onclick="clearAttachment()" style="background: none; border: none; color: var(--accent-red); cursor: pointer;">✕ Remove</button>
                    </div>
                    <textarea id="attachmentText" placeholder="Paste article text, document content, or evidence here..." style="width: 100%; height: 100px; resize: vertical;"></textarea>
                </div>
                
                <div class="input-area" style="flex-direction: column; gap: 8px;">
                    <div style="display: flex; gap: 12px; width: 100%;">
                        <input type="text" id="chatInput" placeholder="Ask about Arctic debate..." onkeypress="if(event.key==='Enter' && !event.shiftKey)sendChat()" style="flex: 1;">
                        <button class="btn btn-secondary" onclick="toggleAttachment()" id="attachBtn" title="Add document to analyze">📎</button>
                        <button class="btn btn-primary" onclick="sendChat()">Send</button>
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-secondary);">
                        💡 Tip: Click 📎 to paste article text for analysis. Ask "Summarize this" or "Is this aff or neg evidence?"
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Databases Tab -->
        <div id="tab-databases" class="tab-content">
            <div class="db-grid" id="dbGrid">
                <div class="loading"><div class="spinner"></div>Loading database info...</div>
            </div>
        </div>
    </div>
    
    <!-- Article Detail Modal -->
    <div class="modal" id="articleModal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">Article Details</h2>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div id="modalBody"></div>
        </div>
    </div>
    
    <!-- Toast Container -->
    <div class="toast-container" id="toastContainer"></div>
    
    <script>
        // ==================== Verbose Logging ====================
        const DEBUG = true;
        const LOG_PREFIX = '🧊 [DebateAgent]';
        
        const log = {
            info: (...args) => console.log(LOG_PREFIX, '📘', ...args),
            debug: (...args) => DEBUG && console.log(LOG_PREFIX, '🔍', ...args),
            warn: (...args) => console.warn(LOG_PREFIX, '⚠️', ...args),
            error: (...args) => console.error(LOG_PREFIX, '❌', ...args),
            api: (method, url, data) => {
                console.groupCollapsed(LOG_PREFIX, '🌐', method, url);
                if (data) console.log('Request:', data);
                console.groupEnd();
            },
            response: (url, status, data, timeMs) => {
                const emoji = status < 400 ? '✅' : '❌';
                console.groupCollapsed(LOG_PREFIX, emoji, status, url, `(${timeMs}ms)`);
                if (data) console.log('Response:', data);
                console.groupEnd();
            },
            cache: (hit, key) => DEBUG && console.log(LOG_PREFIX, hit ? '💾 CACHE HIT' : '💨 CACHE MISS', key),
            user: (action, user) => console.log(LOG_PREFIX, '👤', action, user?.email || 'anonymous')
        };
        
        log.info('Arctic Debate Card Agent - Initializing...');
        log.debug('Debug mode:', DEBUG);
        
        // ==================== State Management ====================
        let sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
        let searchTimeout = null;
        let selectedArticles = new Set();  // For batch article selection
        let currentArticle = null;  // For card cutting
        let currentUser = null;  // For authentication
        
        log.debug('Session ID:', sessionId);
        
        // ==================== API Helper with Logging ====================
        async function apiCall(method, url, data = null, options = {}) {
            const startTime = performance.now();
            log.api(method, url, data);
            
            try {
                const config = {
                    method,
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',  // Include cookies for auth
                    ...options
                };
                
                if (data && method !== 'GET') {
                    config.body = JSON.stringify(data);
                }
                
                const response = await fetch(url, config);
                const timeMs = Math.round(performance.now() - startTime);
                
                let responseData;
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    responseData = await response.json();
                } else {
                    responseData = await response.text();
                }
                
                log.response(url, response.status, responseData, timeMs);
                
                // Handle 401 Unauthorized - redirect to login
                if (response.status === 401) {
                    log.warning('Authentication required - redirecting to login');
                    showToast('Please login to continue', 'warning');
                    setTimeout(() => loginWithGoogle(), 1500);
                    throw new Error('Authentication required');
                }
                
                if (!response.ok) {
                    throw new Error(responseData.detail || `HTTP ${response.status}`);
                }
                
                return responseData;
            } catch (error) {
                const timeMs = Math.round(performance.now() - startTime);
                log.error(`API Error (${timeMs}ms):`, error.message);
                throw error;
            }
        }
        
        // ==================== Authentication ====================
        async function checkAuth() {
            log.info('🔐 Checking authentication status...');
            try {
                const data = await apiCall('GET', '/auth/me');
                log.debug('Auth response:', data);
                if (data.authenticated) {
                    currentUser = data.user;
                    log.info('✅ User authenticated:', currentUser.email);
                    log.debug('User details:', currentUser);
                    updateAuthUI(true);
                } else {
                    currentUser = null;
                    log.info('👤 Not authenticated (anonymous user)');
                    updateAuthUI(false);
                }
            } catch (e) {
                log.error('Auth check failed:', e.message);
                currentUser = null;
                updateAuthUI(false);
            }
        }
        
        async function checkAuthStatus() {
            log.info('🔐 Checking Google OAuth configuration...');
            try {
                const data = await apiCall('GET', '/auth/status');
                log.debug('Auth status response:', data);
                
                if (data.google_enabled) {
                    document.getElementById('googleLoginBtn').style.display = 'flex';
                    log.info('✅ Google Auth is ENABLED');
                    log.debug('Client ID set:', data.client_id_set);
                    log.debug('Client Secret set:', data.client_secret_set);
                } else {
                    log.warn('⚠️ Google Auth is DISABLED');
                    log.warn('Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env');
                    
                    // Show debug info in UI
                    const loginBtn = document.getElementById('googleLoginBtn');
                    if (loginBtn) {
                        loginBtn.innerHTML = '<span style="color:#ff6b6b;">⚠️ Auth not configured</span>';
                        loginBtn.style.display = 'flex';
                        loginBtn.style.opacity = '0.5';
                        loginBtn.onclick = () => alert('Google OAuth not configured.\\n\\nAdd to .env:\\nGOOGLE_CLIENT_ID=...\\nGOOGLE_CLIENT_SECRET=...');
                    }
                }
            } catch (e) {
                log.error('Auth status check failed:', e.message);
            }
        }
        
        function updateAuthUI(isAuthenticated) {
            const loginBtn = document.getElementById('googleLoginBtn');
            const userInfo = document.getElementById('userInfo');
            
            if (isAuthenticated && currentUser) {
                loginBtn.style.display = 'none';
                userInfo.style.display = 'flex';
                userInfo.innerHTML = `
                    <img src="${currentUser.picture_url || ''}" alt="" class="user-avatar" onerror="this.style.display='none'">
                    <span class="user-name">${currentUser.name || currentUser.email}</span>
                    <a href="/auth/logout" class="logout-link" title="Logout">🚪</a>
                `;
            } else {
                if (loginBtn) loginBtn.style.display = 'flex';
                if (userInfo) userInfo.style.display = 'none';
            }
        }
        
        function loginWithGoogle() {
            log.info('Redirecting to login page...');
            const currentUrl = window.location.pathname;
            const returnUrl = encodeURIComponent(currentUrl || '/ui');
            log.debug('Current URL:', currentUrl);
            log.debug('Return URL:', returnUrl);
            window.location.href = '/auth/page?return_url=' + returnUrl;
        }
        
        // ==================== Tab Switching ====================
        function showTab(tab, clickEvent) {
            log.debug('Switching to tab:', tab);
            
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.getElementById('tab-' + tab).classList.add('active');
            
            // Handle both click events and programmatic calls
            if (clickEvent && clickEvent.target) {
                clickEvent.target.classList.add('active');
            } else {
                // Find and activate the correct tab button
                document.querySelectorAll('.nav-tab').forEach(btn => {
                    if (btn.textContent.toLowerCase().includes(tab)) {
                        btn.classList.add('active');
                    }
                });
            }
            
            if (tab === 'articles') loadArticles();
            if (tab === 'databases') loadDbInfo();
        }
        
        // Toast notifications
        function showToast(message, type = 'info') {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = 'toast ' + type;
            toast.textContent = message;
            container.appendChild(toast);
            setTimeout(() => toast.remove(), 4000);
        }
        
        // Load article stats
        async function loadStats() {
            try {
                const res = await fetch('/articles/stats');
                const data = await res.json();
                document.getElementById('statTotal').textContent = data.total_articles || 0;
                document.getElementById('statAff').textContent = data.aff_articles || 0;
                document.getElementById('statNeg').textContent = data.neg_articles || 0;
                document.getElementById('statProcessed').textContent = data.processed_articles || 0;
            } catch (e) { console.error('Stats error:', e); }
        }
        
        // Load articles
        async function loadArticles() {
            const list = document.getElementById('articleList');
            list.innerHTML = '<div class="loading"><div class="spinner"></div>Loading...</div>';
            
            const side = document.getElementById('filterSide').value;
            const source = document.getElementById('filterSource').value;
            const topic = document.getElementById('filterTopic').value;
            const search = document.getElementById('searchQuery').value;
            
            let url = '/articles?limit=50';
            if (side) url += '&side=' + side;
            if (source) url += '&source_type=' + source;
            if (topic) url += '&topic_area=' + topic;
            
            try {
                let articles;
                if (search) {
                    const res = await fetch('/articles/search', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        credentials: 'include',
                        body: JSON.stringify({query: search, n_results: 50})
                    });
                    const data = await res.json();
                    articles = data.results || [];
                } else {
                    const res = await fetch(url);
                    const data = await res.json();
                    articles = data.articles || [];
                }
                
                if (articles.length === 0) {
                    list.innerHTML = '<div class="loading">No articles found. Add some or seed the database!</div>';
                    return;
                }
                
                list.innerHTML = articles.map(a => renderArticle(a)).join('');
            } catch (e) {
                list.innerHTML = '<div class="loading">Error loading articles</div>';
            }
        }
        
        function renderArticle(a) {
            const sideIcon = {aff: '🟢', neg: '🔴', both: '🟡', neutral: '⚪'}[a.side] || '⚪';
            // SECURITY: Escape topic areas to prevent XSS
            const topics = (a.topic_areas || []).slice(0, 3).map(t => `<span class="tag topic">${escapeHtml(t)}</span>`).join('');
            const processed = a.is_processed ? '✅' : '⏳';
            const isSelected = selectedArticles.has(a.id);
            
            // SECURITY: Escape user-generated content
            const safeTitle = escapeHtml(a.title || 'Untitled');
            const safeSource = escapeHtml(a.source_name || 'Unknown');
            const safeSourceType = escapeHtml(a.source_type || 'unknown');
            
            return `
                <div class="article-item" style="display: flex; align-items: center;">
                    <input type="checkbox" 
                           class="article-checkbox" 
                           data-article-id="${a.id}"
                           ${isSelected ? 'checked' : ''}
                           onchange="toggleArticleSelect(${a.id}, this)"
                           style="width: 18px; height: 18px; margin-right: 12px; cursor: pointer; accent-color: var(--accent-blue);">
                    <div class="article-side ${escapeHtml(a.side || 'neutral')}">${sideIcon}</div>
                    <div class="article-content" style="flex: 1;">
                        <div class="article-title">${safeTitle}</div>
                        <div class="article-meta">${safeSource} • ${a.publication_year || '?'} • ${processed}</div>
                        <div class="article-tags">${topics}<span class="tag source">${safeSourceType}</span></div>
                    </div>
                    <div class="article-actions">
                        <button onclick="viewArticle(${a.id})">View</button>
                        <button onclick="quickCutCard(${a.id})" title="Quick cut card" style="background: linear-gradient(135deg, #ff6b6b, #ffd93d); color: #000;">🃏</button>
                        ${!a.is_processed ? `<button onclick="analyzeArticle(${a.id})">Analyze</button>` : ''}
                    </div>
                </div>
            `;
        }
        
        // Quick cut card without opening modal
        async function quickCutCard(articleId) {
            try {
                const res = await fetch('/articles/' + articleId);
                const a = await res.json();
                currentArticle = a;
                cutCardFromArticle();
            } catch (e) {
                showToast('Error loading article', 'error');
            }
        }
        
        // Add article
        async function addArticle() {
            const url = document.getElementById('articleUrl').value.trim();
            if (!url) return showToast('Please enter a URL', 'error');
            
            const btn = document.getElementById('addBtn');
            btn.disabled = true;
            btn.textContent = 'Analyzing...';
            
            try {
                const res = await fetch('/articles/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({url})
                });
                const data = await res.json();
                
                if (data.success) {
                    showToast('Article added successfully!', 'success');
                    document.getElementById('articleUrl').value = '';
                    loadArticles();
                    loadStats();
                } else {
                    showToast(data.error || 'Failed to add article', 'error');
                }
            } catch (e) {
                showToast('Error adding article', 'error');
            }
            
            btn.disabled = false;
            btn.textContent = 'Add & Analyze';
        }
        
        // View article (currentArticle defined at top for card cutting)
        async function viewArticle(id) {
            try {
                const res = await fetch('/articles/' + id);
                const a = await res.json();
                currentArticle = a;  // Store for cut card
                
                // SECURITY: Escape all user-generated content
                const safeTitle = escapeHtml(a.title || 'Article Details');
                const safeSource = escapeHtml(a.source_name || 'Unknown');
                const safeSourceType = escapeHtml(a.source_type || 'unknown');
                const safeAuthor = escapeHtml(a.author_name || 'Unknown');
                const safeCreds = escapeHtml(a.author_credentials || '');
                const safeSummary = escapeHtml(a.summary || 'No summary available. Click Analyze to generate.');
                const safeSide = escapeHtml(a.side || 'Unclassified');
                const safeUrl = escapeHtml(a.url);
                
                document.getElementById('modalTitle').textContent = safeTitle;
                document.getElementById('modalBody').innerHTML = `
                    <p><strong>Source:</strong> ${safeSource} (${safeSourceType})</p>
                    <p><strong>Author:</strong> ${safeAuthor} ${safeCreds ? '- ' + safeCreds : ''}</p>
                    <p><strong>Year:</strong> ${a.publication_year || 'Unknown'}</p>
                    <p><strong>Side:</strong> ${safeSide} ${a.side_confidence ? '(' + Math.round(a.side_confidence * 100) + '% confidence)' : ''}</p>
                    <p><strong>Relevance:</strong> ${a.relevance_score || '-'}/10</p>
                    <hr style="margin: 16px 0; border-color: var(--border);">
                    <p><strong>Summary:</strong></p>
                    <p style="color: var(--text-secondary); margin-bottom: 16px;">${safeSummary}</p>
                    ${a.key_claims && a.key_claims.length ? `
                        <p><strong>Key Claims:</strong></p>
                        <ul style="margin-left: 20px; color: var(--text-secondary);">
                            ${a.key_claims.map(c => `<li>${escapeHtml(c)}</li>`).join('')}
                        </ul>
                    ` : ''}
                    <hr style="margin: 16px 0; border-color: var(--border);">
                    <p><strong>URL:</strong> <a href="${safeUrl}" target="_blank" rel="noopener noreferrer" style="color: var(--accent-blue);">${safeUrl}</a></p>
                    <div style="margin-top: 20px; display: flex; gap: 12px; flex-wrap: wrap;">
                        <button class="btn btn-primary" onclick="cutCardFromArticle()" style="background: linear-gradient(135deg, #ff6b6b, #ffd93d);">🃏 Cut Card</button>
                        ${!a.is_processed ? `<button class="btn btn-primary" onclick="analyzeArticle(${a.id}); closeModal();">Analyze with GPT</button>` : ''}
                        <button class="btn btn-secondary" onclick="fetchAndCutCard(${a.id})">📥 Fetch & Cut</button>
                        <button class="btn btn-danger" onclick="deleteArticle(${a.id}); closeModal();">Delete</button>
                    </div>
                `;
                document.getElementById('articleModal').classList.add('active');
            } catch (e) {
                showToast('Error loading article', 'error');
            }
        }
        
        function closeModal() {
            document.getElementById('articleModal').classList.remove('active');
        }
        
        // Analyze article
        async function analyzeArticle(id) {
            showToast('Analyzing article with GPT...', 'info');
            try {
                const res = await fetch('/articles/' + id + '/analyze', {method: 'POST', credentials: 'include'});
                const data = await res.json();
                if (data.success) {
                    showToast('Article analyzed!', 'success');
                    loadArticles();
                    loadStats();
                } else {
                    showToast(data.error || 'Analysis failed', 'error');
                }
            } catch (e) {
                showToast('Error analyzing article', 'error');
            }
        }
        
        // Delete article
        async function deleteArticle(id) {
            if (!confirm('Delete this article?')) return;
            try {
                await fetch('/articles/' + id, {method: 'DELETE', credentials: 'include'});
                showToast('Article deleted', 'success');
                loadArticles();
                loadStats();
            } catch (e) {
                showToast('Error deleting article', 'error');
            }
        }
        
        // Seed articles
        async function seedArticles() {
            showToast('Seeding articles...', 'info');
            try {
                const res = await fetch('/articles/seed', {method: 'POST', credentials: 'include'});
                const data = await res.json();
                showToast(data.message, 'success');
                loadArticles();
                loadStats();
            } catch (e) {
                showToast('Error seeding articles', 'error');
            }
        }
        
        // Search debounce
        function debounceSearch() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(loadArticles, 300);
        }
        
        // Chat
        // Attachment functions
        function toggleAttachment() {
            const area = document.getElementById('attachmentArea');
            const btn = document.getElementById('attachBtn');
            if (area.style.display === 'none') {
                area.style.display = 'block';
                btn.style.background = 'var(--accent-blue)';
                btn.style.color = 'var(--bg-dark)';
            } else {
                area.style.display = 'none';
                btn.style.background = '';
                btn.style.color = '';
            }
        }
        
        function clearAttachment() {
            document.getElementById('attachmentText').value = '';
            toggleAttachment();
        }
        
        async function sendChat() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            const attachmentText = document.getElementById('attachmentText').value.trim();
            
            if (!message) return;
            
            // Show user message with attachment indicator
            let displayMsg = message;
            if (attachmentText) {
                displayMsg += ' 📎';
            }
            addMessage(displayMsg, 'user');
            input.value = '';
            
            const typingId = showTyping();
            
            try {
                const payload = {
                    message, 
                    session_id: sessionId,
                    use_cache: !attachmentText,  // Don't cache if has attachment
                    use_memory: true
                };
                
                // Add attachment if present
                if (attachmentText) {
                    payload.attachment_text = attachmentText;
                    // Clear attachment after sending
                    document.getElementById('attachmentText').value = '';
                    document.getElementById('attachmentArea').style.display = 'none';
                    document.getElementById('attachBtn').style.background = '';
                    document.getElementById('attachBtn').style.color = '';
                }
                
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                removeTyping(typingId);
                
                // Handle 401 Unauthorized
                if (res.status === 401) {
                    addMessage('⚠️ Please login to use the chat feature. Click "Sign in" above.', 'assistant');
                    showToast('Login required', 'warning');
                    return;
                }
                
                if (data.success) {
                    const meta = `${data.response_time_ms}ms • ${data.tokens_used} tokens`;
                    addMessage(data.response, 'assistant', meta);
                } else {
                    addMessage('Error: ' + (data.error || 'Unknown error'), 'assistant');
                }
            } catch (e) {
                removeTyping(typingId);
                log.error('Chat error:', e.message);
                addMessage('Error connecting to server: ' + e.message, 'assistant');
            }
        }
        
        function addMessage(text, role, meta = '') {
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = 'message ' + role;
            
            // Process text to make URLs clickable and add "Add to Library" buttons
            let processedText = text.replace(/\\n/g, '<br>');
            
            // Find URLs and make them clickable with add button
            if (role === 'assistant') {
                const urlRegex = /(https?:\\/\\/[^\\s<]+)/g;
                const urls = text.match(urlRegex) || [];
                
                // Replace URLs with clickable links
                processedText = processedText.replace(urlRegex, (url) => {
                    return `<a href="${url}" target="_blank" style="color: var(--accent-blue);">${url}</a> <button onclick="quickAddUrl('${url}')" class="url-add-btn" title="Add to Article Library">📥</button>`;
                });
            }
            
            div.innerHTML = `
                <div class="message-content">${processedText}</div>
                ${meta ? '<div class="message-meta">' + meta + '</div>' : ''}
            `;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        // Quick add URL from chat to article library
        async function quickAddUrl(url) {
            // Check for duplicates first
            try {
                const checkRes = await fetch('/articles/check-url?url=' + encodeURIComponent(url));
                const checkData = await checkRes.json();
                
                if (checkData.exists) {
                    showToast('Article already in library!', 'info');
                    return;
                }
            } catch (e) {
                // If check fails, try to add anyway
            }
            
            showToast('Adding to library...', 'info');
            
            try {
                const res = await fetch('/articles/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({url: url})
                });
                const data = await res.json();
                
                if (data.success) {
                    showToast('Added to library! Go to Articles tab to view.', 'success');
                } else {
                    showToast(data.error || 'Failed to add', 'error');
                }
            } catch (e) {
                showToast('Error adding article', 'error');
            }
        }
        
        function showTyping() {
            const messages = document.getElementById('messages');
            const id = 'typing_' + Date.now();
            const div = document.createElement('div');
            div.className = 'message assistant';
            div.id = id;
            div.innerHTML = '<div class="message-content typing"><span></span><span></span><span></span></div>';
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
            return id;
        }
        
        function removeTyping(id) {
            const el = document.getElementById(id);
            if (el) el.remove();
        }
        
        // Database info
        async function loadDbInfo() {
            const grid = document.getElementById('dbGrid');
            grid.innerHTML = '<div class="loading"><div class="spinner"></div>Loading...</div>';
            
            try {
                const res = await fetch('/db-info', {credentials: 'include'});
                const data = await res.json();
                
                grid.innerHTML = `
                    <div class="db-card">
                        <div class="db-header">
                            <span class="db-icon">🐘</span>
                            <div><div class="db-name">PostgreSQL</div><div class="db-type">Relational Database</div></div>
                            <span class="db-status ${data.postgresql?.status === 'connected' ? 'connected' : 'disconnected'}">
                                ${data.postgresql?.status || 'Unknown'}
                            </span>
                        </div>
                        <div class="db-stats">
                            <div class="db-stat"><div class="db-stat-value">${data.postgresql?.conversations || 0}</div><div class="db-stat-label">Conversations</div></div>
                            <div class="db-stat"><div class="db-stat-value">${data.postgresql?.articles || 0}</div><div class="db-stat-label">Articles</div></div>
                        </div>
                    </div>
                    <div class="db-card">
                        <div class="db-header">
                            <span class="db-icon">⚡</span>
                            <div><div class="db-name">Redis</div><div class="db-type">In-Memory Cache</div></div>
                            <span class="db-status ${data.redis?.status === 'connected' ? 'connected' : 'disconnected'}">
                                ${data.redis?.status || 'Unknown'}
                            </span>
                        </div>
                        <div class="db-stats">
                            <div class="db-stat"><div class="db-stat-value">${data.redis?.keys || 0}</div><div class="db-stat-label">Cached Keys</div></div>
                            <div class="db-stat"><div class="db-stat-value">${data.redis?.memory_used || '-'}</div><div class="db-stat-label">Memory</div></div>
                        </div>
                    </div>
                    <div class="db-card">
                        <div class="db-header">
                            <span class="db-icon">🔮</span>
                            <div><div class="db-name">ChromaDB</div><div class="db-type">Vector Store</div></div>
                            <span class="db-status ${data.chromadb?.status === 'connected' ? 'connected' : 'disconnected'}">
                                ${data.chromadb?.status || 'Unknown'}
                            </span>
                        </div>
                        <div class="db-stats">
                            <div class="db-stat"><div class="db-stat-value">${data.chromadb?.total_documents || 0}</div><div class="db-stat-label">Documents</div></div>
                            <div class="db-stat"><div class="db-stat-value">${data.chromadb?.collections || 0}</div><div class="db-stat-label">Collections</div></div>
                        </div>
                    </div>
                    <div class="db-card">
                        <div class="db-header">
                            <span class="db-icon">🌲</span>
                            <div><div class="db-name">Pinecone</div><div class="db-type">Cloud Vector DB</div></div>
                            <span class="db-status ${data.pinecone?.status === 'connected' ? 'connected' : 'disconnected'}">
                                ${data.pinecone?.status || 'Unknown'}
                            </span>
                        </div>
                        <div class="db-stats">
                            <div class="db-stat"><div class="db-stat-value">${data.pinecone?.indexes || 0}</div><div class="db-stat-label">Indexes</div></div>
                            <div class="db-stat"><div class="db-stat-value">${data.pinecone?.environment || '-'}</div><div class="db-stat-label">Environment</div></div>
                        </div>
                    </div>
                `;
            } catch (e) {
                grid.innerHTML = '<div class="loading">Error loading database info</div>';
            }
        }
        
        // ==================== ARTICLE TO CARD FUNCTIONS ====================
        
        // Cut card from currently viewed article (uses summary/claims as evidence)
        function cutCardFromArticle() {
            if (!currentArticle) {
                showToast('No article loaded', 'error');
                return;
            }
            
            const a = currentArticle;
            log.info('=== CUTTING CARD FROM ARTICLE ===');
            log.debug('Full article data:', JSON.stringify(a, null, 2));
            log.debug('author_name:', a.author_name);
            log.debug('source_name:', a.source_name);
            log.debug('publication_year:', a.publication_year);
            log.debug('discovered_at:', a.discovered_at);
            
            // Build evidence text from summary and key claims
            let evidence = '';
            if (a.summary) {
                evidence = a.summary;
            }
            if (a.key_claims && a.key_claims.length) {
                evidence += '\\n\\n' + a.key_claims.join('\\n');
            }
            if (!evidence) {
                evidence = 'Article needs to be analyzed first. Click "Analyze with GPT" or use "Fetch & Cut" to get content.';
            }
            
            // Switch to card editor tab
            showTab('cards');
            
            // Extract year - multiple fallbacks
            let year = a.publication_year;
            log.debug('Year from publication_year:', year);
            if (!year && a.discovered_at) {
                try {
                    year = new Date(a.discovered_at).getFullYear();
                    log.debug('Year from discovered_at:', year);
                } catch (e) {
                    log.warn('Could not parse discovered_at:', a.discovered_at);
                }
            }
            if (!year) {
                year = new Date().getFullYear();
                log.debug('Using current year:', year);
            }
            
            // Get author - multiple fallbacks
            let author = a.author_name;
            log.debug('Author from author_name:', author);
            if (!author && a.source_name) {
                author = a.source_name;
                log.debug('Author from source_name:', author);
            }
            if (!author) {
                author = 'Unknown';
                log.warn('No author found, using Unknown');
            }
            
            // Populate card editor fields
            log.info('Setting card fields:', {author, year, title: a.title, source: a.source_name, url: a.url});
            
            document.getElementById('cardEvidence').value = evidence;
            document.getElementById('cardAuthor').value = author;
            document.getElementById('cardYear').value = year;
            document.getElementById('cardTitle').value = a.title || '';
            document.getElementById('cardSource').value = a.source_name || '';
            document.getElementById('cardUrl').value = a.url || '';
            document.getElementById('cardQuals').value = a.author_credentials || '';
            document.getElementById('cardContext').value = a.side ? (a.side === 'aff' ? 'Affirmative' : a.side === 'neg' ? 'Negative' : 'Both sides') : '';
            
            // Verify fields were set
            log.debug('Verifying field values after set:');
            log.debug('  cardAuthor:', document.getElementById('cardAuthor').value);
            log.debug('  cardYear:', document.getElementById('cardYear').value);
            log.debug('  cardTitle:', document.getElementById('cardTitle').value);
            log.debug('  cardSource:', document.getElementById('cardSource').value);
            
            closeModal();
            showToast('Article loaded into Card Editor - edit evidence and format!', 'success');
        }
        
        // Fetch article content from URL and cut card
        async function fetchAndCutCard(articleId) {
            showToast('Fetching article content...', 'info');
            closeModal();
            
            try {
                // First get the article info
                const artRes = await fetch('/articles/' + articleId);
                const article = await artRes.json();
                
                // Fetch the actual article content
                const fetchRes = await fetch('/articles/' + articleId + '/fetch', {method: 'POST', credentials: 'include'});
                const fetchData = await fetchRes.json();
                
                if (!fetchData.success) {
                    showToast(fetchData.error || 'Failed to fetch article', 'error');
                    return;
                }
                
                // Switch to card editor
                showTab('cards');
                
                // Get year with fallbacks
                let year = article.publication_year;
                if (!year && article.discovered_at) {
                    year = new Date(article.discovered_at).getFullYear();
                }
                if (!year) {
                    year = new Date().getFullYear();
                }
                
                // Get author with fallbacks
                let author = article.author_name || article.source_name || 'Unknown';
                
                // Populate with fetched content
                document.getElementById('cardEvidence').value = fetchData.content || '';
                document.getElementById('cardAuthor').value = author;
                document.getElementById('cardYear').value = year;
                document.getElementById('cardTitle').value = fetchData.title || article.title || '';
                document.getElementById('cardSource').value = article.source_name || '';
                document.getElementById('cardUrl').value = article.url || '';
                document.getElementById('cardQuals').value = article.author_credentials || '';
                
                showToast(`Fetched ${fetchData.content?.length || 0} chars - extract cards or format!`, 'success');
                
            } catch (e) {
                showToast('Error fetching article: ' + e.message, 'error');
            }
        }
        
        // Batch selection functions (selectedArticles defined at top)
        
        function toggleArticleSelect(id, checkbox) {
            if (checkbox.checked) {
                selectedArticles.add(id);
            } else {
                selectedArticles.delete(id);
            }
            updateSelectionUI();
        }
        
        function updateSelectionUI() {
            const count = selectedArticles.size;
            const batchBar = document.getElementById('batchActionBar');
            if (count > 0) {
                batchBar.style.display = 'flex';
                document.getElementById('selectedCount').textContent = count;
            } else {
                batchBar.style.display = 'none';
            }
        }
        
        function selectAllArticles() {
            const checkboxes = document.querySelectorAll('.article-checkbox');
            const allChecked = Array.from(checkboxes).every(cb => cb.checked);
            
            checkboxes.forEach(cb => {
                cb.checked = !allChecked;
                const id = parseInt(cb.dataset.articleId);
                if (!allChecked) {
                    selectedArticles.add(id);
                } else {
                    selectedArticles.delete(id);
                }
            });
            updateSelectionUI();
        }
        
        function clearSelection() {
            selectedArticles.clear();
            document.querySelectorAll('.article-checkbox').forEach(cb => cb.checked = false);
            updateSelectionUI();
        }
        
        async function batchCutCards() {
            if (selectedArticles.size === 0) {
                showToast('No articles selected', 'error');
                return;
            }
            
            showToast(`Processing ${selectedArticles.size} articles...`, 'info');
            
            // Switch to card editor
            showTab('cards');
            
            // Collect all article data
            let combinedEvidence = '';
            let articleList = [];
            
            for (const id of selectedArticles) {
                try {
                    const res = await fetch('/articles/' + id);
                    const a = await res.json();
                    articleList.push(a);
                    
                    combinedEvidence += `\n\n=== ${a.title || 'Article'} (${a.source_name || 'Unknown'}, ${a.publication_year || '?'}) ===\n`;
                    if (a.summary) combinedEvidence += a.summary + '\\n';
                    if (a.key_claims && a.key_claims.length) {
                        combinedEvidence += 'Key Claims:\\n' + a.key_claims.map(c => '• ' + c).join('\\n');
                    }
                } catch (e) {
                    console.error('Error loading article', id, e);
                }
            }
            
            // Put combined evidence in card editor
            document.getElementById('cardEvidence').value = combinedEvidence.trim();
            document.getElementById('cardContext').value = `Batch: ${selectedArticles.size} articles`;
            
            // Clear selection
            clearSelection();
            
            showToast('Articles loaded - use "Extract Multiple Cards" to find best evidence!', 'success');
        }
        
        // ==================== CARD EDITOR FUNCTIONS ====================
        
        async function formatCard() {
            const evidence = document.getElementById('cardEvidence').value.trim();
            const author = document.getElementById('cardAuthor').value.trim();
            const year = document.getElementById('cardYear').value.trim();
            const title = document.getElementById('cardTitle').value.trim();
            const source = document.getElementById('cardSource').value.trim();
            const url = document.getElementById('cardUrl').value.trim();
            const quals = document.getElementById('cardQuals').value.trim();
            const context = document.getElementById('cardContext').value.trim();
            const autoHighlight = document.getElementById('autoHighlight').checked;
            
            if (!evidence) {
                showToast('Please paste evidence text', 'error');
                return;
            }
            if (!author || !year) {
                showToast('Author and Year are required', 'error');
                return;
            }
            
            const btn = document.getElementById('formatBtn');
            btn.disabled = true;
            btn.textContent = '⏳ Formatting...';
            
            try {
                const res = await fetch('/articles/cards/format', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({
                        evidence_text: evidence,
                        author: author,
                        year: year,
                        title: title || 'Article',
                        source: source || 'Source',
                        url: url || null,
                        qualifications: quals || null,
                        argument_context: context || 'Policy debate',
                        generate_tag: true,
                        highlight: autoHighlight
                    })
                });
                
                const data = await res.json();
                
                if (data.success) {
                    displayFormattedCard(data);
                    showToast('Card formatted successfully!', 'success');
                } else {
                    showToast(data.error || 'Failed to format card', 'error');
                }
            } catch (e) {
                showToast('Error connecting to server', 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = '✨ Format Card';
            }
        }
        
        function displayFormattedCard(data) {
            const container = document.getElementById('formattedCard');
            const section = document.getElementById('cardOutputSection');
            
            // Build HTML that copies well to Google Docs
            // Use inline styles for compatibility
            let html = '';
            
            // Tag - Bold
            if (data.tag) {
                html += `<p style="font-weight: bold; font-size: 14pt; margin-bottom: 8px;">${escapeHtml(data.tag)}</p>`;
            }
            
            // Citation - Regular with line breaks
            if (data.cite) {
                const citeLines = data.cite.split('\\n');
                html += `<p style="margin-bottom: 12px;">`;
                citeLines.forEach((line, i) => {
                    if (i === 0) {
                        html += `<strong>${escapeHtml(line)}</strong>`;
                    } else {
                        html += `<br>${escapeHtml(line)}`;
                    }
                });
                html += `</p>`;
            }
            
            // Card text with underlines
            let cardText = data.highlighted_text || data.card_text;
            // Convert __text__ to highlighted text (yellow background for Google Docs compatibility)
            cardText = escapeHtml(cardText);
            cardText = cardText.replace(/__([^_]+)__/g, '<mark style="background-color: #ffff00; padding: 0 2px;">$1</mark>');
            // Convert newlines to <br>
            cardText = cardText.replace(/\\n/g, '<br>');
            
            html += `<p style="text-align: justify;">${cardText}</p>`;
            
            container.innerHTML = html;
            section.style.display = 'block';
            
            // Scroll to output
            section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        async function copyCard() {
            const container = document.getElementById('formattedCard');
            
            try {
                // Select the content
                const range = document.createRange();
                range.selectNodeContents(container);
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
                
                // Copy with formatting (works for Google Docs)
                document.execCommand('copy');
                selection.removeAllRanges();
                
                showToast('Card copied with formatting! Paste into Google Docs', 'success');
            } catch (e) {
                // Fallback to clipboard API
                try {
                    const html = container.innerHTML;
                    const blob = new Blob([html], { type: 'text/html' });
                    await navigator.clipboard.write([
                        new ClipboardItem({ 'text/html': blob })
                    ]);
                    showToast('Card copied!', 'success');
                } catch (e2) {
                    showToast('Copy failed - try selecting manually', 'error');
                }
            }
        }
        
        function copyPlainCard() {
            const container = document.getElementById('formattedCard');
            const text = container.innerText;
            
            navigator.clipboard.writeText(text).then(() => {
                showToast('Plain text copied!', 'success');
            }).catch(() => {
                showToast('Copy failed', 'error');
            });
        }
        
        async function extractCards() {
            const evidence = document.getElementById('cardEvidence').value.trim();
            const context = document.getElementById('cardContext').value.trim() || 'Arctic policy debate';
            
            if (!evidence || evidence.length < 200) {
                showToast('Please paste a longer document (200+ chars) to extract cards', 'error');
                return;
            }
            
            showToast('Extracting cards...', 'info');
            
            try {
                const res = await fetch('/articles/cards/extract', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({
                        document_text: evidence,
                        topic_context: context,
                        side: 'aff',
                        max_cards: 5
                    })
                });
                
                const data = await res.json();
                
                if (data.success && data.cards.length > 0) {
                    displayExtractedCards(data.cards);
                    showToast(`Extracted ${data.count} cards!`, 'success');
                } else {
                    showToast('No cards found in document', 'error');
                }
            } catch (e) {
                showToast('Error extracting cards', 'error');
            }
        }
        
        function displayExtractedCards(cards) {
            const section = document.getElementById('extractedCardsSection');
            const list = document.getElementById('extractedCardsList');
            
            let html = '';
            cards.forEach((card, i) => {
                html += `
                <div style="background: var(--bg-input); padding: 16px; border-radius: 8px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                        <span style="font-weight: 600; color: var(--accent-blue);">Card ${i + 1}: ${escapeHtml(card.argument_type || 'Evidence')}</span>
                        <button class="btn btn-secondary" onclick="useExtractedCard(${i})" style="font-size: 0.8rem; padding: 4px 12px;">Use This</button>
                    </div>
                    <p style="font-weight: 600; margin-bottom: 8px;">${escapeHtml(card.tag)}</p>
                    <p style="font-size: 0.9rem; color: var(--text-secondary);">${escapeHtml(card.passage.substring(0, 300))}...</p>
                    ${card.author_hint ? `<p style="font-size: 0.8rem; color: var(--accent-green); margin-top: 8px;">Suggested cite: ${escapeHtml(card.author_hint)}</p>` : ''}
                </div>
                `;
            });
            
            list.innerHTML = html;
            section.style.display = 'block';
            
            // Store cards for use
            window.extractedCards = cards;
        }
        
        function useExtractedCard(index) {
            const card = window.extractedCards[index];
            if (!card) return;
            
            // Populate the form with extracted card data
            document.getElementById('cardEvidence').value = card.passage;
            
            // Try to parse author hint
            if (card.author_hint) {
                document.getElementById('cardAuthor').value = card.author_hint;
            }
            
            document.getElementById('cardContext').value = card.argument_type || '';
            
            // Scroll to form
            document.querySelector('#tab-cards .card').scrollIntoView({ behavior: 'smooth' });
            showToast('Card loaded - add citation details and format!', 'info');
        }
        
        // Check rate limits and show warning if needed
        async function checkRateLimits() {
            try {
                const res = await fetch('/admin/rate-check');
                const data = await res.json();
                
                if (!data.allowed) {
                    document.getElementById('usageWarningText').textContent = data.reason;
                    document.getElementById('usageWarning').style.display = 'flex';
                } else if (data.daily_remaining && data.daily_remaining < 20000) {
                    const pct = Math.round((data.daily_remaining / 100000) * 100);
                    document.getElementById('usageWarningText').textContent = 
                        `Daily token usage at ${100 - pct}% - ${data.daily_remaining.toLocaleString()} tokens remaining`;
                    document.getElementById('usageWarning').style.display = 'flex';
                }
            } catch (e) {
                console.log('Rate limit check failed (admin not initialized yet)');
            }
        }
        
        // Initial load - wrapped in DOMContentLoaded for safety
        document.addEventListener('DOMContentLoaded', async function() {
            log.info('==========================================');
            log.info('🧊 Arctic Debate Card Agent - Starting...');
            log.info('==========================================');
            const initStart = performance.now();
            
            try {
                // Check for auth callback parameters
                const urlParams = new URLSearchParams(window.location.search);
                log.debug('URL params:', Object.fromEntries(urlParams));
                
                if (urlParams.get('auth_success')) {
                    log.info('✅ Auth success callback received');
                    showToast('✅ Logged in successfully!');
                    window.history.replaceState({}, document.title, window.location.pathname);
                }
                if (urlParams.get('auth_error')) {
                    const errorMsg = decodeURIComponent(urlParams.get('auth_error'));
                    log.error('❌ Auth error callback:', errorMsg);
                    showToast('❌ Login failed: ' + errorMsg, 'error');
                    window.history.replaceState({}, document.title, window.location.pathname);
                }
                
                // Parallel initialization for performance
                log.info('Starting parallel initialization...');
                
                const results = await Promise.allSettled([
                    checkAuth(),
                    checkAuthStatus(),
                    loadStats().catch(e => log.warn('Stats load skipped:', e.message)),
                    loadArticles().catch(e => log.warn('Articles load skipped:', e.message)),
                    checkRateLimits().catch(e => log.warn('Rate limit check skipped:', e.message))
                ]);
                
                // Log any failures
                results.forEach((result, i) => {
                    const names = ['checkAuth', 'checkAuthStatus', 'loadStats', 'loadArticles', 'checkRateLimits'];
                    if (result.status === 'rejected') {
                        log.warn(`${names[i]} failed:`, result.reason);
                    }
                });
                
                const initTime = Math.round(performance.now() - initStart);
                log.info('==========================================');
                log.info(`✅ Initialization complete (${initTime}ms)`);
                log.info('==========================================');
            } catch (e) {
                log.error('Init error:', e);
            }
        });
        
        // Fallback if DOM already loaded
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            console.log('DOM already ready, loading immediately...');
            setTimeout(function() {
                try {
                    loadStats();
                    loadArticles();
                } catch (e) {
                    console.error('Fallback init error:', e);
                }
            }, 100);
        }
    </script>
</body>
</html>'''

