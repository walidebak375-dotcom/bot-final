from openai import OpenAI
import json
import os
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from fpdf import FPDF
import io

# Configuration OpenAI CORRIGÉE
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

app = Flask(__name__)
app.secret_key = 'switch_bot_gpt4_ultra_pro_2026'
HISTORY_FILE = 'chat_history.json'

active_conversations = {}

def load_history():
    """Charge l'historique des conversations"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    """Sauvegarde l'historique"""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erreur sauvegarde: {e}")

def detect_brand(text):
    """Détecte la marque de switch"""
    text = text.lower()
    
    if any(word in text for word in ['cisco', 'ios', 'catalyst']):
        return 'Cisco'
    elif any(word in text for word in ['juniper', 'junos', 'jumper', 'junipeur']):
        return 'Juniper'
    elif any(word in text for word in ['hp', 'aruba', 'hpe', 'procurve']):
        return 'HPE'
    
    return None

def get_system_prompt(brand):
    """Retourne le prompt système pour GPT-4"""
    
    base_rules = """Tu es un expert réseau spécialisé en configuration de switches.

RÈGLES ABSOLUES :
1. Génère UNIQUEMENT des commandes CLI numérotées
2. AUCUN texte explicatif, AUCUNE description
3. AUCUNE commande 'show' sauf si explicitement demandé
4. AUCUNE adresse IP sauf si explicitement demandée
5. Format : 1. commande, 2. commande, etc.
"""

    if brand == 'Cisco':
        return base_rules + """
CISCO IOS - STRUCTURE OBLIGATOIRE :
1. enable
2. configure terminal
3. [commandes de configuration]
X. end
Y. write memory

SYNTAXE CISCO :
- Créer VLAN : vlan X → name VLAN_X → exit
- Port access : interface TYPE X/Y → switchport mode access → switchport access vlan X → exit
- Port trunk : interface TYPE X/Y → switchport mode trunk → switchport trunk allowed vlan X,Y,Z → exit

EXEMPLE (créer vlan 10 avec port fastEthernet 0/1) :
1. enable
2. configure terminal
3. vlan 10
4. name VLAN_10
5. exit
6. interface fastEthernet 0/1
7. switchport mode access
8. switchport access vlan 10
9. exit
10. end
11. write memory
"""

    elif brand == 'Juniper':
        return base_rules + """
JUNIPER JunOS - STRUCTURE OBLIGATOIRE :
1. configure
2. [commandes set]
X. commit

SYNTAXE JUNOS :
- Créer VLAN : set vlans VLAN_X vlan-id X
- Port access : set interfaces ge-X/X/X unit 0 family ethernet-switching vlan members VLAN_X

EXEMPLE (créer vlan 10 avec port ge-0/0/1) :
1. configure
2. set vlans VLAN_10 vlan-id 10
3. set interfaces ge-0/0/1 unit 0 family ethernet-switching vlan members VLAN_10
4. commit
"""

    else:  # HPE
        return base_rules + """
HPE/ARUBA - STRUCTURE OBLIGATOIRE :
1. configure terminal
2. [commandes de configuration]
X. write memory
Y. exit

SYNTAXE HPE :
- Créer VLAN : vlan X → name VLAN_X → exit
- Port access : interface X → vlan access X → exit

EXEMPLE (créer vlan 10 avec port 1) :
1. configure terminal
2. vlan 10
3. name VLAN_10
4. exit
5. interface 1
6. vlan access 10
7. exit
8. write memory
9. exit
"""

def validate_commands(answer, brand):
    """Valide que les commandes suivent la bonne structure"""
    lines = answer.strip().split('\n')
    warnings = []
    
    if brand == 'Cisco':
        if not any('enable' in line.lower() for line in lines[:3]):
            warnings.append("⚠️ Devrait commencer par 'enable'")
        if not any('write memory' in line.lower() or 'copy run' in line.lower() for line in lines):
            warnings.append("⚠️ Devrait finir par 'write memory'")
    
    elif brand == 'Juniper':
        if not any('configure' in line.lower() for line in lines[:2]):
            warnings.append("⚠️ Devrait commencer par 'configure'")
        if not any('commit' in line.lower() for line in lines):
            warnings.append("⚠️ Devrait finir par 'commit'")
    
    elif brand == 'HPE':
        if not any('configure terminal' in line.lower() for line in lines[:2]):
            warnings.append("⚠️ Devrait commencer par 'configure terminal'")
    
    return warnings

def generate_commands_gpt4(query, brand, conversation_history):
    """Génère les commandes CLI avec GPT-4"""
    
    try:
        messages = [
            {
                "role": "system",
                "content": get_system_prompt(brand)
            }
        ]
        
        for msg in conversation_history[-12:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        messages.append({
            "role": "user",
            "content": f"{query}\n\nGénère UNIQUEMENT les commandes CLI numérotées pour {brand}."
        })
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.1,
            max_tokens=1000
        )
        
        answer = response.choices[0].message.content.strip()
        
        print(f"[GPT-4] Tokens: {response.usage.total_tokens}")
        
        return answer
        
    except Exception as e:
        error_msg = str(e)
        
        if "api_key" in error_msg.lower():
            return "❌ ERREUR : Clé API OpenAI invalide.\n\n🔑 Va sur https://platform.openai.com/api-keys"
        elif "quota" in error_msg.lower() or "insufficient" in error_msg.lower():
            return "❌ ERREUR : Quota dépassé.\n\n💳 Ajoute du crédit sur https://platform.openai.com/account/billing"
        elif "rate_limit" in error_msg.lower():
            return "❌ ERREUR : Trop de requêtes. Attends 10 secondes."
        else:
            return f"❌ Erreur GPT-4: {error_msg}"

def generate_pdf(query, brand, answer):
    """Génère un PDF des commandes"""
    
    try:
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Switch Command Assistant - Configuration', ln=True, align='C')
        
        pdf.ln(10)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, f'Marque: {brand}', ln=True)
        
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f'Question: {query}', ln=True)
        pdf.cell(0, 6, f'Date: {datetime.now().strftime("%d/%m/%Y %H:%M")}', ln=True)
        
        pdf.ln(10)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Commandes CLI:', ln=True)
        
        pdf.set_font('Courier', '', 9)
        
        for line in answer.split('\n'):
            if line.strip():
                try:
                    pdf.cell(0, 5, line.encode('latin-1', 'ignore').decode('latin-1'), ln=True)
                except:
                    pdf.cell(0, 5, line, ln=True)
        
        pdf.ln(10)
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 5, 'Generated by Switch Bot Pro', ln=True, align='C')
        
        pdf_output = pdf.output(dest='S').encode('latin-1')
        
        return io.BytesIO(pdf_output)
        
    except Exception as e:
        print(f"Erreur PDF: {e}")
        return None

@app.route('/')
def home():
    """Page d'accueil"""
    return """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Switch Bot Pro - GPT-4 Edition</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            width: 100%;
            max-width: 1400px;
            height: 90vh;
            background: #0d1117;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            display: flex;
            overflow: hidden;
        }
        
        .sidebar {
            width: 300px;
            background: #161b22;
            border-right: 1px solid #30363d;
            display: flex;
            flex-direction: column;
        }
        
        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid #30363d;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
            color: #f0f6fc;
        }
        
        .logo-icon { font-size: 32px; }
        .logo-text { font-size: 18px; font-weight: 700; }
        
        .gpt-badge {
            background: linear-gradient(135deg, #10a37f 0%, #1a7f64 100%);
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 700;
            display: inline-block;
            margin-bottom: 12px;
        }
        
        .new-chat-btn {
            width: 100%;
            background: linear-gradient(135deg, #10a37f 0%, #1a7f64 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        .new-chat-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(16, 163, 127, 0.4);
        }
        
        .templates {
            padding: 16px;
            border-bottom: 1px solid #30363d;
        }
        
        .templates-title {
            font-size: 12px;
            font-weight: 700;
            color: #6e7681;
            text-transform: uppercase;
            margin-bottom: 12px;
        }
        
        .template-btn {
            width: 100%;
            background: #21262d;
            border: 1px solid #30363d;
            color: #8b949e;
            padding: 10px;
            border-radius: 8px;
            font-size: 12px;
            text-align: left;
            cursor: pointer;
            margin-bottom: 8px;
            transition: all 0.2s;
        }
        
        .template-btn:hover {
            background: #30363d;
            color: #f0f6fc;
            border-color: #10a37f;
        }
        
        .history-list {
            flex: 1;
            overflow-y: auto;
            padding: 12px;
        }
        
        .history-date {
            padding: 12px 16px;
            font-size: 11px;
            font-weight: 700;
            color: #6e7681;
            text-transform: uppercase;
        }
        
        .history-item {
            padding: 14px;
            margin: 6px 0;
            border-radius: 10px;
            cursor: pointer;
            font-size: 13px;
            color: #8b949e;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.2s;
        }
        
        .history-item:hover {
            background: #21262d;
            color: #f0f6fc;
            transform: translateX(4px);
        }
        
        .history-text {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .delete-btn {
            opacity: 0;
            color: #f85149;
            cursor: pointer;
            font-size: 16px;
        }
        
        .history-item:hover .delete-btn { opacity: 1; }
        
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: #161b22;
            border-bottom: 1px solid #30363d;
            padding: 20px 30px;
            display: flex;
            align-items: center;
            gap: 16px;
        }
        
        .header-title {
            font-size: 20px;
            font-weight: 700;
            color: #f0f6fc;
        }
        
        .ai-badge {
            background: linear-gradient(135deg, #10a37f 0%, #1a7f64 100%);
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-left: auto;
        }
        
        .brand-pills {
            display: flex;
            gap: 10px;
        }
        
        .pill {
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            transition: transform 0.2s;
        }
        
        .pill:hover { transform: scale(1.05); }
        .pill.cisco { background: #1f6feb; color: white; }
        .pill.juniper { background: #238636; color: white; }
        .pill.hpe { background: #da3633; color: white; }
        
        .chat {
            flex: 1;
            overflow-y: auto;
            padding: 30px;
        }
        
        .message {
            display: flex;
            gap: 16px;
            margin: 20px 0;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message.user { flex-direction: row-reverse; }
        
        .avatar {
            width: 42px;
            height: 42px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            flex-shrink: 0;
        }
        
        .avatar.user {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        .avatar.bot {
            background: linear-gradient(135deg, #10a37f 0%, #1a7f64 100%);
            box-shadow: 0 4px 12px rgba(16, 163, 127, 0.3);
        }
        
        .msg-content {
            max-width: 75%;
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 16px;
            padding: 18px;
            position: relative;
        }
        
        .message.user .msg-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            color: white;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        .brand-tag {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
            margin-bottom: 12px;
            display: inline-block;
            text-transform: uppercase;
        }
        
        .brand-tag.cisco { background: #1f6feb; color: white; }
        .brand-tag.juniper { background: #238636; color: white; }
        .brand-tag.hpe { background: #da3633; color: white; }
        
        .action-buttons {
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
        }
        
        .action-btn {
            background: #30363d;
            border: 1px solid #484f58;
            color: #f0f6fc;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .action-btn:hover {
            background: #484f58;
        }
        
        .action-btn.copied, .action-btn.downloaded {
            background: #238636;
            border-color: #238636;
        }
        
        .code {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 18px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.8;
            color: #58a6ff;
            white-space: pre-wrap;
        }
        
        .warning-box {
            background: #3d2506;
            border: 1px solid #9e6a03;
            border-radius: 8px;
            padding: 12px;
            margin-top: 12px;
            font-size: 12px;
            color: #f0883e;
        }
        
        .welcome {
            text-align: center;
            padding: 80px 20px;
            color: #8b949e;
        }
        
        .welcome-icon { font-size: 64px; margin-bottom: 20px; }
        
        .welcome h2 {
            color: #f0f6fc;
            margin-bottom: 16px;
            font-size: 28px;
            font-weight: 700;
        }
        
        .welcome .highlight {
            color: #10a37f;
            font-weight: 600;
        }
        
        .input-box {
            background: #161b22;
            border-top: 1px solid #30363d;
            padding: 20px 30px;
        }
        
        .input-wrap {
            max-width: 1000px;
            margin: 0 auto;
            display: flex;
            gap: 12px;
        }
        
        #query {
            flex: 1;
            background: #0d1117;
            border: 2px solid #30363d;
            border-radius: 12px;
            padding: 14px 18px;
            font-size: 14px;
            color: #f0f6fc;
            outline: none;
            transition: all 0.3s;
        }
        
        #query:focus {
            border-color: #10a37f;
            box-shadow: 0 0 0 3px rgba(16, 163, 127, 0.1);
        }
        
        #sendBtn {
            background: linear-gradient(135deg, #10a37f 0%, #1a7f64 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 14px 28px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        #sendBtn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(16, 163, 127, 0.4);
        }
        
        #sendBtn:disabled { opacity: 0.5; cursor: not-allowed; }
        
        .loading {
            display: flex;
            gap: 6px;
            padding: 10px 0;
        }
        
        .loading span {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: linear-gradient(135deg, #10a37f 0%, #1a7f64 100%);
            animation: bounce 1.4s infinite ease-in-out both;
        }
        
        .loading span:nth-child(1) { animation-delay: -0.32s; }
        .loading span:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        
        ::-webkit-scrollbar { width: 10px; }
        ::-webkit-scrollbar-track { background: #0d1117; }
        ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 5px; }
        ::-webkit-scrollbar-thumb:hover { background: #484f58; }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="sidebar-header">
                <div class="gpt-badge">⚡ Powered by GPT-4</div>
                <div class="logo">
                    <div class="logo-icon">🤖</div>
                    <div class="logo-text">Switch Bot Pro</div>
                </div>
                <button class="new-chat-btn" id="newChat">
                    ➕ Nouvelle conversation
                </button>
            </div>
            
            <div class="templates">
                <div class="templates-title">📋 Templates populaires</div>
                <button class="template-btn" data-template="créer 10 vlan avec 1 port chacun cisco">
                    📌 Créer 10 VLANs + ports
                </button>
                <button class="template-btn" data-template="sécuriser les ports inutilisés cisco">
                    🔒 Sécuriser ports inutilisés
                </button>
                <button class="template-btn" data-template="configurer trunk avec tous les vlans cisco">
                    🔗 Configurer trunk
                </button>
                <button class="template-btn" data-template="activer ssh avec authentification cisco">
                    🔐 Activer SSH
                </button>
                <button class="template-btn" data-template="créer agrégation de liens 2 ports cisco">
                    ⚡ Agrégation de liens
                </button>
            </div>
            
            <div class="history-list" id="history"></div>
        </div>
        
        <div class="main">
            <div class="header">
                <h1 class="header-title">Switch Command Assistant</h1>
                <span class="ai-badge">⚡ GPT-4 Edition</span>
                <div class="brand-pills">
                    <span class="pill cisco">Cisco IOS</span>
                    <span class="pill juniper">Juniper JunOS</span>
                    <span class="pill hpe">HPE Aruba</span>
                </div>
            </div>
            
            <div class="chat" id="chat">
                <div class="welcome">
                    <div class="welcome-icon">⚡</div>
                    <h2>Switch Bot Pro - GPT-4</h2>
                    <p>IA de pointe avec <span class="highlight">précision maximale</span></p>
                    <p style="margin-top: 12px;">
                        Génération de commandes CLI professionnelles
                    </p>
                </div>
            </div>
            
            <div class="input-box">
                <div class="input-wrap">
                    <input 
                        type="text" 
                        id="query" 
                        placeholder="Ex: créer 10 vlans avec 1 port chacun sur Cisco" 
                        autofocus
                    >
                    <button id="sendBtn">Envoyer ↵</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const chat = document.getElementById('chat');
        const query = document.getElementById('query');
        const sendBtn = document.getElementById('sendBtn');
        const historyDiv = document.getElementById('history');
        const newChatBtn = document.getElementById('newChat');
        
        let firstMsg = true;
        let sessionId = Date.now().toString();
        let currentChatId = null;
        
        document.querySelectorAll('.template-btn').forEach(btn => {
            btn.onclick = () => {
                query.value = btn.dataset.template;
                send();
            };
        });
        
        loadHistory();
        
        function loadHistory() {
            fetch('/history')
                .then(r => r.json())
                .then(data => renderHistory(data.history))
                .catch(err => console.error('Erreur:', err));
        }
        
        function renderHistory(items) {
            historyDiv.innerHTML = '';
            
            if (!items || items.length === 0) {
                historyDiv.innerHTML = '<div style="padding: 20px; text-align: center; color: #6e7681; font-size: 13px;">Aucun historique</div>';
                return;
            }
            
            const today = [], yesterday = [], older = [];
            const now = new Date();
            
            items.forEach(item => {
                const d = new Date(item.timestamp).toDateString();
                const td = now.toDateString();
                const yd = new Date(now.getTime() - 86400000).toDateString();
                
                if (d === td) today.push(item);
                else if (d === yd) yesterday.push(item);
                else older.push(item);
            });
            
            if (today.length) {
                addDateHeader("Aujourd'hui");
                today.forEach(addHistItem);
            }
            
            if (yesterday.length) {
                addDateHeader('Hier');
                yesterday.forEach(addHistItem);
            }
            
            if (older.length) {
                addDateHeader('Plus ancien');
                older.forEach(addHistItem);
            }
        }
        
        function addDateHeader(text) {
            const date = document.createElement('div');
            date.className = 'history-date';
            date.textContent = text;
            historyDiv.appendChild(date);
        }
        
        function addHistItem(item) {
            const div = document.createElement('div');
            div.className = 'history-item';
            
            const icon = document.createElement('span');
            icon.textContent = '💬';
            
            const text = document.createElement('span');
            text.className = 'history-text';
            text.textContent = item.query;
            
            const del = document.createElement('span');
            del.className = 'delete-btn';
            del.textContent = '🗑️';
            del.onclick = (e) => {
                e.stopPropagation();
                if (confirm('Supprimer ?')) {
                    fetch('/delete/' + item.id, {method: 'DELETE'})
                        .then(() => loadHistory());
                }
            };
            
            div.appendChild(icon);
            div.appendChild(text);
            div.appendChild(del);
            
            div.onclick = () => {
                chat.innerHTML = '';
                firstMsg = false;
                currentChatId = item.id;
                addUserMsg(item.query);
                addBotMsg(item.brand, item.answer, item.warnings || [], item.id, item.query);
            };
            
            historyDiv.appendChild(div);
        }
        
        newChatBtn.onclick = () => {
            firstMsg = true;
            sessionId = Date.now().toString();
            currentChatId = null;
            chat.innerHTML = `
                <div class="welcome">
                    <div class="welcome-icon">✨</div>
                    <h2>Nouvelle conversation</h2>
                    <p>GPT-4 va générer des commandes parfaites</p>
                </div>
            `;
            query.value = '';
            query.focus();
        };
        
        function addUserMsg(text) {
            if (firstMsg) {
                chat.innerHTML = '';
                firstMsg = false;
            }
            const msg = document.createElement('div');
            msg.className = 'message user';
            msg.innerHTML = `
                <div class="avatar user">👤</div>
                <div class="msg-content">${escapeHtml(text)}</div>
            `;
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function copyCode(codeText, btnElement) {
            navigator.clipboard.writeText(codeText).then(() => {
                const originalText = btnElement.innerHTML;
                btnElement.innerHTML = '✅ Copié !';
                btnElement.classList.add('copied');
                setTimeout(() => {
                    btnElement.innerHTML = originalText;
                    btnElement.classList.remove('copied');
                }, 2000);
            });
        }
        
        function downloadPDF(chatId, btnElement) {
            const originalText = btnElement.innerHTML;
            btnElement.innerHTML = '⏳ Génération...';
            
            fetch('/download_pdf/' + chatId)
                .then(response => response.blob())
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'switch_config_' + chatId + '.pdf';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    btnElement.innerHTML = '✅ Téléchargé !';
                    btnElement.classList.add('downloaded');
                    setTimeout(() => {
                        btnElement.innerHTML = originalText;
                        btnElement.classList.remove('downloaded');
                    }, 2000);
                })
                .catch(err => {
                    console.error('Erreur PDF:', err);
                    btnElement.innerHTML = originalText;
                    alert('Erreur lors du téléchargement du PDF');
                });
        }
        
        function addBotMsg(brand, answer, warnings = [], chatId = null, query = '') {
            const msg = document.createElement('div');
            msg.className = 'message';
            
            let tag = '';
            if (brand === 'Cisco') tag = '<span class="brand-tag cisco">Cisco IOS</span>';
            else if (brand === 'Juniper') tag = '<span class="brand-tag juniper">Juniper JunOS</span>';
            else if (brand === 'HPE') tag = '<span class="brand-tag hpe">HPE Aruba</span>';
            
            let warningHtml = '';
            if (warnings.length > 0) {
                warningHtml = '<div class="warning-box">' + warnings.join('<br>') + '</div>';
            }
            
            const escapedAnswer = escapeHtml(answer);
            const chatIdStr = chatId || currentChatId || '';
            
            msg.innerHTML = `
                <div class="avatar bot">🤖</div>
                <div class="msg-content">
                    ${tag}
                    <div class="action-buttons">
                        <button class="action-btn" onclick="copyCode(\`${answer.replace(/`/g, '\\`')}\`, this)">
                            📋 Copier
                        </button>
                        <button class="action-btn" onclick="downloadPDF('${chatIdStr}', this)">
                            📥 Télécharger PDF
                        </button>
                    </div>
                    <div class="code">${escapedAnswer}</div>
                    ${warningHtml}
                </div>
            `;
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function showLoad() {
            const msg = document.createElement('div');
            msg.className = 'message';
            msg.id = 'loading';
            msg.innerHTML = `
                <div class="avatar bot">🤖</div>
                <div class="msg-content">
                    <div class="loading"><span></span><span></span><span></span></div>
                </div>
            `;
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function hideLoad() {
            const l = document.getElementById('loading');
            if (l) l.remove();
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        async function send() {
            const q = query.value.trim();
            if (!q) return;
            
            addUserMsg(q);
            query.value = '';
            query.disabled = true;
            sendBtn.disabled = true;
            showLoad();
            
            try {
                const res = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: q, session_id: sessionId})
                });
                
                const data = await res.json();
                hideLoad();
                currentChatId = data.chat_id;
                addBotMsg(data.brand, data.answer, data.warnings || [], data.chat_id, q);
                loadHistory();
                
            } catch (e) {
                hideLoad();
                addBotMsg('Erreur', `❌ Erreur: ${e.message}`);
            } finally {
                query.disabled = false;
                sendBtn.disabled = false;
                query.focus();
            }
        }
        
        sendBtn.onclick = send;
        query.onkeypress = (e) => { 
            if (e.key === 'Enter') send();
        };
    </script>
</body>
</html>"""

@app.route('/history')
def get_history():
    return jsonify({'history': load_history()})

@app.route('/delete/<chat_id>', methods=['DELETE'])
def delete(chat_id):
    history = [h for h in load_history() if h['id'] != chat_id]
    save_history(history)
    return jsonify({'success': True})

@app.route('/download_pdf/<chat_id>')
def download_pdf(chat_id):
    """Télécharge le PDF d'une conversation"""
    try:
        history = load_history()
        chat = next((h for h in history if h['id'] == chat_id), None)
        
        if not chat:
            return "Conversation non trouvée", 404
        
        pdf_buffer = generate_pdf(chat['query'], chat['brand'], chat['answer'])
        
        if pdf_buffer:
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'switch_config_{chat_id}.pdf'
            )
        else:
            return "Erreur génération PDF", 500
            
    except Exception as e:
        print(f"Erreur download PDF: {e}")
        return f"Erreur: {str(e)}", 500

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        q = data.get('query', '').strip()
        session_id = data.get('session_id', 'default')
        
        if not q:
            return jsonify({'brand': 'Erreur', 'answer': 'Question vide', 'warnings': [], 'chat_id': ''}), 400
        
        if session_id not in active_conversations:
            active_conversations[session_id] = []
        
        conversation = active_conversations[session_id]
        
        brand = detect_brand(q)
        
        if not brand:
            text_lower = q.lower()
            
            if any(word in text_lower for word in ['pareil', 'même', 'identique']):
                if any(word in text_lower for word in ['juniper', 'junos', 'jumper']):
                    brand = 'Juniper'
                elif any(word in text_lower for word in ['hp', 'hpe', 'aruba']):
                    brand = 'HPE'
                elif 'cisco' in text_lower:
                    brand = 'Cisco'
            
            if not brand and conversation:
                for msg in reversed(conversation):
                    if msg['role'] == 'assistant':
                        content = msg.get('content', '')
                        if '[Cisco]' in content:
                            brand = 'Cisco'
                            break
                        elif '[Juniper]' in content:
                            brand = 'Juniper'
                            break
                        elif '[HPE]' in content:
                            brand = 'HPE'
                            break
        
        if not brand:
            brand = 'Cisco'
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Q: {q[:50]}... | Marque: {brand}")
        
        answer = generate_commands_gpt4(q, brand, conversation)
        
        warnings = validate_commands(answer, brand)
        
        conversation.append({'role': 'user', 'content': q})
        conversation.append({'role': 'assistant', 'content': f"[{brand}]\n{answer}"})
        
        active_conversations[session_id] = conversation[-20:]
        
        history = load_history()
        chat_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        history.insert(0, {
            'id': chat_id,
            'query': q,
            'brand': brand,
            'answer': answer,
            'warnings': warnings,
            'timestamp': datetime.now().isoformat()
        })
        
        save_history(history[:100])
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Réponse GPT-4 générée")
        
        return jsonify({'brand': brand, 'answer': answer, 'warnings': warnings, 'chat_id': chat_id})
        
    except Exception as e:
        print(f"[ERREUR] {str(e)}")
        return jsonify({'brand': 'Erreur', 'answer': f"❌ Erreur: {str(e)}", 'warnings': [], 'chat_id': ''}), 500

if __name__ == '__main__':
    print("=" * 70)
    print("⚡ SWITCH BOT PRO - GPT-4 EDITION FINALE")
    print("=" * 70)
    print(f"✅ Modèle: GPT-4o (OpenAI)")
    print(f"✅ Fonctionnalités:")
    print(f"   - GPT-4 ✓")
    print(f"   - Bouton Copier ✓")
    print(f"   - Export PDF ✓")
    print(f"   - Templates ✓")
    print(f"   - Validation ✓")
    print(f"   - Mémoire conversationnelle ✓")
    print("=" * 70)
    print(f"🌐 URL: http://127.0.0.1:5000")
    print("=" * 70)
    print()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
